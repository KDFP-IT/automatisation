import urllib.request,json
base='http://127.0.0.1:8000/api/'
s=json.load(urllib.request.urlopen(base+'schemes/8228d97b-8338-48a8-9bbf-5f3b81a45e8a'))
p=json.load(urllib.request.urlopen(base+'projects/'+s['project_id']))
assert p['name']=='Проверка стыков 6.0' and len(p['schemes'])==1
r=json.load(urllib.request.urlopen(urllib.request.Request(base+'projects/'+p['id']+'/state',data=json.dumps({'action':'trash','revision':p['revision']}).encode(),headers={'Content-Type':'application/json'},method='POST')))
print('Test project moved to recoverable trash:',bool(r['deleted_at']))
