import urllib.request,json
from pathlib import Path
m=json.load(urllib.request.urlopen('http://localhost:8086/api/schemes/6ef1e581-7943-4b21-b246-1c2b30de54a5'))['model'];Path('diagnostics-current.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8');print('Read-only snapshot saved')
