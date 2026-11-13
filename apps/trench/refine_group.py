from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8').replace("const toggle=ev.ctrlKey||ev.metaKey||ev.shiftKey||state.groupMode;","const toggle=ev.ctrlKey||ev.metaKey||ev.shiftKey||(state.groupMode&&!state.selection.includes(key));")
s=s.replace("state.scale='network';render();\n};","state.selection=[];state.scale='network';render();\n};")
f.write_text(s,encoding='utf-8')
for name in ['package.json','compose.yaml','package_network.py']:
 f=Path(name);f.write_text(f.read_text(encoding='utf-8').replace('6.0.0','6.1.0'),encoding='utf-8')
