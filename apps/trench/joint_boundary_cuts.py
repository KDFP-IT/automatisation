from pathlib import Path
p=Path('dist/joint-excavation.js');s=p.read_text(encoding='utf-8');pos=s.index(' let samples=0;');s=s[:pos]+''' const slice=(polygon,origin,normal,range)=>{const area=polygon.reduce((n,a,i)=>{const b=polygon[(i+1)%polygon.length];return n+a[0]*b[1]-a[1]*b[0]},0),sign=area<0?-1:1;for(let i=0;i<polygon.length&&range;i++){const a=polygon[i],b=polygon[(i+1)%polygon.length],dx=b[0]-a[0],dy=b[1]-a[1];range=clipRange(range,sign*(dx*(origin[1]-a[1])-dy*(origin[0]-a[0])),sign*(dx*normal[1]-dy*normal[0]),0,Infinity)}return range};
'''+s[pos:]
s=s.replace("for(const v of candidates){const ox=c.x-v.start.x", "for(const v of candidates){const footprintRange=slice(v.polygon,[c.x,c.y],[-source.dy,source.dx],[left,right]);if(footprintRange)xZones.push({lo:footprintRange[0],hi:footprintRange[1],h:(right-left)/nx});const ox=c.x-v.start.x")
p.write_text(s,encoding='utf-8')
