import urllib.request,json
base='http://127.0.0.1:8000/api/'
s=json.load(urllib.request.urlopen(base+'schemes/4ca14004-c091-47be-96dc-142f0512d963'))
p=json.load(urllib.request.urlopen(base+'projects/'+s['project_id']))
assert p['name']=='Проверка прямых труб 5.4' and len(p['schemes'])==1
r=json.load(urllib.request.urlopen(urllib.request.Request(base+'projects/'+p['id']+'/state',data=json.dumps({'action':'trash','revision':p['revision']}).encode(),headers={'Content-Type':'application/json'},method='POST')))
print('Test project moved to recoverable trash:',bool(r['deleted_at']))
