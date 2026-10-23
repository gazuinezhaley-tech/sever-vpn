import json,socket,time
from sever import ROOT
def wait_core(timeout=15):
 port=json.loads((ROOT/'config/server.json').read_text())['port']
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  try:
   for p in [port,10085]:
    with socket.create_connection(('127.0.0.1',p),timeout=0.5): pass
   return
  except OSError: time.sleep(0.2)
 raise RuntimeError('VPN service did not open its listening ports')
