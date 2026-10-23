import json,subprocess
from sever import ROOT,write
def accumulate(users,stats,epoch):
 for item in stats.get('stat',[]):
  parts=item.get('name','').split('>>>')
  if len(parts)!=4 or parts[0]!='user' or parts[2]!='traffic' or parts[3] not in ['uplink','downlink'] or parts[1] not in users: continue
  u=users[parts[1]]; direction=parts[3]; value=int(item.get('value',0))
  if value<0: raise ValueError('Negative traffic counter')
  last=u.setdefault('counters',{})
  before=int(last.get(direction,0)) if u.get('counter_epoch')==epoch else 0
  delta=value-before if value>=before else value
  u[direction+'_bytes']=int(u.get(direction+'_bytes',0))+delta
  if u.get('counter_epoch')!=epoch:
   last.clear(); u['counter_epoch']=epoch
  last[direction]=value
 for u in users.values(): u['used_bytes']=u.get('uplink_bytes',0)+u.get('downlink_bytes',0)
 return users
def collect():
 epoch=subprocess.check_output(['systemctl','show','sever-xray','--property=InvocationID','--value'],text=True).strip()
 if not epoch: raise RuntimeError('VPN service is not running')
 raw=subprocess.check_output([str(ROOT/'vendor/xray'),'api','statsquery','--server=127.0.0.1:10085','-pattern','user>>>'],text=True,timeout=8)
 after=subprocess.check_output(['systemctl','show','sever-xray','--property=InvocationID','--value'],text=True).strip()
 if after!=epoch: raise RuntimeError('VPN restarted during collection; retry')
 db=ROOT/'config/users.json'; users=json.loads(db.read_text())
 accumulate(users,json.loads(raw),epoch); write(db,users)
 return users
