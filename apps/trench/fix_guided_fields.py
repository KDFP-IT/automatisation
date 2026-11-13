from pathlib import Path
f=Path('dist/validation-ui.js');s=f.read_text(encoding='utf-8').replace("const note=document.createElement('small');note.className='field-issue';note.textContent=found[0].guidance?.directions[0]||found[0].message;node.closest('label')?.append(note)", "const label=node.closest?.('label');if(label){const note=label.ownerDocument.createElement('small');note.className='field-issue';note.textContent=found[0].guidance?.directions[0]||found[0].message;label.append(note)}")
f.write_text(s,encoding='utf-8')
f=Path('tests/plain-errors.test.js');s=f.read_text(encoding='utf-8').replace("selector==='[data-validation-paths]'?[]:[node]", "['[data-validation-paths]','.field-issue'].includes(selector)?[]:[node]");f.write_text(s,encoding='utf-8')
f=Path('dist/issue-guidance.js');s=f.read_text(encoding='utf-8').replace("'geometry',{station:o.station})", "'geometry',{station:o.station,end:'from'})")
s=s.replace("keys=Object.keys(labels).filter(k=>!Number.isFinite(w[k])||positive.has(k)?!Number.isFinite(w[k])||w[k]<=0:w[k]<0)", "keys=Object.keys(labels).filter(k=>!Number.isFinite(w[k])||(positive.has(k)?w[k]<=0:w[k]<0))")
f.write_text(s,encoding='utf-8')
