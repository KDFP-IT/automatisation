import urllib.request,json
base='http://127.0.0.1:8000/api/'
s=json.load(urllib.request.urlopen(base+'schemes/b0ac3bd5-0e89-4f20-88ef-deb6d76e0dfe'))
p=json.load(urllib.request.urlopen(base+'projects/'+s['project_id']))
assert p['name']=='Проверка узлов 5.2' and len(p['schemes'])==1
body=json.dumps({'action':'trash','revision':p['revision']}).encode()
r=json.load(urllib.request.urlopen(urllib.request.Request(base+'projects/'+p['id']+'/state',data=body,headers={'Content-Type':'application/json'},method='POST')))
print('Test project moved to recoverable trash:',bool(r['deleted_at']))
