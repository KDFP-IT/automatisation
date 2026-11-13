from pathlib import Path
import json
m=json.loads(Path('ui-junctions.json').read_text(encoding='utf-8'));m['wells'][2].update(name='К1',shape='rect',width=2,length=2,rotationMode='manual',rotation=20,zeroAngle=0)
s='''import urllib.request,json
base='http://127.0.0.1:8000/api/'
def post(path,body):return json.load(urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')))
'''
s+='m='+repr(m)+'\np=post("projects",{"name":"Проверка исправлений 5.3"});s=post("projects/"+p["id"]+"/schemes",{"name":"Подключения — тест","model":m});print(s["id"])\n'
Path('create_ui_friendly.py').write_text(s,encoding='utf-8')
