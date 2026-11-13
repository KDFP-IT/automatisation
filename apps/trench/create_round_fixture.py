import json,urllib.request
from pathlib import Path
def req(path,data):
 r=urllib.request.Request('http://localhost:8086/api/'+path,data=json.dumps(data,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
 return json.load(urllib.request.urlopen(r))
p=req('projects',{'name':'Тест стены и группы 6.3 (временный)'})
s=req('projects/'+p['id']+'/schemes',{'name':'Проверка стены и группы 6.3','model':json.loads(Path('group-fixture.json').read_text(encoding='utf-8'))})
Path('group-test-ids.json').write_text(json.dumps({'project':p['id'],'scheme':s['id']}));print(s['id'])
