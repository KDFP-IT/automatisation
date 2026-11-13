from pathlib import Path
import json
m=json.loads(Path('analysis-current.json').read_text(encoding='utf-8'));m['soils']=[{'id':'qa-soil','name':'Тестовый однородный грунт','color':'#b8a889','group':'II'}];m['notes']='Тестовая копия для проверки общей выемки. Однородный грунт задан только для проверки программы, не является геологией исходного проекта.'
for w in m['wells']:
 if w.get('kind')!='endpoint':w['layers']=[{'soil':'qa-soil','bottom':20}]
for e in m['edges']:e['layers']=[{'soil':'qa-soil','start':20,'end':20}]
s='''import urllib.request,json
base='http://127.0.0.1:8000/api/'
def post(path,body):return json.load(urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')))
'''
s+='m='+repr(m)+'\np=post("projects",{"name":"Проверка стыков 6.0"});s=post("projects/"+p["id"]+"/schemes",{"name":"Два стыка — тестовый грунт","model":m});print(s["id"])\n'
Path('create_ui_union.py').write_text(s,encoding='utf-8')
