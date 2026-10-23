import sys, pathlib
SOURCE=pathlib.Path(__file__).resolve().parents[1]
import sys,unittest
sys.path.insert(0,str(SOURCE/'src'))
from traffic import accumulate
from policy import allowed
def sample(up,down): return {'stat':[{'name':'user>>>alice>>>traffic>>>uplink','value':str(up)},{'name':'user>>>alice>>>traffic>>>downlink','value':str(down)}]}
class Traffic(unittest.TestCase):
 def test_idempotency_restart_and_quota(self):
  u={'alice':{'enabled':True,'quota_bytes':400}}
  accumulate(u,sample(100,200),'one'); self.assertEqual(u['alice']['used_bytes'],300)
  accumulate(u,sample(100,200),'one'); self.assertEqual(u['alice']['used_bytes'],300)
  accumulate(u,sample(120,220),'one'); self.assertEqual(u['alice']['used_bytes'],340)
  accumulate(u,sample(20,30),'two'); self.assertEqual(u['alice']['used_bytes'],390)
  self.assertTrue(allowed(u['alice']))
  accumulate(u,sample(30,30),'two'); self.assertFalse(allowed(u['alice']))
 def test_decreased_counters(self):
  u={'alice':{'enabled':True}}
  accumulate(u,sample(100,100),'one'); accumulate(u,sample(10,20),'one')
  self.assertEqual(u['alice']['used_bytes'],230)
if __name__=='__main__': unittest.main()
