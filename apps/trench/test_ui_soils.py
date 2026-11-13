import urllib.request,json
base='http://127.0.0.1:8000/api/'
def req(path,body=None):
 data=None if body is None else json.dumps(body).encode()
 return json.load(urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'},method='GET' if body is None else 'PUT')))
s=req('schemes/14b397cf-b21b-44fa-bfc3-82173532dc5f');project=req('projects/'+s['project_id']);assert project['name']=='Проверка новых узлов 5.0'
m=s['model'];m['soils']=[{'id':'testsoil','name':'Суглинок (тест)','color':'#b8a889','group':'II'}]
for w in m['wells']:w['layers']=[] if w.get('kind')=='endpoint' else [{'soil':'testsoil','bottom':20}]
for e in m['edges']:e['layers']=[{'soil':'testsoil','start':20,'end':20}]
r=req('schemes/'+s['id'],{'model':m,'revision':s['revision']});print('Test scheme revision',r['revision'])
