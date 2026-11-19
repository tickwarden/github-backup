"""Validate encrypted 7z; optional unencrypted ZIP. Not a full history audit."""
import os, pathlib, subprocess, tempfile, hashlib, shutil, json, re, zipfile
import py7zr
os.umask(0o077)
root=pathlib.Path(os.environ['RUNNER_TEMP']);account=os.environ['ACCOUNT']
if account not in ('tickwarden','IronCrest-sudo'):raise SystemExit('Invalid account')
archives=list((root/f'out-{account}').glob('*.7z'))
if len(archives)!=1:raise SystemExit('Exactly one 7z archive required')
archive=archives[0];password=os.environ['ARCHIVE_PASSWORD']
secrets=[os.environ[k].encode() for k in ('GH_TOKEN','ARCHIVE_PASSWORD')]
pattern=re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
def checksum(file):
    h=hashlib.sha256()
    with file.open('rb') as inp:
        for chunk in iter(lambda:inp.read(1048576),b''):h.update(chunk)
    file.with_name(file.name+'.sha256').write_text(h.hexdigest()+'  '+file.name+'\n')
manifest={'account':account,'kind':'user','format':'7z','basic_credential_check':True,'full_git_history_secret_audit':False,'restore_test':False,'all_accessible_orgs_backed_up':False,'complete_backup_verified':False}
stage='initialization'
with tempfile.TemporaryDirectory(dir=root,prefix='verify-7z-') as tmp:
    dest=pathlib.Path(tmp)/'data';dest.mkdir()
    try:
        stage='archive_open_and_path_check'
        print('VERIFY_STAGE '+stage,flush=True)
        with py7zr.SevenZipFile(archive,mode='r',password=password) as z:
            if not z.needs_password():raise ValueError('Archive must be encrypted')
            seen=set()
            for info in z.list():
                name=info.filename;p=pathlib.PurePosixPath(name)
                if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or not p.parts:raise ValueError('Unsafe path')
                if str(p) in seen:raise ValueError('Duplicate path')
                seen.add(str(p))
                if getattr(info,'is_symlink',False):raise ValueError('Links unsupported')
            stage='archive_extraction'
            print('VERIFY_STAGE '+stage,flush=True)
            z.extractall(path=dest)
        # Exact read/CRC test through independent 7z CLI, output suppressed.
        stage='7z_integrity_test'
        print('VERIFY_STAGE '+stage,flush=True)
        test=subprocess.run(['7z','t','-p'+password,'-bd',str(archive)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if test.returncode:raise ValueError('7z integrity test failed')
        stage='credential_and_filesystem_scan'
        print('VERIFY_STAGE '+stage,flush=True)
        files=[]
        for base,dirs,names in os.walk(dest,followlinks=False):
            for name in dirs+names:
                p=pathlib.Path(base)/name
                if p.is_symlink() or not p.resolve().is_relative_to(dest.resolve()):raise ValueError('Links unsupported')
            for name in names:
                p=pathlib.Path(base)/name
                if not p.is_file():raise ValueError('Special files unsupported')
                tail=b''
                with p.open('rb') as inp:
                    for chunk in iter(lambda:inp.read(1048576),b''):
                        data=tail+chunk
                        if any(secret in data for secret in secrets):raise ValueError('Known credential found')
                        if pattern.search(data):
                            match=pattern.search(data)
                            category='PRIVATE_KEY_MARKER' if match.group().startswith(b'-----BEGIN') else 'TOKEN_SHAPED_STRING'
                            finding={'category':category,'relative_path':p.relative_to(dest).as_posix(),'content_not_included':True,'automatic_bypass':False}
                            (root/'SCAN-FINDING.json').write_text(json.dumps(finding,indent=2))
                            print('SCAN_FINDING category='+category+'; details saved locally in SCAN-FINDING.json; no content printed.',flush=True)
                            raise ValueError('Credential pattern found')
                        tail=data[-4096:]
                files.append(p)
        if not files:raise ValueError('Empty archive')
        staged=pathlib.Path(tmp)/'output';staged.mkdir()
        if os.environ.get('PLAINTEXT_ZIP','').lower()=='true':
            stage='plaintext_zip_creation'
            print('VERIFY_STAGE '+stage,flush=True)
            plain=staged/f'{account}-UNENCRYPTED.zip'
            with zipfile.ZipFile(plain,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
                for base,dirs,names in os.walk(dest):
                    for name in dirs:
                        p=pathlib.Path(base)/name;z.write(p,p.relative_to(dest).as_posix()+'/')
                for p in files:z.write(p,p.relative_to(dest).as_posix())
            stage='plaintext_zip_crc_test'
            print('VERIFY_STAGE '+stage,flush=True)
            with zipfile.ZipFile(plain) as z:
                if z.testzip() is not None:raise ValueError('ZIP CRC failed')
        stage='publish_preparation'
        print('VERIFY_STAGE '+stage,flush=True)
        approved=root/f'approved-{account}';shutil.rmtree(approved,ignore_errors=True);approved.mkdir(mode=0o700)
        shutil.copy2(archive,approved/archive.name);checksum(approved/archive.name)
        manifest['encrypted_7z_integrity_verified']=True
        (approved/'COVERAGE.json').write_text(json.dumps(manifest,indent=2))
        if os.environ.get('PLAINTEXT_ZIP','').lower()=='true':
            target=root/f'plaintext-{account}';shutil.rmtree(target,ignore_errors=True);target.mkdir(mode=0o700)
            shutil.copy2(plain,target/plain.name);checksum(target/plain.name)
            (target/'COVERAGE.json').write_text(json.dumps(dict(manifest,unencrypted=True,zip_crc_verified=True),indent=2))
    except Exception as error:
        # Only allowlisted, constant diagnostic values; never raw exception text.
        known={
            'Archive must be encrypted':'ENCRYPTION_REQUIRED',
            'Unsafe path':'UNSAFE_ARCHIVE_PATH',
            'Duplicate path':'DUPLICATE_ARCHIVE_PATH',
            'Links unsupported':'LINK_NOT_SUPPORTED',
            '7z integrity test failed':'SEVENZIP_INTEGRITY_FAILED',
            'Special files unsupported':'SPECIAL_FILE_NOT_SUPPORTED',
            'Known credential found':'KNOWN_CREDENTIAL_FOUND',
            'Credential pattern found':'CREDENTIAL_PATTERN_FOUND',
            'Empty archive':'EMPTY_ARCHIVE',
            'ZIP CRC failed':'ZIP_CRC_FAILED',
        }
        code=known.get(str(error),'LIBRARY_OR_IO_FAILURE') if type(error) is ValueError else 'LIBRARY_OR_IO_FAILURE'
        allowed_types={'ValueError','OSError','PermissionError','FileNotFoundError','Bad7zFile','CrcError','PasswordRequired','DecompressionError','UnsupportedCompressionMethodError','BadZipFile','RuntimeError','EOFError','MemoryError'}
        typename=type(error).__name__
        typename=typename if typename in allowed_types else 'OTHER_EXCEPTION'
        print(f'::error::Verification blocked: stage={stage}; code={code}; type={typename}. No artifacts published.',flush=True)
        raise SystemExit(1) from None
print('7z integrity and basic credential checks passed; requested ZIP created. Full history audit/restore not verified.')
