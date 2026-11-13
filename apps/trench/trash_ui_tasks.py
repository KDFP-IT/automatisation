import urllib.request,json
base='http://127.0.0.1:8000/api/'
s=json.load(urllib.request.urlopen(base+'schemes/4687ee9d-93da-4bc0-bdb3-20819022c4f0'))
p=json.load(urllib.request.urlopen(base+'projects/'+s['project_id']))
assert p['name']=='Проверка списка данных 5.5' and len(p['schemes'])==1
r=json.load(urllib.request.urlopen(urllib.request.Request(base+'projects/'+p['id']+'/state',data=json.dumps({'action':'trash','revision':p['revision']}).encode(),headers={'Content-Type':'application/json'},method='POST')))
print('Test copy moved to recoverable trash:',bool(r['deleted_at']))
