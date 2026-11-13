import urllib.request,json
from pathlib import Path
ids=json.loads(Path('group-test-ids.json').read_text());m=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/'+ids['scheme']))['model'];w=next(v for v in m['wells'] if v.get('kind')!='endpoint');e=m['edges'][0]
assert w['height']==4 and w['workingHeightOverride']==2.2
assert w['backfillSource']=='imported' and w['backfillMaterial']=='Песчано-гравийная смесь'
assert e['backfillSource']=='imported' and e['backfillMaterial']=='Песок средней крупности'
print('Saved UI settings verified: working height, total height, pipe and well backfill materials')
