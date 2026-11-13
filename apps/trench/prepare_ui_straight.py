from pathlib import Path
import json
m=json.loads(Path('ui-straight.json').read_text(encoding='utf-8'))
s='''import urllib.request,json
base='http://127.0.0.1:8000/api/'
def post(path,body):return json.load(urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')))
'''
s+='m='+repr(m)+'\np=post("projects",{"name":"Проверка прямых труб 5.4"});s=post("projects/"+p["id"]+"/schemes",{"name":"Понятные ошибки — тест","model":m});print(s["id"])\n'
Path('create_ui_straight.py').write_text(s,encoding='utf-8')
