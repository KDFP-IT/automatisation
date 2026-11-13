from pathlib import Path
p=Path('dist/network-linked.js');s=p.read_text(encoding='utf-8').replace('cells(j,report.valid&&!j.errors.length)', 'cells(j,!j.errors.length&&Number.isFinite(j.excavation))');p.write_text(s,encoding='utf-8')
p=Path('tests/network.test.js');s=p.read_text(encoding='utf-8').replace('overlapping well pits and crossing trench axes are explicitly blocked','overlapping well pits and actual pipe collisions remain blocked');p.write_text(s,encoding='utf-8')
p=Path('tests/plain-errors.test.js');s=p.read_text(encoding='utf-8').replace('one trench overlap gives one clear problem and a visible location on plan','calculated overlap is a shared quantity and has a visible location on plan');p.write_text(s,encoding='utf-8')
