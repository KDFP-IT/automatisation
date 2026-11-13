import re
from pathlib import Path
for f in Path('dist').glob('*.css'):
 for rule in re.findall(r'[^{}]+\{[^{}]*\}',f.read_text(encoding='utf-8')):
  if 'summary' in rule and ('content:' in rule or 'open' in rule):print(f.name,rule[:400])
