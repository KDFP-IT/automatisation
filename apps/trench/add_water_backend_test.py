from pathlib import Path
f=Path('tests_backend.py');s=f.read_text(encoding='utf-8');idx=s.index("if __name__=='__main__'");s=s[:idx]+''' def test_backfill_and_working_chamber_roundtrip(self):
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
'''+s[idx:];f.write_text(s,encoding='utf-8')
