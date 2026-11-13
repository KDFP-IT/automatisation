from pathlib import Path
import json
m=json.loads(Path('dist/examples/kulko-d13.json').read_text(encoding='utf-8'));m['version']=4;m['wells'][0].update(shape='rect',width=1.4,length=1.4,rotationMode='pipe',rotation=0,zeroAngle=15)
s='''import urllib.request,json
base='http://127.0.0.1:8000/api/'
def post(path,body):return json.load(urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')))
'''
s+='m='+repr(m)+'\np=post("projects",{"name":"Проверка углов 5.1"});s=post("projects/"+p["id"]+"/schemes",{"name":"Углы — тест","model":m});print(s["id"])\n'
Path('create_ui_angles.py').write_text(s,encoding='utf-8')
