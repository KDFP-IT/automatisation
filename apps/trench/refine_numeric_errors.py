from pathlib import Path
f=Path('dist/issue-guidance.js');s=f.read_text(encoding='utf-8').replace("'Допустимый низ трубы: '","'При текущем уклоне допустимый низ: '")
s=s.replace("const labels={wall:", "const labels={x:'Координата X',y:'Координата Y',ground:'Отметка земли',wall:")
s=s.replace("positive.has(k)?w[k]<=0:w[k]<0", "positive.has(k)?w[k]<=0:!['x','y','ground'].includes(k)&&w[k]<0")
f.write_text(s,encoding='utf-8')
f=Path('dist/validation-ui.js');s=f.read_text(encoding='utf-8');needle="  if(found.length){const error="
idx=s.index(needle);end=s.index('\n }\n}',idx)
s=s[:end]+'''\n  if(!found.length&&node.type==='number'&&!node.readOnly&&!node.dataset.optional){const cmd=node.dataset.command,value=node.value===''?NaN:Number(node.value),positive=['well-height','well-working-height','pipe-length'].includes(cmd),nonnegative=cmd==='well-neck-height';if(!Number.isFinite(value)||positive&&value<=0||nonnegative&&value<0){node.setAttribute('aria-invalid','true');const label=node.closest('label');if(label){const note=label.ownerDocument.createElement('small');note.className='field-issue';note.textContent=positive?'Введите число больше нуля.':nonnegative?'Введите ноль или положительное число.':'Введите числовое значение.';label.append(note)}}}
'''+s[end:];f.write_text(s,encoding='utf-8')
