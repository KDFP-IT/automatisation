from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8').replace(";if(command==='well-working-height'&&well())setWellWorkingHeight(well(),val);if(command==='floor'&&well())node.value", ";if(command==='floor'&&well())node.value")
s=s.replace("if(command==='well-height'&&well()){setWellHeight(well(),val)}", "if(command==='well-height'&&well()){setWellHeight(well(),val)}if(command==='well-working-height'&&well())setWellWorkingHeight(well(),val);")
f.write_text(s,encoding='utf-8')
