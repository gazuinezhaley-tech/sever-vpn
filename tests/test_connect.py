import base64,json,os,pathlib,subprocess,sys,tempfile,unittest
SOURCE=pathlib.Path(__file__).resolve().parents[1]
class ConnectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.root=pathlib.Path(self.tmp.name); (self.root/'config').mkdir()
  self.server={'host':'198.51.100.10','port':443,'sni':'www.example.com','public_key':'A'*43,'short_id':'1234567890abcdef','private_key':'PRIVATE_SERVER_KEY_NEVER_EXPORT'}
  self.user={'id':'00000000-0000-4000-8000-000000000001','enabled':True}
  (self.root/'config/server.json').write_text(json.dumps(self.server)); self.save_user()
 def save_user(self): (self.root/'config/users.json').write_text(json.dumps({'device':self.user}))
 def run_cli(self,*args):
  env=dict(os.environ,SEVER_ROOT=str(self.root),PYTHONNOUSERSITE='1'); env.pop('PYTHONPATH',None)
  return subprocess.run([sys.executable,str(SOURCE/'src/connect.py'),*args],env=env,capture_output=True,text=True)
 def test_all_platform_exports_and_private_material(self):
  for platform in ['ios','android','windows','macos','linux']:
   with self.subTest(platform=platform):
    result=self.run_cli('connect','device','--platform',platform); self.assertEqual(result.returncode,0,result.stderr)
    folder=self.root/'config/exports/device'; uri=(folder/'link.txt').read_bytes()
    self.assertEqual(base64.b64decode((folder/'subscription.txt').read_bytes()),uri)
    self.assertTrue((folder/'qr.png').read_bytes().startswith(bytes([137,80,78,71,13,10,26,10])))
    self.assertIn(b'<svg',(folder/'qr.svg').read_bytes())
    cfg=json.loads((folder/'xray.json').read_text()); self.assertEqual(cfg['inbounds'][0]['listen'],'127.0.0.1')
    self.assertEqual(cfg['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'],self.user['id'])
    for f in folder.iterdir():
     self.assertEqual(f.stat().st_mode&0o077,0)
     self.assertNotIn(self.server['private_key'].encode(),f.read_bytes())
    self.assertEqual(folder.stat().st_mode&0o077,0)
 def test_unavailable_users_do_not_export(self):
  for policy in [{'enabled':False},{'expires_at':1},{'quota_bytes':1,'used_bytes':1}]:
   self.user={'id':'00000000-0000-4000-8000-000000000001','enabled':True,**policy}; self.save_user()
   self.assertNotEqual(self.run_cli('connect','device').returncode,0)
   self.assertFalse((self.root/'config/exports/device').exists())
 def test_guide_and_terminal_qr(self):
  r=self.run_cli('guide'); self.assertEqual(r.returncode,0,r.stderr)
  for title in ['iPhone','Android','Windows','macOS','Linux']: self.assertIn(title,r.stdout)
  r=self.run_cli('qr','device'); self.assertEqual(r.returncode,0,r.stderr); self.assertGreater(len(r.stdout),1000)
if __name__=='__main__': unittest.main()
