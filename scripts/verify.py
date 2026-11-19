"""Fail closed. Basic credential check, not a complete Git history secret audit."""
import os, pathlib, subprocess, tempfile, tarfile, re, hashlib, shutil, json
root=pathlib.Path(os.environ['RUNNER_TEMP'])
account=os.environ['ACCOUNT']
archives=list((root/f'out-{account}').glob('*.tar.gz.gpg'))
if len(archives)!=1: raise SystemExit('Exactly one encrypted archive required')
archive=archives[0]
secrets=[os.environ[k].encode() for k in ('GH_TOKEN','ARCHIVE_PASSWORD') if os.environ.get(k)]
pattern=re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
with tempfile.TemporaryFile() as plaintext:
    result=subprocess.run(['gpg','--batch','--quiet','--pinentry-mode','loopback','--passphrase-fd','0','--decrypt',str(archive)],input=secrets[1]+b'\n',stdout=plaintext,stderr=subprocess.DEVNULL)
    if result.returncode:raise SystemExit('Decrypt verification failed')
    plaintext.seek(0)
    with tarfile.open(fileobj=plaintext,mode='r|gz') as tar:
        count=0
        for member in tar:
            if not member.isfile():continue
            stream=tar.extractfile(member);tail=b''
            while True:
                chunk=stream.read(1024*1024)
                if not chunk:break
                data=tail+chunk
                if any(secret in data for secret in secrets) or pattern.search(data):
                    raise SystemExit('Potential credential found; upload blocked. No content printed.')
                tail=data[-4096:]
            count+=1
        if count==0:raise SystemExit('Empty archive rejected')
approved=root/f'approved-{account}';approved.mkdir(mode=0o700)
shutil.copy2(archive,approved/archive.name)
hashobj=hashlib.sha256()
with archive.open('rb') as file:
    for chunk in iter(lambda:file.read(1024*1024),b''):hashobj.update(chunk)
(approved/(archive.name+'.sha256')).write_text(hashobj.hexdigest()+'  '+archive.name+'\n')
(approved/'COVERAGE.json').write_text(json.dumps({'account':account,'kind':'user','decrypt_and_tar_read':True,'basic_credential_check':True,'full_git_history_secret_audit':False,'restore_test':False,'all_accessible_orgs_backed_up':False,'complete_backup_verified':False},indent=2))
print('Encrypted archive decrypted, tar read, basic credential check passed. Full coverage/restore not verified.')
