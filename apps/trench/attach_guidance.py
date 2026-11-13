from pathlib import Path
f=Path('dist/network-model.js');s=f.read_text(encoding='utf-8');s="import {enrichIssues} from './issue-guidance.js';\n"+s;s=s.replace(" return {wells,edges,joints,jointRegions,numerical,preview:", " enrichIssues(p,issues,{wellGeometry,resolveEdge,crossSection});\n return {wells,edges,joints,jointRegions,numerical,preview:");f.write_text(s,encoding='utf-8')
