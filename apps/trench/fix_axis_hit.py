from pathlib import Path
p=Path('dist/constructor.css');p.write_text(p.read_text(encoding='utf-8')+'\n.well-orientation{pointer-events:none}.well-orientation .rotation-handle{pointer-events:all}\n',encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace("else pathSet(path,val);if(path.endsWith('.shape')", "else {pathSet(path,val);if(path.endsWith('.rotationMode')&&val==='pipe')well().rotation=0}if(path.endsWith('.shape')");p.write_text(s,encoding='utf-8')
