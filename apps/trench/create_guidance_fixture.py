import urllib.request,json
from pathlib import Path
def call(path,body):return json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8086/api/'+path,data=json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')))
p=call('projects',{'name':'Проверка подсказок 7.3 (временный)'})
ids={'project':p['id'],'schemes':[]}
for file,name in [('guide-height.json','Проверка высоты подключения'),('guide-cross.json','Проверка пересечения труб')]:
 s=call('projects/'+p['id']+'/schemes',{'name':name,'model':json.loads(Path(file).read_text(encoding='utf-8'))});ids['schemes'].append(s['id'])
Path('guide-test-ids.json').write_text(json.dumps(ids));print(json.dumps(ids))
