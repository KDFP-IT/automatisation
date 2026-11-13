from pathlib import Path
out=Path('../output');bundle=out/'kdfp-trench-network-v6.3.0-offline';bundle.mkdir(exist_ok=True)
for name in ['compose.yaml','DEPLOY.md','.env.example']:
 old=out/'kdfp-trench-network-v6.2.0-offline'/name
 (bundle/name).write_text(old.read_text(encoding='utf-8').replace('6.2.0','6.3.0'),encoding='utf-8')
