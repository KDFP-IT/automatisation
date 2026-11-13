from pathlib import Path
f=Path('dist/network-checks.js');s=f.read_text(encoding='utf-8')
old="for(const e of self?[a.e]:[a.e,b.e])add(self?'pipe-self-clash':'pipe-clash','error','edge',e.id,message,[edgePath(e)+'.waypoints',edgePath(e)+'.diameter',edgePath(e)+'.sections'],'geometry',self?[]:[e===a.e?b.e.id:a.e.id]);"
new="""for(const e of self?[a.e]:[a.e,b.e]){add(self?'pipe-self-clash':'pipe-clash','error','edge',e.id,message,[edgePath(e)+'.waypoints',edgePath(e)+'.diameter',edgePath(e)+'.sections'],'geometry',self?[]:[e===a.e?b.e.id:a.e.id]);Object.assign(issues.at(-1),{location:midpoint,clash:{distance:hit.distance,required:a.radius+b.radius,overlap:a.radius+b.radius-hit.distance,edges:[{id:a.e.id,station:a.lo+(a.hi-a.lo)*hit.s},{id:b.e.id,station:b.lo+(b.hi-b.lo)*hit.t}],points:[hit.p,hit.q]}})}"""
assert old in s;s=s.replace(old,new)
old="add('port-openings','error','well',w.id,message,[wellPath(w)+'.ports',wellPath(w)+'.diameter',wellPath(w)+'.width',wellPath(w)+'.length']);for(const e of [a.e,b.e])add('port-openings','error','edge',e.id,message,[edgePath(e)+'.diameter',edgePath(e)+'.waypoints',wellPath(w)+'.ports'],'geometry',[w.id]);"
new="""const details={well:w.id,distance:Math.hypot(...sub(a.point,b.point)),required:a.radius+b.radius,edges:[a.e.id,b.e.id]};add('port-openings','error','well',w.id,message,[wellPath(w)+'.ports',wellPath(w)+'.diameter',wellPath(w)+'.width',wellPath(w)+'.length']);Object.assign(issues.at(-1),{location:mix(a.point,b.point,.5),opening:details});for(const e of [a.e,b.e]){add('port-openings','error','edge',e.id,message,[edgePath(e)+'.diameter',edgePath(e)+'.waypoints',wellPath(w)+'.ports'],'geometry',[w.id]);Object.assign(issues.at(-1),{location:mix(a.point,b.point,.5),opening:details})}"""
assert old in s;s=s.replace(old,new)
f.write_text(s,encoding='utf-8')

