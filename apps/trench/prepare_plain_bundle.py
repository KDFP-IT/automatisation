from pathlib import Path
f=Path('dist/network.css');s=f.read_text(encoding='utf-8').replace('.inspector-block[open] summary:after','.inspector-block[open]>summary:after');f.write_text(s,encoding='utf-8')
out=Path('../output');bundle=out/'kdfp-trench-network-v7.1.0-offline';bundle.mkdir(exist_ok=True)
for name in ['compose.yaml','.env.example']:
 old=out/'kdfp-trench-network-v7.0.0-offline'/name
 (bundle/name).write_text(old.read_text(encoding='utf-8').replace('7.0.0','7.1.0'),encoding='utf-8')
(bundle/'DEPLOY.md').write_bytes(Path('DEPLOY.md').read_bytes())
