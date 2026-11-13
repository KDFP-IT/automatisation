import json,urllib.request
from pathlib import Path
ids=json.loads(Path('group-test-ids.json').read_text());m=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/'+ids['scheme']))['model'];w=next(v for v in m['wells'] if v.get('kind')!='endpoint')
assert abs(w['height']-3)<1e-8 and abs(w['workingHeightOverride']-1.8)<1e-8 and w['base']==.25
neck=w['height']-w['workingHeightOverride']-w['base']-w['slab'];assert abs(neck-.75)<1e-8
assert w['pitSlope']==0
print('Saved UI result verified: editable neck, unchanged working chamber, plate thickness and pit slope')
