import base64,contextlib,io,json,os,pathlib,secrets,grp
from sever import ROOT,write
from runtime import link
from policy import allowed
def publish():
 db=ROOT/'config/users.json'; users=json.loads(db.read_text()); settings=json.loads((ROOT/'config/server.json').read_text())
 records={}
 for name,u in users.items():
  token=u.setdefault('subscription_token',secrets.token_urlsafe(32))
  uri=''
  if allowed(u):
   out=io.StringIO()
   with contextlib.redirect_stdout(out): link(name)
   uri=out.getvalue().strip()
  records[token]={'enabled':u.get('enabled',False),'expires_at':u.get('expires_at',0),'quota_bytes':u.get('quota_bytes',0),'used_bytes':u.get('used_bytes',0),'uplink_bytes':u.get('uplink_bytes',0),'downlink_bytes':u.get('downlink_bytes',0),'uri':uri}
 write(db,users)
 folder=pathlib.Path('/var/lib/sever-sub'); folder.mkdir(exist_ok=True,mode=0o750)
 gid=grp.getgrnam('sever-sub').gr_gid
 os.chown(folder,0,gid); folder.chmod(0o750)
 target=folder/'data.json'; write(target,records); os.chown(target,0,gid); target.chmod(0o640)
def subscription_url(name):
 settings=json.loads((ROOT/'config/server.json').read_text()); users=json.loads((ROOT/'config/users.json').read_text())
 if name not in users or not allowed(users[name]): raise SystemExit('User disabled, expired or over quota')
 if not settings.get('https_subscription_ready'): raise SystemExit('HTTPS subscription is not enabled. Use sever link NAME or sever export NAME.')
 print('https://'+settings['host']+':8443/s/'+users[name]['subscription_token'])
