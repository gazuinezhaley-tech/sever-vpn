import sys, pathlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]
import base64,sys,unittest
sys.path.insert(0,str(SOURCE/'src'))
from subserver import resolve
class Subscriptions(unittest.TestCase):
 def test_access(self):
  token='a'*43
  item={'enabled':True,'expires_at':200,'quota_bytes':100,'used_bytes':20,'uplink_bytes':5,'downlink_bytes':15,'uri':'vless://example'}
  data={token:item}
  result=resolve('/s/'+token,data,100)
  self.assertEqual(base64.b64decode(result[0]),b'vless://example'+bytes([10]))
  self.assertIn('total=100',result[1])
  self.assertIsNone(resolve('/s/'+'b'*43,data,100))
  self.assertIsNone(resolve('/s/'+token,data,200))
  item['enabled']=False; self.assertIsNone(resolve('/s/'+token,data,100))
  item['enabled']=True; item['used_bytes']=100
  self.assertIsNone(resolve('/s/'+token,data,100))
if __name__=='__main__': unittest.main()
