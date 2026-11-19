"""Fail-closed 7z validation, whole-repository withholding, and honest coverage."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
import py7zr

PATTERN = re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----')
class Blocked(Exception):
    pass

def matches(data, secrets):
    if any(s and s in data for s in secrets):
        return 'KNOWN_CREDENTIAL'
    m = PATTERN.search(data)
    if m:
        return 'PRIVATE_KEY_MARKER' if m.group().startswith(b'-----BEGIN') else 'TOKEN_PATTERN'
    return None

def scan_stream(stream, secrets, length=None):
    tail = b''
    while length is None or length > 0:
        chunk = stream.read(1048576 if length is None else min(1048576, length))
        if not chunk:
            if length is not None and length > 0:
                raise Blocked('TRUNCATED_GIT_OBJECT')
            break
        if length is not None:
            length -= len(chunk)
        category = matches(tail + chunk, secrets)
        if category:
            # Consume the full object so the batch stream remains aligned.
            if length is not None:
                while length:
                    rest = stream.read(min(length, 1048576))
                    if not rest:
                        raise Blocked('TRUNCATED_GIT_OBJECT')
                    length -= len(rest)
            return category
        tail = (tail + chunk)[-8192:]
    return None

def unit_for(relative):
    parts = relative.parts
    if len(parts) >= 3 and parts[1] == 'repositories':
        return '/'.join(parts[:3])
    # Gists and metadata are not silently omitted: findings there block publication.
    return None

def validate_names(names):
    seen = set()
    for name in names:
        p = PurePosixPath(name)
        if not p.parts or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
            raise Blocked('UNSAFE_ARCHIVE_PATH')
        key = str(p)
        if key in seen:
            raise Blocked('DUPLICATE_ARCHIVE_PATH')
        seen.add(key)

def run7(args, password):
    # CLI requires a password argument; use only a single-tenant hosted runner.
    result = subprocess.run(['7z'] + args + ['-p' + password], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
    if result.returncode:
        raise Blocked('SEVENZIP_COMMAND_FAILED')

def sha(file):
    h = hashlib.sha256()
    with file.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def scan_git(repo, secrets):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_NO_REPLACE_OBJECTS='1')
    findings = set()
    with tempfile.TemporaryFile() as errors:
        p = subprocess.Popen(['git', '--git-dir=' + str(repo), 'cat-file', '--batch-all-objects', '--batch'],
                             stdout=subprocess.PIPE, stderr=errors, env=env)
        try:
            while True:
                header = p.stdout.readline()
                if not header:
                    break
                fields = header.rstrip(b'\n').split()
                if len(fields) != 3 or not fields[2].isdigit():
                    raise Blocked('INVALID_GIT_OBJECT_STREAM')
                category = scan_stream(p.stdout, secrets, int(fields[2]))
                if p.stdout.read(1) != b'\n':
                    raise Blocked('INVALID_GIT_OBJECT_STREAM')
                if category:
                    findings.add(category)
            if p.wait() != 0:
                raise Blocked('GIT_OBJECT_SCAN_FAILED')
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
    return findings

def main():
    os.umask(0o077)
    root = Path(os.environ['RUNNER_TEMP'])
    account = os.environ['ACCOUNT']
    if account not in ('tickwarden', 'IronCrest-sudo'):
        raise Blocked('INVALID_ACCOUNT')
    password = os.environ['ARCHIVE_PASSWORD']
    secrets = [os.environ['GH_TOKEN'].encode(), password.encode()]
    if not secrets[0] or len(password) < 20:
        raise Blocked('MISSING_SECRET')
    reportdir = root / ('report-' + account)
    reportdir.mkdir(exist_ok=True, mode=0o700)
    stage = 'open'
    report = {'account': account, 'findings': [], 'complete_backup_verified': False,
              'status': 'blocked', 'full_git_history_secret_audit': False,
              'scope': 'user target only; accessible organizations not independently enumerated',
              'restore_test': False, 'scan_limits': 'Pattern and exact-credential scan; not all possible secrets or nested compressed formats are detected.'}
    try:
        archives = list((root / ('out-' + account)).glob('*.7z'))
        if len(archives) != 1:
            raise Blocked('ONE_ARCHIVE_REQUIRED')
        archive = archives[0]
        with tempfile.TemporaryDirectory(dir=root, prefix='validated-') as tmp:
            tmp = Path(tmp)
            data = tmp / 'data'
            data.mkdir()
            print('VERIFY_STAGE archive_integrity', flush=True)
            run7(['t', '-bd', str(archive)], password)
            stage = 'extract'
            with py7zr.SevenZipFile(archive, 'r', password=password) as z:
                if not z.needs_password():
                    raise Blocked('ENCRYPTION_REQUIRED')
                info = z.list()
                validate_names([f.filename for f in info])
                if any(getattr(f, 'is_symlink', False) for f in info):
                    raise Blocked('LINK_UNSUPPORTED')
                z.extractall(data)
            files = []
            for base, dirs, names in os.walk(data, followlinks=False):
                for name in dirs + names:
                    p = Path(base) / name
                    if p.is_symlink() or not p.resolve().is_relative_to(data.resolve()):
                        raise Blocked('LINK_UNSUPPORTED')
                for name in names:
                    p = Path(base) / name
                    if not p.is_file():
                        raise Blocked('SPECIAL_FILE_UNSUPPORTED')
                    files.append(p)
            if not files:
                raise Blocked('EMPTY_ARCHIVE')
            stage = 'scan'
            withheld = set()
            unsafe_global = False
            def finding(path, category, source):
                nonlocal unsafe_global
                rel = path.relative_to(data)
                unit = unit_for(rel)
                report['findings'].append({'unit': unit, 'path_sha256': hashlib.sha256(str(rel).encode()).hexdigest(),
                                           'category': category, 'source': source})
                if unit:
                    withheld.add(unit)
                else:
                    unsafe_global = True
            print('VERIFY_STAGE regular_files_and_git_objects', flush=True)
            last = time.monotonic()
            for index, path in enumerate(files):
                with path.open('rb') as f:
                    category = scan_stream(f, secrets)
                if category:
                    finding(path, category, 'regular_file')
                if time.monotonic() - last > 30:
                    print('SCAN_PROGRESS files=' + str(index + 1), flush=True)
                    last = time.monotonic()
            for head in data.rglob('HEAD'):
                repo = head.parent
                if head.is_file() and (repo / 'objects').is_dir() and (repo / 'config').is_file():
                    for category in scan_git(repo, secrets):
                        finding(head, category, 'decoded_git_objects')
            report['withheld_repository_units'] = sorted(withheld)
            report['decoded_git_object_scan'] = True
            if unsafe_global:
                raise Blocked('ACCOUNT_METADATA_OR_UNMAPPED_FINDING')
            stage = 'repack'
            # Never edit Git history or suppress a match: withhold the WHOLE unit.
            for unit in withheld:
                shutil.rmtree(data / unit)
            retained = [p for p in data.rglob('*') if p.is_file()]
            if not retained:
                raise Blocked('NO_SAFE_FILES')
            report.update(status='partial' if withheld else 'passed_basic_checks',
                          retained_file_count=len(retained),
                          coverage_warning='Withheld units are NOT backed up. Original inventory files may mention excluded units; this report controls delivered coverage.')
            (data / 'DELIVERY-COVERAGE.json').write_text(json.dumps(report, indent=2))
            staged = tmp / 'approved'
            staged.mkdir()
            label = '-PARTIAL' if withheld else '-CHECKED'
            output = staged / (account + label + '.7z')
            result = subprocess.run(['7z', 'a', '-t7z', '-mhe=on', '-p' + password, '-bd', str(output), '.'],
                                    cwd=data, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=1800)
            if result.returncode:
                raise Blocked('REPACK_FAILED')
            run7(['t', '-bd', str(output)], password)
            (staged / (output.name + '.sha256')).write_text(sha(output) + '  ' + output.name + '\n')
            (staged / 'COVERAGE.json').write_text(json.dumps(report, indent=2))
            dest = root / ('approved-' + account)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(staged, dest)
            if os.environ.get('PLAINTEXT_ZIP', '').lower() == 'true':
                stage = 'zip'
                plain = root / ('plaintext-' + account)
                plain.mkdir(mode=0o700, exist_ok=True)
                zp = plain / (account + label + '-UNENCRYPTED.zip')
                with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
                    for path in data.rglob('*'):
                        z.write(path, path.relative_to(data).as_posix())
                with zipfile.ZipFile(zp) as z:
                    if z.testzip() is not None:
                        raise Blocked('ZIP_CRC_FAILED')
                (plain / (zp.name + '.sha256')).write_text(sha(zp) + '  ' + zp.name + '\n')
                (plain / 'COVERAGE.json').write_text(json.dumps(report, indent=2))
            if withheld:
                print('::warning::PARTIAL backup: ' + str(len(withheld)) + ' whole repository units withheld. See coverage report.', flush=True)
            print('Verification finished; complete coverage/restore NOT claimed.', flush=True)
    except Exception as e:
        code = str(e) if isinstance(e, Blocked) else 'LIBRARY_OR_IO_FAILURE'
        report.update(status='blocked', stage=stage, error_code=code)
        for prefix in ('approved-', 'plaintext-'):
            shutil.rmtree(root / (prefix + account), ignore_errors=True)
        print('::error::Verification blocked: stage=' + stage + '; code=' + code + '. No backup artifact published.', flush=True)
        raise SystemExit(1) from None
    finally:
        (reportdir / 'SCAN-REPORT.json').write_text(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
