import argparse,ipaddress,json,os,pathlib,re,tarfile,uuid
from sever import ROOT,write
REQUIRED={'config/server.json','config/users.json'}
def validate(server,users):
 ipaddress.ip_address(server['host'])
 if type(server.get('port')) is not int or not 1<=server['port']<=65535: raise ValueError('Invalid server port')
 if not re.fullmatch(r'[A-Za-z0-9.-]{1,253}',server['sni']): raise ValueError('Invalid server name')
 for key in ['private_key','public_key']:
  if not re.fullmatch(r'[A-Za-z0-9_-]{43}',server[key]): raise ValueError('Invalid REALITY key')
 if not re.fullmatch(r'(?:[a-fA-F0-9]{2}){1,8}',server['short_id']): raise ValueError('Invalid short ID')
 if not isinstance(users,dict) or len(users)>10000: raise ValueError('Invalid users')
 ids=set()
 for name,u in users.items():
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',name): raise ValueError('Invalid username')
  uid=str(uuid.UUID(u['id']))
  if uid in ids: raise ValueError('Duplicate user ID')
  ids.add(uid)
  if type(u['enabled']) is not bool: raise ValueError('Invalid enabled flag')
  for key in ['expires_at','quota_bytes','used_bytes','uplink_bytes','downlink_bytes']:
   if type(u.get(key,0)) is not int or u.get(key,0)<0: raise ValueError('Invalid '+key)
  if 'subscription_token' in u and not re.fullmatch(r'[A-Za-z0-9_-]{43}',u['subscription_token']): raise ValueError('Invalid token')
 return server,users
def read_archive(archive,host=None):
 found={}
 with tarfile.open(archive,'r:*') as t:
  for index,m in enumerate(t):
   if index>100000: raise ValueError('Too many archive entries')
   path=pathlib.PurePosixPath(m.name)
   if path.is_absolute() or '..' in path.parts or m.issym() or m.islnk() or not (m.isfile() or m.isdir()): raise ValueError('Unsafe archive entry')
   name=str(path)
   if name in REQUIRED:
    if name in found or not m.isfile() or m.size>20*1024*1024: raise ValueError('Invalid or duplicate configuration entry')
    found[name]=json.load(t.extractfile(m))
 if set(found)!=REQUIRED: raise ValueError('Backup must contain server.json and users.json')
 server,users=validate(found['config/server.json'],found['config/users.json'])
 if host: server['host']=str(ipaddress.ip_address(host))
 server['https_subscription_ready']=False
 for u in users.values():
  u.pop('counters',None); u.pop('counter_epoch',None)
  total=u.get('uplink_bytes',0)+u.get('downlink_bytes',0)
  if u.get('used_bytes',0)>total: u['downlink_bytes']=u.get('downlink_bytes',0)+u['used_bytes']-total
 return server,users
def stage(archive,destination,host=None):
 server,users=read_archive(archive,host)
 destination=pathlib.Path(destination)
 if destination.exists() or destination.is_symlink(): raise ValueError('Destination must not exist')
 destination.mkdir(parents=False,mode=0o700)
 write(destination/'config/server.json',server); write(destination/'config/users.json',users)
 return destination
def main():
 p=argparse.ArgumentParser(description='Restore data into a new private directory; never execute backup code')
 p.add_argument('archive'); p.add_argument('--to',required=True); p.add_argument('--host')
 a=p.parse_args(); os.umask(0o077)
 try: dest=stage(a.archive,a.to,a.host)
 except (OSError,ValueError,KeyError,TypeError,tarfile.TarError) as e: p.exit(1,'Restore rejected: '+str(e)+chr(10))
 print('Data restored to',dest); print('Existing VPN configuration was not changed.')
if __name__=='__main__': main()
