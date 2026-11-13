from pathlib import Path
out=Path('../output');bundle=out/'kdfp-trench-network-v6.2.0-offline';bundle.mkdir(exist_ok=True)
for name in ['compose.yaml','DEPLOY.md','.env.example']:
 old=out/'kdfp-trench-network-v6.1.0-offline'/name
 (bundle/name).write_text(old.read_text(encoding='utf-8').replace('6.1.0','6.2.0'),encoding='utf-8')
f=Path('NETWORK.md');s=f.read_text(encoding='utf-8').replace('## 6.2.0 — стены и перенос группы','## 6.1.0 — стены и перенос группы');f.write_text(s,encoding='utf-8')
