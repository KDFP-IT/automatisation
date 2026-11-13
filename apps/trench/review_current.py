import urllib.request,json
from pathlib import Path
p=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/7c5a13a8-60da-4f92-acc1-4254ed919247'))
Path('review-current.json').write_text(json.dumps(p['model'],ensure_ascii=False),encoding='utf-8')
print('Read-only project snapshot saved for calculation review')
