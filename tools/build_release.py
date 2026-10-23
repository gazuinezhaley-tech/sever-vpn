import hashlib,json,pathlib,tarfile
root=pathlib.Path(__file__).resolve().parents[1]
files=[root/'install.py',root/'README.md']
for folder in ['src','bin','deploy','tests','tools','docs']:
 files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for name in ['xray','geoip.dat','geosite.dat','LICENSE']: files.append(root/'vendor'/name)
manifest={'version':'0.6.0','platform':'linux-x86_64','sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
(root/'RELEASE.json').write_text(json.dumps(manifest,indent=2)+chr(10))
target=root/'dist/sever-0.6.0-linux-x86_64.tar.gz'
target.parent.mkdir(exist_ok=True)
with tarfile.open(target,'w:gz') as t:
 for f in files+[root/'RELEASE.json']: t.add(f,arcname='sever/'+str(f.relative_to(root)),recursive=False)
(target.parent/(target.name+'.sha256')).write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+chr(10))
print(target)
