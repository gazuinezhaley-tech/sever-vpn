#!/usr/bin/env python3
import argparse, datetime, fcntl, json, os, pathlib, re, subprocess, tarfile, tempfile, uuid
ROOT=pathlib.Path(os.environ.get('SEVER_ROOT','/opt/sever'))
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'w') as f:
   json.dump(data,f,indent=2); f.flush(); os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)
def main():
 p=argparse.ArgumentParser(description='Sever server manager')
 s=p.add_subparsers(dest='cmd',required=True)
 for n in ['status','doctor','backup','users']: s.add_parser(n)
 for n in ['add','disable','enable']:
  q=s.add_parser(n); q.add_argument('name')
 a=p.parse_args(); ROOT.mkdir(parents=True,exist_ok=True); os.umask(0o077)
 with open(ROOT/'.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  db=ROOT/'config/users.json'; users=json.loads(db.read_text()) if db.exists() else {}
  if a.cmd in ['add','disable','enable']:
   if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}',a.name): p.error('Name: 1-48 letters, digits, _ or -')
   if a.cmd=='add':
    if a.name in users: p.error('User already exists')
    users[a.name]={'id':str(uuid.uuid4()),'enabled':True,'created':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   else:
    if a.name not in users: p.error('Unknown user')
    users[a.name]['enabled']=a.cmd=='enable'
   write(db,users); print('Saved. Runtime configuration must be applied before changes affect VPN.')
  elif a.cmd=='users':
   for name,u in users.items(): print(name, 'enabled' if u['enabled'] else 'disabled')
  elif a.cmd=='status':
   print('Sever 0.6.0'); print('Users:',len(users)); print('VPN:', 'configured' if (ROOT/'config/xray.json').exists() else 'not configured')
  elif a.cmd=='doctor':
   for cmd in [['uname','-sr'],['free','-h'],['df','-h',str(ROOT)],['ss','-lntup']]: subprocess.run(cmd,check=True)
  elif a.cmd=='backup':
   dest=ROOT/'backups'; dest.mkdir(exist_ok=True)
   name=dest/('sever-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.tar.gz')
   with tarfile.open(name,'w:gz') as t:
    for folder in ['config','src','bin','deploy']:
     if (ROOT/folder).exists(): t.add(ROOT/folder,arcname=folder)
   print(name)
if __name__=='__main__': main()
