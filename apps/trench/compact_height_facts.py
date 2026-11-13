from pathlib import Path
f=Path('dist/issue-guidance.js');s=f.read_text(encoding='utf-8');s=s.replace("facts=['Колодец '+w.name+'.','Низ трубы '+n(port.invert)+' м; пол '+n(lo)+' м; низ верхней плиты '+n(g.bodyTop-w.slab)+' м.']", "facts=['Колодец '+w.name+': низ трубы '+n(port.invert)+' м.']")
s=s.replace("'При текущем уклоне допустимый низ: '", "'Допустимый низ при этом уклоне: '")
s=s.replace("'Если отметку менять нельзя, измените размеры колодца; проверьте обе границы рабочей части.'", "'Если отметку менять нельзя, измените размеры колодца. Пол: '+n(lo)+' м; низ верхней плиты: '+n(g.bodyTop-w.slab)+' м. Проверьте обе границы рабочей части.'")
f.write_text(s,encoding='utf-8')
