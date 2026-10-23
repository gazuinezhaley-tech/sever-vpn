import json, pathlib, subprocess, sys, secrets, urllib.parse, os, fcntl
from sever import ROOT, write
from policy import allowed
BIN=ROOT/'vendor/xray'
def apply():
 settings=json.loads((ROOT/'config/server.json').read_text())
 users=json.loads((ROOT/'config/users.json').read_text())
 clients=[{'id':u['id'],'email':name,'flow':'xtls-rprx-vision'} for name,u in users.items() if allowed(u)]
 cfg={'log':{'loglevel':'warning'},'inbounds':[{'listen':settings.get('listen','127.0.0.1'),'port':settings['port'],'protocol':'vless','settings':{'clients':clients,'decryption':'none'},'streamSettings':{'network':'tcp','security':'reality','realitySettings':{'show':False,'target':settings['sni']+':443','xver':0,'serverNames':[settings['sni']],'privateKey':settings['private_key'],'shortIds':[settings['short_id']]}}}],'outbounds':[{'protocol':'freedom','tag':'direct'},{'protocol':'blackhole','tag':'block'}],'routing':{'rules':[{'type':'field','ip':['geoip:private'],'outboundTag':'block'}]}}
 cfg['stats']={}
 cfg['api']={'tag':'api','listen':'127.0.0.1:10085','services':['StatsService']}
 cfg['policy']={'levels':{'0':{'statsUserUplink':True,'statsUserDownlink':True}}}
 candidate=ROOT/'config/candidate.json'; write(candidate,cfg)
 subprocess.run([str(BIN),'run','-test','-config',str(candidate)],check=True,cwd=BIN.parent)
 candidate.replace(ROOT/'config/xray.json')
 print('Configuration validated and saved; restart service to apply.')
def link(name):
 s=json.loads((ROOT/'config/server.json').read_text()); u=json.loads((ROOT/'config/users.json').read_text())[name]
 if not allowed(u): raise SystemExit('User disabled or expired')
 q=urllib.parse.urlencode({'encryption':'none','security':'reality','sni':s['sni'],'fp':'chrome','pbk':s['public_key'],'sid':s['short_id'],'type':'tcp','flow':'xtls-rprx-vision'})
 print('vless://'+u['id']+'@'+s['host']+':'+str(s['port'])+'?'+q+'#'+urllib.parse.quote('Sever-'+name))
if __name__=='__main__':
 os.umask(0o077)
 lock=open(ROOT/'.lock','a')
 fcntl.flock(lock,fcntl.LOCK_EX)
 if sys.argv[1]=='apply': apply()
 elif sys.argv[1]=='link': link(sys.argv[2])
