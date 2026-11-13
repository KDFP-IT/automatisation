from pathlib import Path
import json
p=json.loads(Path('review-current.json').read_text(encoding='utf-8'));p['name']='Тест переноса К1 — копия рабочей геометрии'
Path('group-fixture.json').write_text(json.dumps(p,ensure_ascii=False),encoding='utf-8')
for source,target in [('create_group_fixture.py','create_round_fixture.py'),('cleanup_group_fixture.py','cleanup_round_fixture.py')]:
 Path(target).write_text(Path(source).read_text(encoding='utf-8-sig').replace('6.1','6.3'),encoding='utf-8')
