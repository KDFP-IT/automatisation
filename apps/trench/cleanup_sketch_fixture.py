import json,urllib.request
from pathlib import Path
ids=json.loads(Path('group-test-ids.json').read_text())
url='http://localhost:8086/api/projects/'+ids['project']
p=json.load(urllib.request.urlopen(url))
assert p['name']=='Тест стены и группы 7.2 (временный)'
assert [s['id'] for s in p['schemes']]==[ids['scheme']]
r=urllib.request.Request(url+'/state',data=json.dumps({'action':'trash','revision':p['revision']}).encode(),headers={'Content-Type':'application/json'},method='POST')
res=json.load(urllib.request.urlopen(r));assert res['deleted_at'];print('Temporary project moved to recoverable trash')

