import copy,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from contextlib import closing
from tests_backend import MODEL
from api.app import create_app

class LifecycleTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.path=str(Path(self.tmp.name)/'db.sqlite3');self.client=create_app(self.path).test_client()
 def tearDown(self):self.tmp.cleanup()
 def project(self):return self.client.post('/api/projects',json={'name':'Проект'}).json
 def scheme(self,pid):return self.client.post('/api/projects/'+pid+'/schemes',json={'name':'Схема','model':MODEL}).json
 def meta(self,kind,id):
  with closing(sqlite3.connect(self.path)) as db:
   db.row_factory=sqlite3.Row;return dict(db.execute('SELECT * FROM '+('projects' if kind=='project' else 'schemes')+' WHERE id=?',(id,)).fetchone())
 def state(self,kind,id,action):
  r=self.client.post('/api/'+('projects' if kind=='project' else 'schemes')+'/'+id+'/state',json={'action':action,'revision':self.meta(kind,id)['revision']});self.assertEqual(r.status_code,200,r.json);return r.json
 def test_scheme_archive_restore_trash_preserves_model_and_prior_state(self):
  p=self.project();s=self.scheme(p['id']);original=copy.deepcopy(s['model'])
  self.state('scheme',s['id'],'archive')
  self.assertEqual(self.client.get('/api/projects/'+p['id']).json['schemes'],[])
  self.assertEqual(len(self.client.get('/api/projects/'+p['id']+'?view=archived').json['schemes']),1)
  self.assertEqual(self.client.get('/api/schemes/'+s['id']).status_code,409)
  self.state('scheme',s['id'],'trash');self.assertEqual(len(self.client.get('/api/projects/'+p['id']+'?view=trash').json['schemes']),1)
  restored=self.state('scheme',s['id'],'restore');self.assertTrue(restored['archived_at']);self.assertIsNone(restored['deleted_at'])
  self.state('scheme',s['id'],'unarchive');self.assertEqual(self.client.get('/api/schemes/'+s['id']).json['model'],original)
 def test_project_parent_state_is_atomic_and_does_not_revive_individually_trashed_schemes(self):
  p=self.project();a=self.scheme(p['id']);b=self.scheme(p['id']);self.state('scheme',b['id'],'trash')
  self.state('project',p['id'],'trash');self.assertEqual(self.client.get('/api/projects').json['projects'],[]);self.assertEqual(len(self.client.get('/api/projects?view=trash').json['projects']),1)
  self.assertEqual(self.client.get('/api/schemes/'+a['id']).status_code,409)
  self.assertEqual(self.client.post('/api/projects/'+p['id']+'/schemes',json={'name':'Новая','model':MODEL}).status_code,409)
  self.state('project',p['id'],'restore');self.assertEqual(len(self.client.get('/api/projects/'+p['id']).json['schemes']),1);self.assertEqual(len(self.client.get('/api/projects/'+p['id']+'?view=trash').json['schemes']),1)
 def test_stale_editors_and_stale_state_actions_cannot_overwrite_after_parent_restore(self):
  p=self.project();s=self.scheme(p['id']);old=self.meta('project',p['id'])
  self.state('project',p['id'],'archive')
  stale=self.client.post('/api/projects/'+p['id']+'/state',json={'action':'trash','revision':old['revision']});self.assertEqual(stale.status_code,409)
  self.assertEqual(self.client.put('/api/schemes/'+s['id'],json={'revision':s['revision'],'model':s['model']}).status_code,409)
  self.state('project',p['id'],'unarchive')
  self.assertEqual(self.client.put('/api/schemes/'+s['id'],json={'revision':s['revision'],'model':s['model']}).status_code,409)
  self.assertEqual(self.client.get('/api/schemes/'+s['id']).json['model'],s['model'])
 def test_permanent_delete_requires_trash_exact_name_revision_and_cleans_dependencies(self):
  imported=self.client.post('/api/import',json={'source_key':'lifecycle-import','model':MODEL}).json;pid=imported['project_id'];sid=imported['id']
  self.client.put('/api/schemes/'+sid,json={'revision':1,'model':imported['model']})
  def purge(name,revision):return self.client.delete('/api/projects/'+pid,json={'confirm_name':name,'revision':revision})
  self.assertEqual(purge(self.meta('project',pid)['name'],self.meta('project',pid)['revision']).status_code,409)
  row=self.state('project',pid,'trash');self.assertEqual(purge('Неверное имя',row['revision']).status_code,400);self.assertEqual(purge(row['name'],row['revision']-1).status_code,409)
  self.assertEqual(purge(row['name'],row['revision']).status_code,200)
  with closing(sqlite3.connect(self.path)) as db:
   for table in ['projects','schemes','scheme_versions','imports']:self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0,table)
 def test_scheme_purge_leaves_other_schemes_and_project_intact(self):
  p=self.project();a=self.scheme(p['id']);b=self.scheme(p['id']);row=self.state('scheme',a['id'],'trash')
  self.assertEqual(self.client.delete('/api/schemes/'+a['id'],json={'revision':row['revision'],'confirm_name':row['name']}).status_code,200)
  self.assertEqual(self.client.get('/api/schemes/'+b['id']).status_code,200);self.assertEqual(len(self.client.get('/api/projects').json['projects']),1)
 def test_copy_ignores_trashed_schemes_and_preserves_archived_schemes(self):
  p=self.project();a=self.scheme(p['id']);b=self.scheme(p['id']);self.state('scheme',a['id'],'archive');self.state('scheme',b['id'],'trash')
  copied=self.client.post('/api/projects/'+p['id']+'/copy',json={});self.assertEqual(copied.status_code,201)
  self.assertEqual(self.client.get('/api/projects/'+copied.json['id']).json['schemes'],[]);self.assertEqual(len(self.client.get('/api/projects/'+copied.json['id']+'?view=archived').json['schemes']),1)
 def test_existing_v1_database_migrates_without_touching_model_or_ids_and_migration_is_repeatable(self):
  oldpath=str(Path(self.tmp.name)/'old.sqlite3')
  with closing(sqlite3.connect(oldpath)) as db:
   db.executescript('CREATE TABLE projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE schemes(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),name TEXT NOT NULL,model_json TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);PRAGMA user_version=1;')
   db.execute('INSERT INTO projects VALUES(?,?,?,?)',('old-project','Старый','old','old'));db.execute('INSERT INTO schemes VALUES(?,?,?,?,?,?,?)',('old-scheme','old-project',MODEL['name'],json.dumps(MODEL),8,'old','old'));db.commit()
  for _ in range(2):
   client=create_app(oldpath).test_client();r=client.get('/api/schemes/old-scheme');self.assertEqual(r.status_code,200);self.assertEqual(r.json['model'],MODEL);self.assertEqual(r.json['revision'],8)
  with closing(sqlite3.connect(oldpath)) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2)
 def test_invalid_view_action_and_lifecycle_on_deleted_object_are_rejected(self):
  p=self.project();self.assertEqual(self.client.get('/api/projects?view=whatever').status_code,400)
  self.assertEqual(self.client.post('/api/projects/'+p['id']+'/state',json={'action':'unknown','revision':p['revision']}).status_code,400)
  self.state('project',p['id'],'trash');r=self.client.post('/api/projects/'+p['id']+'/state',json={'action':'archive','revision':self.meta('project',p['id'])['revision']});self.assertEqual(r.status_code,409)
if __name__=='__main__':unittest.main()
