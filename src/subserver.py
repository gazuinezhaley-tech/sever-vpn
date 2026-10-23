import base64,http.server,json,os,pathlib,re,time,urllib.parse
DATA=pathlib.Path(os.environ.get('SEVER_SUB_DATA','/var/lib/sever-sub/data.json'))
def resolve(path,records,now=None):
 now=time.time() if now is None else now
 parsed=urllib.parse.urlsplit(path)
 if not re.fullmatch(r'/s/[A-Za-z0-9_-]{43}',parsed.path): return None
 item=records.get(parsed.path[3:])
 if not item or not item['enabled'] or (item['expires_at'] and item['expires_at']<=now) or (item['quota_bytes'] and item['used_bytes']>=item['quota_bytes']) or not item['uri']: return None
 body=base64.b64encode((item['uri']+chr(10)).encode())
 info='upload='+str(item['uplink_bytes'])+'; download='+str(item['downlink_bytes'])+'; total='+str(item['quota_bytes'])+'; expire='+str(item['expires_at'])
 return body,info
class Handler(http.server.BaseHTTPRequestHandler):
 server_version='Sever'; sys_version=''
 def log_message(self,*args): pass
 def do_GET(self):
  try: result=resolve(self.path,json.loads(DATA.read_text()))
  except (OSError,ValueError,KeyError): self.send_error(503); return
  if result is None:
   self.send_response(404); self.send_header('Content-Length','0'); self.end_headers(); return
  body,info=result
  self.send_response(200)
  for k,v in [('Content-Type','text/plain; charset=utf-8'),('Cache-Control','no-store'),('Subscription-Userinfo',info),('Profile-Update-Interval','1'),('Content-Length',str(len(body)))]: self.send_header(k,v)
  self.end_headers(); self.wfile.write(body)
if __name__=='__main__': http.server.HTTPServer(('127.0.0.1',18081),Handler).serve_forever()
