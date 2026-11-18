import os,sys,unittest,tempfile,json,copy,sqlite3
from contextlib import closing
from pathlib import Path
os.environ['TRENCH_TESTING']='1'
sys.path.insert(0,str(Path(__file__).resolve().parent/'api'))
from app import create_app
MODEL=json.loads((Path(__file__).resolve().parent/'dist/examples/kulko-d13.json').read_text(encoding='utf-8'))
class CatalogueTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.path=str(Path(self.tmp.name)/'db.sqlite3');self.app=create_app(self.path);self.client=self.app.test_client()
 def tearDown(self):self.tmp.cleanup()
 def project(self,title='Кулько'):
  r=self.client.post('/api/projects',json={'name':title});self.assertEqual(r.status_code,201);return r.json
 def test_same_origin_with_port_can_create_project(self):
  response=self.client.post('/api/projects',base_url='http://portal.example:8090',headers={'Origin':'http://portal.example:8090'},json={'name':'Проверка Origin'})
  self.assertEqual(response.status_code,201,response.json)
 def test_foreign_origin_cannot_create_project(self):
  response=self.client.post('/api/projects',base_url='http://portal.example:8090',headers={'Origin':'http://other.example:8090'},json={'name':'Чужой запрос'})
  self.assertEqual(response.status_code,403,response.json)
  self.assertEqual(self.client.get('/api/projects').json['projects'],[])
 def scheme(self,pid):
  r=self.client.post('/api/projects/'+pid+'/schemes',json={'model':MODEL,'name':'Д13 — Д13′'});self.assertEqual(r.status_code,201,r.json);return r.json
 def test_v4_node_fields_roundtrip_and_physical_counts(self):
  model=copy.deepcopy(MODEL);model['version']=4
  model['wells'][0]['ports'][0]['wall']=2
  model['edges'][0]['waypoints'].insert(0,{'id':'test-auto-lead','x':1,'y':0,'ground':None,'invert':None,'autoPort':model['edges'][0]['from']['well']})
  model['wells'][0].update(kind='endpoint',rotation=32,zeroAngle=10,rotationMode='manual',heightMode='total',height=3.7)
  project=self.project();r=self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':model,'name':'Узлы'})
  self.assertEqual(r.status_code,201,r.json);item=r.json
  self.assertEqual(item['well_count'],len(model['wells'])-1);self.assertEqual(item['endpoint_count'],1)
  self.assertEqual(self.client.get('/api/schemes/'+item['id']).json['model']['wells'][0]['height'],3.7)
  self.assertEqual(self.client.get('/api/schemes/'+item['id']).json['model']['wells'][0]['ports'][0]['wall'],2)
 def test_reject_invalid_optional_node_fields(self):
  project=self.project()
  for key,value in [('height','3'),('rotationMode','other'),('kind','other'),('rotationEdge',42)]:
   model=copy.deepcopy(MODEL);model['version']=4;model['wells'][0][key]=value
   self.assertEqual(self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':model,'name':'Ошибка'}).status_code,400)
 def test_persistent_catalogue_and_independent_copies(self):
  p=self.project();s=self.scheme(p['id']);self.assertEqual(s['model']['name'],s['name'])
  other=self.project('Другой');self.assertEqual(self.client.get('/api/projects/'+other['id']).json['schemes'],[])
  duplicate=self.client.post('/api/projects/'+p['id']+'/copy',json={});self.assertEqual(duplicate.status_code,201)
  copied=self.client.get('/api/projects/'+duplicate.json['id']).json['schemes'][0]
  model=copy.deepcopy(s['model']);model['name']='Изменена';model['wells'][0]['x']=999
  r=self.client.put('/api/schemes/'+s['id'],json={'model':model,'revision':1});self.assertEqual(r.status_code,200);self.assertEqual(r.json['revision'],2)
  self.assertNotEqual(self.client.get('/api/schemes/'+copied['id']).json['model']['wells'][0]['x'],999)
  self.assertEqual(create_app(self.path).test_client().get('/api/schemes/'+s['id']).json['model'],model)
  self.assertEqual(self.client.patch('/api/projects/'+p['id'],json={'name':'Новый заголовок'}).status_code,200)
 def test_conflict_does_not_overwrite_and_keeps_previous_revision(self):
  s=self.scheme(self.project()['id']);m=copy.deepcopy(s['model']);m['name']='Первое изменение'
  self.assertEqual(self.client.put('/api/schemes/'+s['id'],json={'model':m,'revision':1}).status_code,200)
  m['name']='Устаревший клиент'
  self.assertEqual(self.client.put('/api/schemes/'+s['id'],json={'model':m,'revision':1}).status_code,409)
  self.assertEqual(self.client.get('/api/schemes/'+s['id']).json['name'],'Первое изменение')
  with closing(sqlite3.connect(self.path)) as db:self.assertEqual(db.execute('SELECT count(*) FROM scheme_versions').fetchone()[0],1)
 def test_idempotent_import_and_scheme_copy(self):
  data={'model':MODEL,'project_name':'Импорт','source_key':'test-hash'}
  a=self.client.post('/api/import',json=data);b=self.client.post('/api/import',json=data)
  self.assertEqual(a.status_code,201);self.assertEqual(b.status_code,200);self.assertEqual(a.json['id'],b.json['id']);self.assertEqual(len(self.client.get('/api/projects').json['projects']),1)
  c=self.client.post('/api/schemes/'+a.json['id']+'/copy',json={});self.assertEqual(c.status_code,201);self.assertNotEqual(c.json['model']['id'],a.json['model']['id'])
 def test_legacy_hash_import_works_without_browser_crypto(self):
  raw=json.dumps(MODEL,ensure_ascii=False,separators=(',',':'))
  data={'model':MODEL,'project_name':'Кулько','source_key':'legacy-model','source_json':raw}
  a=self.client.post('/api/import',json=data);b=self.client.post('/api/import',json=data)
  self.assertEqual(a.status_code,201);self.assertEqual(a.json['id'],b.json['id'])
  data['source_json']='{}';self.assertEqual(self.client.post('/api/import',json=data).status_code,400)
 def test_bad_payloads_leave_database_unchanged(self):
  for body in [None,[],3,'text']:
   self.assertEqual(self.client.post('/api/projects',data=json.dumps(body),content_type='application/json').status_code,400)
  for value in [None,42,[],{'version':3,'name':'Bad','wells':[3],'edges':[],'soils':[]}]:
   self.assertEqual(self.client.post('/api/import',json={'model':value,'source_key':'bad'}).status_code,400)
  self.assertEqual(self.client.get('/api/projects').json['projects'],[])
  self.assertEqual(self.client.post('/api/projects',json={'name':'Other'},headers={'Origin':'https://evil.example'}).status_code,403)
  self.assertEqual(self.client.get('/api/schemes/absent').status_code,404)
 def test_reused_ports_and_malformed_endpoints_rejected_atomically(self):
  model=copy.deepcopy(MODEL);e=copy.deepcopy(model['edges'][0]);e['id']='other-edge'
  for collection in ['sections','waypoints']:
   for i,v in enumerate(e[collection]):v['id']='other-'+collection+str(i)
  model['edges'].append(e)
  r=self.client.post('/api/import',json={'model':model,'source_key':'duplicate-port'})
  self.assertEqual(r.status_code,400);self.assertIn('подключение',r.json['error'])
  for value in [[],None,3]:
   bad=copy.deepcopy(MODEL);bad['edges'][0]['from']=value
   self.assertEqual(self.client.post('/api/import',json={'model':bad,'source_key':'bad-endpoint'}).status_code,400)
  self.assertEqual(self.client.get('/api/projects').json['projects'],[])
 def test_online_backup_contains_committed_model(self):
  s=self.scheme(self.project()['id']);target=str(Path(self.tmp.name)/'backup.sqlite3')
  with closing(sqlite3.connect(self.path)) as origin,closing(sqlite3.connect(target)) as dest:origin.backup(dest)
  self.assertEqual(create_app(target).test_client().get('/api/schemes/'+s['id']).json['model'],s['model'])
 def test_backfill_and_working_chamber_roundtrip(self):
  model=copy.deepcopy(MODEL);model['version']=4
  model['wells'][0].update(heightMode='total',height=4,workingHeightOverride=2.2,backfillSource='imported',backfillMaterial='Песок')
  model['edges'][0].update(backfillSource='imported',backfillMaterial='ПГС')
  model['edges'][0]['sections'][0]['aroundMaterial']='Песок'
  project=self.project();r=self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':model,'name':'Засыпка'})
  self.assertEqual(r.status_code,201,r.json)
  saved=self.client.get('/api/schemes/'+r.json['id']).json['model']
  self.assertEqual(saved['wells'][0]['workingHeightOverride'],2.2)
  self.assertEqual(saved['edges'][0]['backfillMaterial'],'ПГС')
  for key,value in [('backfillSource','bad'),('backfillMaterial',' '),('workingHeightOverride',0)]:
   bad=copy.deepcopy(model);bad['wells'][0][key]=value
   self.assertEqual(self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':bad,'name':'Ошибка'}).status_code,400)
if __name__=='__main__':unittest.main()


