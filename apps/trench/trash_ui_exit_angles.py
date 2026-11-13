import urllib.request,json
base='http://127.0.0.1:8000/api/'
s=json.load(urllib.request.urlopen(base+'schemes/f1713611-f655-4c3f-9a52-379c2130c7da'))
p=json.load(urllib.request.urlopen(base+'projects/'+s['project_id']))
assert p['name']=='Проверка углов 5.1' and len(p['schemes'])==1
body=json.dumps({'action':'trash','revision':p['revision']}).encode()
r=json.load(urllib.request.urlopen(urllib.request.Request(base+'projects/'+p['id']+'/state',data=body,headers={'Content-Type':'application/json'},method='POST')))
print('Temporary test project moved to recoverable trash:',bool(r['deleted_at']))
