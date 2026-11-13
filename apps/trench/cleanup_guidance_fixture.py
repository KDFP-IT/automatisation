import urllib.request,json
from pathlib import Path
ids=json.loads(Path('guide-test-ids.json').read_text());url='http://localhost:8086/api/projects/'+ids['project'];p=json.load(urllib.request.urlopen(url));assert p['name']=='Проверка подсказок 7.3 (временный)';assert {s['id'] for s in p['schemes']}==set(ids['schemes'])
for sid in ids['schemes']:
 m=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/'+sid))['model']
 if len(m['edges'])==1:assert abs(m['wells'][0]['ports'][0]['invert']-118.599)<1e-8
 else:
  e=m['edges'][0]
  for side in ['from','to']:
   ref=e[side];w=next(w for w in m['wells'] if w['id']==ref['well']);assert next(port for port in w['ports'] if port['id']==ref['port'])['invert']==118
print('UI corrections persisted in both test schemes')
r=urllib.request.Request(url+'/state',data=json.dumps({'action':'trash','revision':p['revision']}).encode(),headers={'Content-Type':'application/json'},method='POST');result=json.load(urllib.request.urlopen(r));assert result['deleted_at'];print('Temporary project moved to recoverable trash')
