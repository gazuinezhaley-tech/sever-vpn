import argparse,base64,contextlib,datetime,fcntl,io,json,os,pathlib,subprocess,sys,time
from sever import ROOT,write
from policy import allowed
from health import wait_core
from traffic import collect
from subscriptions import publish,subscription_url
from runtime import apply,link
os.umask(0o077)
def run(*args): subprocess.run(['/usr/local/bin/sever',*args],check=True)
def sync():
 collect()
 target=ROOT/'config/xray.json'
 previous=target.read_bytes() if target.exists() else None
 apply()
 try:
  subprocess.run(['systemctl','restart','sever-xray'],check=True)
  subprocess.run(['systemctl','is-active','--quiet','sever-xray'],check=True)
  wait_core()
 except (subprocess.CalledProcessError,RuntimeError):
  if previous is not None:
   write(target,json.loads(previous))
   subprocess.run(['systemctl','restart','sever-xray'],check=False)
  raise

def main():
 p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
 q=sub.add_parser('expire'); q.add_argument('name'); q.add_argument('days',type=int)
 q=sub.add_parser('export'); q.add_argument('name'); q.add_argument('--format',choices=['plain','base64'],default='base64')
 for n in ['sync','enforce','menu','usage']: sub.add_parser(n)
 q=sub.add_parser('subscription'); q.add_argument('name')
 q=sub.add_parser('quota'); q.add_argument('name'); q.add_argument('gib',type=float)
 a=p.parse_args()
 if a.cmd=='menu':
  while True:
   print(chr(10)+'SEVER — управление сервером'+chr(10)+'1 Статус  2 Пользователи  3 Добавить  4 Отключить'+chr(10)+'5 Включить  6 Ссылка  7 Срок  8 Подписка в файл'+chr(10)+'9 Резервная копия  10 Диагностика  11 Расход трафика\n12 Квота  13 HTTPS-подписка (не включена)  14 Восстановить в папку  15 Подключение устройств  16 QR-код  17 Инструкции  0 Выход')
   try:
    choice=input('Выберите пункт: ').strip()
    if choice=='0': return
    simple={'1':'status','2':'users','9':'backup','10':'doctor','11':'usage'}
    if choice in simple: run(simple[choice]); continue
    if choice=='14':
     run('restore',input('Архив резервной копии: ').strip(),'--to',input('Новая папка для данных: ').strip()); continue
    if choice=='17': run('guide'); continue
    name=input('Имя пользователя: ').strip()
    if choice in ['3','4','5']:
     run({'3':'add','4':'disable','5':'enable'}[choice],name); run('sync')
    elif choice=='15':
     platform=input('Устройство: 0 Все, 1 iPhone/iPad, 2 Android, 3 Windows, 4 macOS, 5 Linux: ').strip()
     choices={'0':'all','1':'ios','2':'android','3':'windows','4':'macos','5':'linux'}
     if platform not in choices: raise ValueError('Выберите устройство от 0 до 5')
     run('connect',name,'--platform',choices[platform])
    elif choice=='16': run('qr',name)
    elif choice=='6': run('link',name)
    elif choice=='7': run('expire',name,input('Срок в днях (0 — без срока): ').strip()); run('sync')
    elif choice=='8': run('export',name)
    elif choice=='12': run('quota',name,input('Квота в GiB (0 — без лимита): ').strip()); run('enforce')
    elif choice=='13': run('subscription',name)
   except (subprocess.CalledProcessError,ValueError) as e: print('Операция не выполнена:',e)
   except (EOFError,KeyboardInterrupt): return
 else:
  with open(ROOT/'.lock','a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   db=ROOT/'config/users.json'; users=json.loads(db.read_text())
   if a.cmd=='expire':
    if a.name not in users: p.error('Unknown user')
    if a.days<0 or a.days>36500: p.error('Days must be between 0 and 36500')
    users[a.name]['expires_at']=int(time.time()+a.days*86400) if a.days else 0
    write(db,users); print('Expiry saved. Run sever sync to apply.')
   elif a.cmd=='export':
    if a.name not in users or not allowed(users[a.name]): p.error('User unavailable')
    out=io.StringIO()
    with contextlib.redirect_stdout(out): link(a.name)
    data=out.getvalue().strip()+chr(10)
    if a.format=='base64': data=base64.b64encode(data.encode()).decode()+chr(10)
    folder=ROOT/'config/exports'; folder.mkdir(exist_ok=True,mode=0o700)
    target=folder/(a.name+'.'+a.format+'.txt'); target.write_text(data); target.chmod(0o600)
    print(target)
   elif a.cmd=='subscription':
    publish(); subscription_url(a.name)
   elif a.cmd=='sync':
    sync(); publish()
   elif a.cmd=='quota':
    import math
    if a.name not in users: p.error('Unknown user')
    if not math.isfinite(a.gib) or a.gib<0 or a.gib>1000000: p.error('Invalid GiB quota')
    users[a.name]['quota_bytes']=max(1,int(a.gib*1024**3)) if a.gib else 0
    write(db,users); print('Quota saved; run sever enforce to apply')
   elif a.cmd=='usage':
    users=collect()
    for name,u in users.items(): print(name,'used bytes:',u.get('used_bytes',0),'quota bytes:',u.get('quota_bytes',0))
   elif a.cmd=='enforce':
    users=collect()
    current=json.loads((ROOT/'config/xray.json').read_text())
    actual={x['id'] for x in current['inbounds'][0]['settings']['clients']}
    desired={u['id'] for u in users.values() if allowed(u)}
    if actual!=desired: sync()
    publish()
if __name__=='__main__': main()
