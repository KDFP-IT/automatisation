from pathlib import Path
out=Path('../output');bundle=out/'kdfp-trench-network-v7.0.0-offline';bundle.mkdir(exist_ok=True)
for name in ['compose.yaml','.env.example']:
 old=out/'kdfp-trench-network-v6.3.0-offline'/name
 (bundle/name).write_text(old.read_text(encoding='utf-8').replace('6.3.0','7.0.0').replace('trench-projects-api:2.1.0','trench-projects-api:2.2.0'),encoding='utf-8')
(bundle/'DEPLOY.md').write_bytes(Path('DEPLOY.md').read_bytes())
