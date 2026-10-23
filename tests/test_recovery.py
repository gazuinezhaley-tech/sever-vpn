import sys, pathlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]
import copy,io,json,pathlib,sys,tarfile,tempfile,unittest,uuid
sys.path.insert(0,str(SOURCE/'src'))
from recovery import read_archive,stage
class Recovery(unittest.TestCase):
 def archive(self,root,extra=None):
  server={'host':'192.0.2.1','port':443,'sni':'example.com','private_key':'a'*43,'public_key':'b'*43,'short_id':'aa'}
  users={'alice':{'id':str(uuid.uuid4()),'enabled':True,'quota_bytes':1000,'used_bytes':10,'counter_epoch':'old','counters':{'uplink':10},'subscription_token':'c'*43}}
  p=root/'backup.tar.gz'
  with tarfile.open(p,'w:gz') as t:
   for name,data in [('config/server.json',server),('config/users.json',users)]:
    b=json.dumps(data).encode(); m=tarfile.TarInfo(name); m.size=len(b); t.addfile(m,io.BytesIO(b))
   if extra: t.addfile(extra)
  return p,server,users
 def test_restore_identity_quota_host_and_permissions(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d); p,s,u=self.archive(root)
   dest=stage(p,root/'restored','198.51.100.2')
   server=json.loads((dest/'config/server.json').read_text()); users=json.loads((dest/'config/users.json').read_text())
   self.assertEqual(server['host'],'198.51.100.2'); self.assertEqual(server['private_key'],s['private_key'])
   self.assertEqual(users['alice']['id'],u['alice']['id']); self.assertEqual(users['alice']['quota_bytes'],1000)
   self.assertEqual(users['alice']['subscription_token'],u['alice']['subscription_token'])
   self.assertNotIn('counter_epoch',users['alice']); self.assertEqual(users['alice']['downlink_bytes'],10)
   self.assertEqual((dest/'config/users.json').stat().st_mode & 0o777,0o600)
   with self.assertRaises(ValueError): stage(p,dest)
 def test_reject_traversal_and_links(self):
  for name,kind in [('../escape',tarfile.REGTYPE),('config/link',tarfile.SYMTYPE)]:
   with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d); m=tarfile.TarInfo(name); m.type=kind; m.linkname='/etc/passwd'
    p,_,_=self.archive(root,m)
    with self.assertRaises(ValueError): read_archive(p)
 def test_reject_incomplete(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'empty.tar'
   with tarfile.open(p,'w'): pass
   with self.assertRaises(ValueError): read_archive(p)
if __name__=='__main__': unittest.main()
