import argparse,base64,contextlib,fcntl,io,json,os,pathlib,sys,tempfile
from sever import ROOT
from runtime import link
from policy import allowed
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'_vendor'))
PLATFORMS={
 'ios':('iPhone / iPad','Happ','https://www.happ.su/main'),
 'android':('Android','Happ','https://www.happ.su/main'),
 'windows':('Windows','v2rayN или Happ','https://github.com/2dust/v2rayN/releases'),
 'macos':('macOS','Happ или v2rayN','https://www.happ.su/main'),
 'linux':('Linux','v2rayN или Happ','https://github.com/2dust/v2rayN/releases')}
def guide(platform='all'):
 names=list(PLATFORMS) if platform=='all' else [platform]
 lines=['SEVER — подключение устройств','']
 for key in names:
  title,client,url=PLATFORMS[key]
  lines.extend([title+': '+client,url,'1. Установите клиент с официальной страницы для своей ОС.','2. Скопируйте ссылку из link.txt и импортируйте из буфера обмена.','   На телефоне можно открыть сканер QR внутри клиента и отсканировать qr.png.','3. Выберите профиль Sever и включите подключение.'])
  if key in ['ios','android']: lines.append('4. При первом подключении подтвердите системный запрос на создание VPN.')
  else: lines.append('4. Для всего устройства включите VPN/TUN; системный прокси охватывает только поддерживающие его приложения. Режим TUN может запросить права администратора.')
  lines.append('')
 lines.extend(['Для Linux, Windows и macOS также есть xray.json: запустите Xray командой xray run -config xray.json.','Это локальный SOCKS5-прокси 127.0.0.1:10808, а не автоматическое перенаправление всего устройства.','Проверка: curl --proxy socks5h://127.0.0.1:10808 https://example.com','Для телефона проверьте работу сначала по Wi-Fi, затем через мобильный интернет.','Домен и сертификат для этого подключения не нужны. HTTPS-подписка не включена.','Для независимого отключения и учёта трафика создавайте отдельного пользователя для каждого устройства.','Файлы и QR-код дают доступ к VPN: передавайте их только владельцу устройства.','Совместимость формата не означает, что каждая версия клиента уже проверена на реальном устройстве.'])
 return chr(10).join(lines)+chr(10)
def client_config(server,user):
 return {'log':{'loglevel':'warning'},'inbounds':[{'tag':'local-socks','listen':'127.0.0.1','port':10808,'protocol':'socks','settings':{'auth':'noauth','udp':True}}],
 'outbounds':[{'tag':'sever','protocol':'vless','settings':{'vnext':[{'address':server['host'],'port':server['port'],'users':[{'id':user['id'],'encryption':'none','flow':'xtls-rprx-vision'}]}]},'streamSettings':{'network':'tcp','security':'reality','realitySettings':{'serverName':server['sni'],'fingerprint':'chrome','password':server['public_key'],'shortId':server['short_id']}}}]}
def save(path,data):
 if isinstance(data,str): data=data.encode()
 fd,tmp=tempfile.mkstemp(prefix='.export-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)
def prepare(name,platform='all',terminal=False):
 import qrcode
 from qrcode.image.pure import PyPNGImage
 from qrcode.image.svg import SvgPathImage
 users=json.loads((ROOT/'config/users.json').read_text())
 if name not in users or not allowed(users[name]): raise ValueError('Пользователь недоступен: отключён, срок истёк или квота исчерпана.')
 server=json.loads((ROOT/'config/server.json').read_text())
 out=io.StringIO()
 with contextlib.redirect_stdout(out): link(name)
 uri=out.getvalue().strip()
 folder=ROOT/'config/exports'/name; folder.mkdir(parents=True,exist_ok=True,mode=0o700); folder.chmod(0o700)
 qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=8,border=4)
 qr.add_data(uri); qr.make(fit=True)
 for filename,factory in [('qr.png',PyPNGImage),('qr.svg',SvgPathImage)]:
  buf=io.BytesIO(); qr.make_image(image_factory=factory).save(buf); save(folder/filename,buf.getvalue())
 save(folder/'link.txt',uri+chr(10))
 save(folder/'subscription.txt',base64.b64encode((uri+chr(10)).encode())+bytes([10]))
 save(folder/'xray.json',json.dumps(client_config(server,users[name]),indent=2)+chr(10))
 save(folder/'README.txt',guide(platform))
 if terminal: qr.print_ascii(invert=True)
 print('Профиль: '+name)
 print('Файлы подключения: '+str(folder))
 print('link.txt — импорт из буфера; qr.png / qr.svg — сканирование; xray.json — Xray; README.txt — инструкция.')
 print('Платформы: '+', '.join(PLATFORMS[k][0] for k in (PLATFORMS if platform=='all' else [platform])))
 return folder
def main():
 p=argparse.ArgumentParser(description='Подключение к Sever со всех основных платформ')
 p.add_argument('command',choices=['connect','qr','guide']); p.add_argument('name',nargs='?')
 p.add_argument('--platform',choices=['all']+list(PLATFORMS),default='all')
 a=p.parse_args(); os.umask(0o077)
 if a.command=='guide': print(guide(a.platform)); return
 if not a.name: p.error('Укажите имя пользователя')
 with open(ROOT/'.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  try: prepare(a.name,a.platform,a.command=='qr')
  except (ValueError,OSError) as e: raise SystemExit(str(e))
if __name__=='__main__': main()
