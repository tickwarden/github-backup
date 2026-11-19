import importlib.util, io, os, json, tempfile, pathlib, subprocess, unittest, zipfile
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify',P/'scripts/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
PASSWORD='test-only-strong-password-0123456789'
TOKEN='ghp_'+'A'*36
class UnitTests(unittest.TestCase):
 def test_safe_names(self):v.validate_names(['root','root/repositories/a/file'])
 def test_absolute(self):self.assertRaises(v.Blocked,v.validate_names,['/etc/passwd'])
 def test_parent(self):self.assertRaises(v.Blocked,v.validate_names,['root/../x'])
 def test_backslash(self):self.assertRaises(v.Blocked,v.validate_names,['root\\x'])
 def test_drive(self):self.assertRaises(v.Blocked,v.validate_names,['C:/x'])
 def test_duplicate(self):self.assertRaises(v.Blocked,v.validate_names,['a/x','a/./x'])
 def test_empty(self):self.assertRaises(v.Blocked,v.validate_names,[''])
 def test_unit(self):self.assertEqual(v.unit_for(pathlib.Path('root/repositories/a/repository/config')),'root/repositories/a')
 def test_dot_unit(self):self.assertEqual(v.unit_for(pathlib.Path('root/repositories/.github/a')),'root/repositories/.github')
 def test_metadata_not_unit(self):self.assertIsNone(v.unit_for(pathlib.Path('root/org-meta/profile.json')))
 def test_known_secret(self):self.assertEqual(v.matches(b'hello password here',[b'password']),'KNOWN_CREDENTIAL')
 def test_token(self):self.assertEqual(v.matches(TOKEN.encode(),[]),'TOKEN_PATTERN')
 def test_private_marker(self):self.assertEqual(v.matches(b'-----BEGIN OPENSSH PRIVATE KEY-----',[]),'PRIVATE_KEY_MARKER')
 def test_plain(self):self.assertIsNone(v.matches(b'public ordinary content',[]))
 def test_cross_chunk(self):self.assertEqual(v.scan_stream(io.BytesIO(b'x'*(1048576-5)+TOKEN.encode()),[]),'TOKEN_PATTERN')
 def test_length_consumption(self):
  f=io.BytesIO(TOKEN.encode()+b'xyz\nnext');self.assertEqual(v.scan_stream(f,[],len(TOKEN)+3),'TOKEN_PATTERN');self.assertEqual(f.read(),b'\nnext')
 def test_truncated(self):self.assertRaises(v.Blocked,v.scan_stream,io.BytesIO(b'a'),[],5)
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.source=self.root/'src';self.source.mkdir();self.out=self.root/'out-tickwarden';self.out.mkdir()
 def tearDown(self):self.tmp.cleanup()
 def file(self,path,content):
  p=self.source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);return p
 def pack(self,password=PASSWORD):
  subprocess.run(['7z','a','-t7z','-mhe=on','-p'+password,str(self.out/'test.7z'),'.'],cwd=self.source,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
 def runverify(self,zip=False,password=PASSWORD):
  env=dict(os.environ,RUNNER_TEMP=str(self.root),ACCOUNT='tickwarden',GH_TOKEN=TOKEN,ARCHIVE_PASSWORD=password,PLAINTEXT_ZIP=str(zip).lower())
  return subprocess.run([os.sys.executable,str(P/'scripts/verify.py')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60)
 def report(self):return json.loads((self.root/'report-tickwarden/SCAN-REPORT.json').read_text())
 def test_clean_7z(self):
  self.file('root/repositories/clean/readme','hello');self.pack();r=self.runverify();self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(self.report()['status'],'passed_basic_checks');self.assertTrue(list((self.root/'approved-tickwarden').glob('*.7z')))
 def test_zip_crc(self):
  self.file('root/repositories/clean/readme','hello');self.pack();r=self.runverify(True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  with zipfile.ZipFile(next((self.root/'plaintext-tickwarden').glob('*.zip'))) as z:self.assertIsNone(z.testzip());self.assertEqual(z.read('root/repositories/clean/readme'),b'hello')
 def test_whole_unit_withheld(self):
  self.file('root/repositories/bad/key','-----BEGIN RSA PRIVATE KEY-----');self.file('root/repositories/bad/innocent','must also be withheld');self.file('root/repositories/good/readme','safe');self.pack();r=self.runverify(True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(self.report()['status'],'partial')
  with zipfile.ZipFile(next((self.root/'plaintext-tickwarden').glob('*.zip'))) as z:self.assertFalse(any('/bad/' in n for n in z.namelist()));self.assertTrue(any('/good/' in n for n in z.namelist()))
 def test_account_metadata_blocks(self):
  self.file('root/org-meta/profile',TOKEN);self.pack();r=self.runverify();self.assertNotEqual(r.returncode,0);self.assertEqual(self.report()['error_code'],'ACCOUNT_METADATA_OR_UNMAPPED_FINDING');self.assertFalse((self.root/'approved-tickwarden').exists());self.assertNotIn(TOKEN,r.stdout+r.stderr)
 def test_wrong_password(self):
  self.file('root/a','hello');self.pack();r=self.runverify(password='wrong-but-long-password-0123456789');self.assertNotEqual(r.returncode,0);self.assertFalse((self.root/'approved-tickwarden').exists())
 def test_corrupt(self):
  (self.out/'bad.7z').write_bytes(b'not an archive');r=self.runverify();self.assertNotEqual(r.returncode,0)
 def test_multiple_archives(self):
  (self.out/'a.7z').write_bytes(b'a');(self.out/'b.7z').write_bytes(b'b');r=self.runverify();self.assertNotEqual(r.returncode,0);self.assertEqual(self.report()['error_code'],'ONE_ARCHIVE_REQUIRED')
 def test_missing_archive(self):
  r=self.runverify();self.assertNotEqual(r.returncode,0)
 def test_report_no_matching_content(self):
  self.file('root/repositories/bad/readme',TOKEN);self.file('root/a','safe');self.pack();r=self.runverify();self.assertEqual(r.returncode,0,r.stdout+r.stderr);report=(self.root/'report-tickwarden/SCAN-REPORT.json').read_text();self.assertNotIn(TOKEN,report);self.assertNotIn(PASSWORD,report)
 def test_git_compressed_object(self):
  p=self.root/'git';subprocess.run(['git','init','--bare',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  subprocess.run(['git','--git-dir='+str(p),'hash-object','-w','--stdin'],input=TOKEN.encode(),stdout=subprocess.DEVNULL,check=True)
  self.assertIn('TOKEN_PATTERN',v.scan_git(p,[]))
 def test_safe_git_objects(self):
  p=self.root/'git';subprocess.run(['git','init','--bare',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  subprocess.run(['git','--git-dir='+str(p),'hash-object','-w','--stdin'],input=b'innocent',stdout=subprocess.DEVNULL,check=True)
  self.assertFalse(v.scan_git(p,[]))
if __name__=='__main__':unittest.main()

class WorkflowTests(unittest.TestCase):
 def setUp(self):self.workflow=(P/'.github/workflows/backup.yml').read_text()
 def test_hosted_only(self):self.assertNotIn('self-hosted',self.workflow);self.assertEqual(self.workflow.count('runs-on: ubuntu-24.04'),4)
 def test_no_helper_references(self):
  for name in ['run-with-progress.py','capture-persistent.sh','plaintext-zip.py']:self.assertNotIn(name,self.workflow)
 def test_no_private_requirement(self):self.assertNotIn('Backup publication blocked: this repository is public',self.workflow)
 def test_no_summary_dependency(self):self.assertNotIn('GITHUB_STEP_SUMMARY',self.workflow)
 def test_script_count(self):self.assertEqual({p.name for p in (P/'scripts').iterdir() if p.is_file()},{'backup-org.sh','verify.py'})
 def test_no_test_job(self):self.assertNotIn('  tests:',self.workflow)
