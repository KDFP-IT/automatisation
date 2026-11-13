"""Package only the deployable source and an already-exported offline image."""
from pathlib import Path
import zipfile,hashlib,json,tarfile
root=Path(__file__).parent;out=root.parent/'output';bundle=out/'kdfp-trench-network-v7.3.0-offline';bundle.mkdir(exist_ok=True)
source=out/'kdfp-trench-network-v7.3.0-source.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for name in ['Dockerfile','Dockerfile.api','tests_backend.py','tests_lifecycle.py','compose.yaml','nginx.conf','.dockerignore','.env.example','package.json','README.md','NETWORK.md','DEPLOY.md']:
  z.write(root/name,name)
 for directory in ['dist','tests','api']:
  for f in (root/directory).rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(root).as_posix())
for name in ['NETWORK.md','README.md']:(bundle/name).write_bytes((root/name).read_bytes())
image=bundle/'trench-calculator-image.tar'
if not image.exists():raise SystemExit('Export the verified image before packaging offline release.')
digest=hashlib.sha256(image.read_bytes()).hexdigest();(bundle/'image.sha256').write_text(digest+'  trench-calculator-image.tar\n',encoding='ascii')
with tarfile.open(image) as t:
 manifest=json.load(t.extractfile('manifest.json'))
 tags={tag for m in manifest for tag in (m.get('RepoTags') or [])}
 assert {'trench-calculator:7.3.0','trench-projects-api:2.2.0'} <= tags,'Missing image tags'
offline=out/'kdfp-trench-network-v7.3.0-offline.zip'
with zipfile.ZipFile(offline,'w',zipfile.ZIP_DEFLATED) as z:
 for f in bundle.iterdir():
  if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.name)
for path in [source,offline]:
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 print(path, path.stat().st_size)
