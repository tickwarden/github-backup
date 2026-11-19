"""Convert the already-checked encrypted tar into an optional unencrypted ZIP."""
import os, pathlib, tempfile, subprocess, tarfile, zipfile, shutil, hashlib, json
os.umask(0o077)
root = pathlib.Path(os.environ['RUNNER_TEMP'])
account = os.environ['ACCOUNT']
if account not in ('tickwarden', 'IronCrest-sudo'):
    raise SystemExit('Invalid account')
if os.environ.get('PLAINTEXT_ZIP', '').lower() != 'true':
    print('Unencrypted ZIP disabled.')
    raise SystemExit(0)
approved = root / f'approved-{account}'
manifest = json.loads((approved/'COVERAGE.json').read_text())
if not manifest.get('basic_credential_check'):
    raise SystemExit('Previous verification required')
archives = list(approved.glob('*.tar.gz.gpg'))
if len(archives) != 1:
    raise SystemExit('Exactly one approved encrypted archive required')
with tempfile.TemporaryDirectory(dir=root, prefix='plaintext-stage-') as tmp:
    staged = pathlib.Path(tmp)/f'{account}-UNENCRYPTED.zip'
    with tempfile.TemporaryFile(dir=tmp) as tarbytes:
        result = subprocess.run(['gpg','--batch','--quiet','--pinentry-mode','loopback','--passphrase-fd','0','--decrypt',str(archives[0])],input=(os.environ['ARCHIVE_PASSWORD']+'\n').encode(),stdout=tarbytes,stderr=subprocess.DEVNULL)
        if result.returncode:
            raise SystemExit('Decryption failed')
        tarbytes.seek(0)
        seen=set()
        with tarfile.open(fileobj=tarbytes, mode='r|gz') as source, zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as dest:
            for member in source:
                name=member.name
                parts=pathlib.PurePosixPath(name)
                if parts.is_absolute() or '..' in parts.parts or '\\' in name or '\x00' in name:
                    raise SystemExit('Unsafe archive path; ZIP blocked')
                if not parts.parts: continue
                normalized=str(parts)
                if normalized in seen:
                    raise SystemExit('Duplicate archive path; ZIP blocked')
                seen.add(normalized)
                if member.isdir():
                    dest.mkdir(normalized, mode=member.mode & 0o777)
                    continue
                if not member.isfile():
                    raise SystemExit('Links or special files cannot be faithfully converted; ZIP blocked')
                info=zipfile.ZipInfo(normalized)
                info.create_system=3
                info.external_attr=(0o100000 | (member.mode & 0o777)) << 16
                info.compress_type=zipfile.ZIP_DEFLATED
                with source.extractfile(member) as inp, dest.open(info,'w',force_zip64=True) as output:
                    shutil.copyfileobj(inp,output,1024*1024)
    with zipfile.ZipFile(staged) as check:
        if check.testzip() is not None:
            raise SystemExit('ZIP CRC verification failed')
    target=root/f'plaintext-{account}'
    target.mkdir(mode=0o700)
    shutil.copy2(staged,target/staged.name)
    digest=hashlib.sha256()
    with staged.open('rb') as inp:
        for chunk in iter(lambda:inp.read(1024*1024), b''):digest.update(chunk)
    (target/(staged.name+'.sha256')).write_text(digest.hexdigest()+'  '+staged.name+'\n')
    manifest.update(unencrypted=True, zip_crc_verified=True, symlinks_supported=False)
    (target/'COVERAGE.json').write_text(json.dumps(manifest,indent=2))
print('WARNING: Unencrypted ZIP produced. Keep private. Full Git history secret audit and restore test NOT performed.')
