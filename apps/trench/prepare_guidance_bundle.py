from pathlib import Path
out=Path('../output');bundle=out/'kdfp-trench-network-v7.3.0-offline';bundle.mkdir(exist_ok=True)
for name in ['compose.yaml','.env.example']:
 old=out/'kdfp-trench-network-v7.2.0-offline'/name
 (bundle/name).write_text(old.read_text(encoding='utf-8').replace('7.2.0','7.3.0'),encoding='utf-8')
(bundle/'DEPLOY.md').write_bytes(Path('DEPLOY.md').read_bytes())
