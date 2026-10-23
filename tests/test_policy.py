import sys, pathlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]
import base64,json,os,pathlib,subprocess,tempfile,unittest,sys
sys.path.insert(0,str(SOURCE/'src'))
from policy import allowed
class Policy(unittest.TestCase):
 def test_boundary(self):
  self.assertTrue(allowed({'enabled':True},100))
  self.assertFalse(allowed({'enabled':False},100))
  self.assertFalse(allowed({'enabled':True,'expires_at':100},100))
  self.assertTrue(allowed({'enabled':True,'expires_at':101},100))
 def test_exports_and_expiry(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d); (root/'config').mkdir()
   (root/'config/users.json').write_text(json.dumps({'alice':{'id':'test-id','enabled':True}}))
   (root/'config/server.json').write_text(json.dumps({'host':'127.0.0.1','port':443,'sni':'example.com','public_key':'test','short_id':'aa'}))
   env=dict(os.environ,SEVER_ROOT=d)
   def run(*args): return subprocess.run([sys.executable,str(SOURCE/'src/manage.py'),*args],env=env,capture_output=True,text=True)
   self.assertEqual(run('expire','alice','30').returncode,0)
   self.assertNotEqual(run('expire','alice','-1').returncode,0)
   self.assertEqual(run('export','alice').returncode,0)
   f=root/'config/exports/alice.base64.txt'
   self.assertTrue(base64.b64decode(f.read_text()).startswith(b'vless://test-id@'))
   self.assertEqual(f.stat().st_mode & 0o777,0o600)
   u=json.loads((root/'config/users.json').read_text()); u['alice']['expires_at']=1
   (root/'config/users.json').write_text(json.dumps(u))
   self.assertNotEqual(run('export','alice').returncode,0)
if __name__=='__main__': unittest.main()
