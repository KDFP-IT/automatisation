from pathlib import Path
f=Path('dist/validation-ui.js');s=f.read_text(encoding='utf-8').replace("<span>${esc(help)}</span>${limitDimensionsHTML", "<span>${esc(g?g.directions[0]:help)}</span>${limitDimensionsHTML")
s=s.replace("</button>`:'')}</div></article>`;", "</button>`:'')}</div>${g?.directions.length>1?`<details class=\"issue-alternatives\"><summary>Другие варианты</summary><p>${esc(g.directions.slice(1).join(' '))}</p></details>`:''}</article>`;")
f.write_text(s,encoding='utf-8')
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8').replace("else $('inspector').scrollTop=0;return;\n }", "else $('inspector').scrollTop=0;$('object-validation').scrollTop=0;return;\n }")
s=s.replace("state.zoom=1}catch{}renderCanvas();return}\n if(a==='issue')", "state.zoom=1}catch{}renderCanvas();$('object-validation').scrollTop=0;return}\n if(a==='issue')")
f.write_text(s,encoding='utf-8')
