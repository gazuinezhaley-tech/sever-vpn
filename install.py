#!/usr/bin/env python3
import argparse,hashlib,ipaddress,json,os,pathlib,platform,secrets,shutil,socket,subprocess,sys,tempfile,uuid
SOURCE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE/'src'))
from recovery import read_archive,validate
from sever import write
TARGET=pathlib.Path('/opt/sever')
def run(*args,**kwargs): return subprocess.run(args,check=True,**kwargs)
def verify():
 manifest=json.loads((SOURCE/'RELEASE.json').read_text())
 for name,expected in manifest['sha256'].items():
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts: raise ValueError('Invalid manifest path')
  f=SOURCE/name
  if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=expected: raise ValueError('Checksum mismatch: '+name)
def build(dest,host,archive=None):
 if dest.exists() or dest.is_symlink(): raise ValueError('Target exists; refusing to replace it')
 dest.mkdir(mode=0o755)
 dest.chmod(0o755)
 manifest=json.loads((SOURCE/'RELEASE.json').read_text())
 for name in manifest['sha256']:
  if name in ['install.py','README.md']: continue
  target=dest/name; target.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
  shutil.copy2(SOURCE/name,target)
 for file in ['README.md','install.py','RELEASE.json']: shutil.copy2(SOURCE/file,dest/file)
 (dest/'config').mkdir(mode=0o700); (dest/'backups').mkdir(mode=0o700)
 (dest/'src').chmod(0o755)
 (dest/'vendor').chmod(0o755)
 for f in (dest/'vendor').iterdir():
  if f.is_file(): f.chmod(0o755 if f.name=='xray' else 0o644)
 if archive: server,users=read_archive(archive,host)
 else:
  raw=subprocess.check_output([str(dest/'vendor/xray'),'x25519'],text=True)
  keys=dict(line.split(':',1) for line in raw.splitlines())
  server={'host':host,'listen':'0.0.0.0','port':443,'sni':'www.cloudflare.com','private_key':keys['PrivateKey'].strip(),'public_key':keys['Password (PublicKey)'].strip(),'short_id':secrets.token_hex(8)}
  users={'owner':{'id':str(uuid.uuid4()),'enabled':True}}
 validate(server,users)
 write(dest/'config/server.json',server); write(dest/'config/users.json',users)
 env=dict(os.environ,SEVER_ROOT=str(dest))
 run(sys.executable,str(dest/'src/runtime.py'),'apply',env=env)
 (dest/'bin/sever').chmod(0o750)
 return server

def main():
 p=argparse.ArgumentParser(description='Offline Sever installer for a clean systemd server')
 p.add_argument('--host',required=True); p.add_argument('--restore'); p.add_argument('--stage-only',type=pathlib.Path)
 a=p.parse_args(); os.umask(0o077)
 host=str(ipaddress.ip_address(a.host))
 if ':' in host: p.error('This release requires an IPv4 public address')
 if platform.system()!='Linux' or platform.machine() not in ['x86_64','amd64']: p.error('Linux x86_64 is required')
 verify()
 if a.stage_only:
  build(a.stage_only.resolve(),host,a.restore); print('Staging validated; no system services were changed.'); return
 if os.geteuid()!=0: p.error('Run as root')
 if TARGET.exists() or TARGET.is_symlink(): p.error('/opt/sever exists; installation refuses to overwrite it')
 for unit in ['sever-xray.service','sever-enforce.service','sever-enforce.timer','sever-sub.service']:
  if (pathlib.Path('/etc/systemd/system')/unit).exists(): p.error('Existing Sever unit: '+unit)
 if pathlib.Path('/usr/local/bin/sever').exists() or pathlib.Path('/usr/local/bin/sever').is_symlink(): p.error('Existing sever command')
 version=subprocess.check_output(['systemctl','--version'],text=True)
 if int(version.split()[1])<247: p.error('systemd 247 or newer is required')
 if sys.version_info<(3,10): p.error('Python 3.10 or newer is required')
 for tool in ['useradd','id']:
  if not shutil.which(tool): p.error('Missing system tool: '+tool)
 if shutil.disk_usage('/opt').free<300*1024**2: p.error('At least 300 MiB free space is required')
 vpn_port=read_archive(a.restore,host)[0]['port'] if a.restore else 443
 for port in [vpn_port,10085,18081]:
  with socket.socket() as sock: sock.bind(('0.0.0.0' if port==vpn_port else '127.0.0.1',port))
 staging=pathlib.Path(tempfile.mkdtemp(prefix='.sever-install-',dir='/opt'))/'app'
 build(staging,host,a.restore)
 staging.rename(TARGET)
 for unit in (TARGET/'deploy').glob('sever-*'):
  shutil.copy2(unit,pathlib.Path('/etc/systemd/system')/unit.name)
 if subprocess.run(['id','sever-sub'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  run('useradd','--system','--no-create-home','--home-dir','/nonexistent','--shell','/usr/sbin/nologin','sever-sub')
 pathlib.Path('/usr/local/bin/sever').symlink_to(TARGET/'bin/sever')
 env=dict(os.environ,SEVER_ROOT=str(TARGET),PYTHONPATH=str(TARGET/'src'))
 run(sys.executable,'-c','from subscriptions import publish; publish()',env=env)
 run('systemctl','daemon-reload')
 run('systemctl','enable','--now','sever-xray','sever-sub','sever-enforce.timer')
 run('systemctl','is-active','--quiet','sever-xray','sever-sub','sever-enforce.timer')
 run(sys.executable,'-c','from health import wait_core; wait_core()',env=env)
 print('Sever installed. Run sever for the menu. HTTPS subscription remains disabled.')
if __name__=='__main__':
 try: main()
 except (OSError,ValueError,subprocess.CalledProcessError,KeyError) as e: raise SystemExit('Installation stopped: '+str(e))
