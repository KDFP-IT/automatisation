import re
from pathlib import Path
for f in Path('dist').glob('*.css'):
 for rule in re.findall(r'[^{}]+\{[^{}]*\}',f.read_text(encoding='utf-8')):
  if 'svg' in rule and any(v in rule for v in ['min-height','height:250','height:260','height:240']):print(f.name,rule[:450])
