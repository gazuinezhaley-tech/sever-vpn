import sys, pathlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]
import json, os, pathlib, subprocess, tempfile, unittest
class CLI(unittest.TestCase):
 def test_users_and_backup(self):
  with tempfile.TemporaryDirectory() as d:
   env=dict(os.environ,SEVER_ROOT=d)
   def run(*args): return subprocess.run([sys.executable,str(SOURCE/'src/sever.py'),*args],env=env,capture_output=True,text=True)
   self.assertEqual(run('add','alice').returncode,0)
   self.assertNotEqual(run('add','alice').returncode,0)
   self.assertNotEqual(run('add','../escape').returncode,0)
   self.assertEqual(run('disable','alice').returncode,0)
   data=json.loads((pathlib.Path(d)/'config/users.json').read_text())
   self.assertFalse(data['alice']['enabled'])
   self.assertEqual((pathlib.Path(d)/'config/users.json').stat().st_mode & 0o777,0o600)
   self.assertEqual(run('enable','alice').returncode,0)
   self.assertEqual(run('backup').returncode,0)
   import tarfile
   archive=next((pathlib.Path(d)/'backups').glob('*.gz'))
   with tarfile.open(archive) as t: self.assertIn('config/users.json',t.getnames())
if __name__=='__main__': unittest.main()
