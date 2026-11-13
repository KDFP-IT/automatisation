import json,urllib.request
from pathlib import Path
ids=json.loads(Path('group-test-ids.json').read_text());m=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/'+ids['scheme']))['model'];e=m['edges'][0];b=next(w for w in m['wells'] if w['id']==e['to']['well']);w=next(w for w in m['wells'] if w['id']==e['from']['well'])
assert abs(b['x']-w['x']-22)<1e-8
assert b['ports'][0]['invert']==118.2
assert e['sections'][0]['width']==1.2 and e['sections'][0]['topWidth']==7 and e['sections'][0]['slopeMode']=='top'
assert w['height']==4
print('UI edits persisted: length, end level, trench width and slope mode; well dimensions preserved')
