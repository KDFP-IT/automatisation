import json,urllib.request
from pathlib import Path
ids=json.loads(Path('group-test-ids.json').read_text());model=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/'+ids['scheme']))['model'];old=json.loads(Path('review-current.json').read_text(encoding='utf-8'))
for w in model['wells']:
 prev=next(v for v in old['wells'] if v['id']==w['id'])
 if w.get('kind')!='endpoint' and w['name']!='К1': assert (w['x'],w['y'])==(prev['x'],prev['y']),w['name']
 assert [v['invert'] for v in w['ports']]==[v['invert'] for v in prev['ports']]
assert next(w for w in model['wells'] if w['name']=='К1')['x']!=next(w for w in old['wells'] if w['name']=='К1')['x']
print('UI saved: K1 moved; other wells and all elevations unchanged')
