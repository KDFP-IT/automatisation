from pathlib import Path
f=Path('dist/wall-connections.js');s=f.read_text(encoding='utf-8').replace("points=new Map(p.wells.map(w=>[w.id,{x:w.x,y:w.y}]));", "points=new Map(p.wells.map(w=>{const old=!pinned.has(w.id)&&reached.has(w.id)?before.wells.find(v=>v.id===w.id):w;return [w.id,{x:old.x,y:old.y}]}));")
f.write_text(s,encoding='utf-8')
