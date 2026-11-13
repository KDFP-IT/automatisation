import {backfillSource,backfillName} from './backfill.js';
import {rectangleVertices} from './node-geometry.js';
import {clipPolygon} from './network-checks.js';
// Numerical union of vertical excavation columns. Wells keep their existing priority:
// all trench quantities inside a well pit are accounted for by that pit, not by a trench.
const EPS=1e-9;
const quantityKeys=['excavation','pipe','fill','bedding','around','protection','backfill','nativeBackfill','importedBackfill'];
const empty=p=>({...Object.fromEntries(quantityKeys.map(k=>[k,0])),soils:Object.fromEntries(p.soils.map(s=>[s.id,0])),errors:[]});
const inside=(z,interval)=>interval&&z>=interval[0]-EPS&&z<interval[1]-EPS;
export function integrateJointTrenches(p,members,geometry,{jointStep=.1,jointCrossSamples=128,step,crossSamples,preview=false}={}){
 const {resolveEdge,crossSection,wellGeometry,pitInterval}=geometry,parts=[],rows=Object.fromEntries(members.map(e=>[e.id,empty(p)])),joints=new Map(),conflicts=new Map(),backfillConflicts=new Map();
 const pits=p.wells.filter(w=>w.kind!=='endpoint').map(w=>{const g=wellGeometry(w,p);return {w,g,polygons:[rectangleVertices(w,g.topW,g.topL,g.rotation),rectangleVertices(w,g.width,g.length,g.rotation)]}});
 for(const e of [...members].sort((a,b)=>a.id.localeCompare(b.id))){const res=resolveEdge(p,e),bounds=[...new Set([0,res.length,...res.points.map(v=>v.s),...e.sections.flatMap(v=>[v.a*res.length,v.b*res.length])])].sort((a,b)=>a-b);
  for(let i=1;i<bounds.length;i++){const lo=bounds[i-1],hi=bounds[i],section=e.sections.find(v=>(lo+hi)/2/res.length>=v.a-EPS&&(lo+hi)/2/res.length<=v.b+EPS);if(section?.method!=='trench'||hi-lo<EPS)continue;
   const epsilon=Math.min(1e-8,(hi-lo)/1000),evaluate=s=>crossSection(e,res,section,Math.max(lo+epsilon,Math.min(hi-epsilon,s))),a=evaluate(lo),b=evaluate(hi),mid=evaluate((lo+hi)/2),dx=mid.dx,dy=mid.dy,start={x:a.x-dx*epsilon,y:a.y-dy*epsilon},length=hi-lo;
   const corners=[a,b].flatMap(c=>[-c.width/2-c.left*c.depth,c.width/2+c.right*c.depth].map(x=>[c.x-dy*x,c.y+dx*x]));
   const polygon=[corners[0],corners[1],corners[3],corners[2]],r=a.radius,end={x:start.x+dx*length,y:start.y+dy*length},pipePolygon=[[start.x-dy*r,start.y+dx*r],[start.x+dy*r,start.y-dx*r],[end.x+dy*r,end.y-dx*r],[end.x-dy*r,end.y+dx*r]];parts.push({e,res,section,lo,hi,length,dx,dy,start,evaluate,polygon,pipePolygon,radius:r,box:[Math.min(...corners.map(v=>v[0]))-1e-6,Math.max(...corners.map(v=>v[0]))+1e-6,Math.min(...corners.map(v=>v[1]))-1e-6,Math.max(...corners.map(v=>v[1]))+1e-6]});
  }
 }
 parts.forEach((v,i)=>v.rank=i);
 const inBox=(v,x,y)=>x>=v.box[0]&&x<=v.box[1]&&y>=v.box[2]&&y<=v.box[3];
 const column=(part,x,y)=>{if(!inBox(part,x,y))return null;const s=(x-part.start.x)*part.dx+(y-part.start.y)*part.dy;if(s<-EPS||s>part.length+EPS)return null;const c=part.evaluate(part.lo+Math.max(0,Math.min(part.length,s))),lat=-(x-c.x)*part.dy+(y-c.y)*part.dx,side=lat<-c.width/2?c.left:lat>c.width/2?c.right:null,offset=lat<-c.width/2?-lat-c.width/2:lat>c.width/2?lat-c.width/2:0;
  if(offset>0&&!(side>EPS))return null;const bottom=c.bottom+(offset?offset/side:0);if(c.ground-bottom<EPS)return null;
  const half=Math.abs(lat)<c.radius?Math.sqrt(Math.max(0,c.radius*c.radius-lat*lat))*Math.sqrt(1+c.grade*c.grade):0,pipe=half>0?[c.axis-half,c.axis+half]:null,bed=[c.bottom,c.bottom+part.section.bedding],around=part.section.around?[bed[1],c.axis+c.verticalR]:null,protection=part.section.around?[c.axis+c.verticalR,c.fillTop]:null;
  let previous=0;const soils=part.e.layers.map(layer=>{const depth=layer.start+(layer.end-layer.start)*c.s/part.res.length,value={soil:layer.soil,range:[c.ground-depth,c.ground-previous]};previous=depth;return value});
  return {part,range:[bottom,c.ground],pipe,bed,around,protection,soils};
 };
 const cells=(lo,hi,base,zones=[])=>{const cuts=[lo,hi,...zones.flatMap(v=>[Math.max(lo,v.lo),Math.min(hi,v.hi)])].filter(v=>v>=lo&&v<=hi).sort((a,b)=>a-b),result=[];for(let i=1;i<cuts.length;i++){const a=cuts[i-1],b=cuts[i];if(b-a<EPS)continue;const mid=(a+b)/2,h=zones.filter(v=>mid>=v.lo&&mid<=v.hi).reduce((n,v)=>Math.min(n,v.h),base),n=Math.max(1,Math.ceil((b-a)/h)),step=(b-a)/n;for(let k=0;k<n;k++)result.push({mid:a+(k+.5)*step,step})}return result};
 const clipRange=(range,offset,coefficient,lo,hi)=>{if(Math.abs(coefficient)<1e-10)return offset>=lo-EPS&&offset<=hi+EPS?range:null;const a=(lo-offset)/coefficient,b=(hi-offset)/coefficient,result=[Math.max(range[0],Math.min(a,b)),Math.min(range[1],Math.max(a,b))];return result[1]>result[0]+EPS?result:null};
 const slice=(polygon,origin,normal,range)=>{const area=polygon.reduce((n,a,i)=>{const b=polygon[(i+1)%polygon.length];return n+a[0]*b[1]-a[1]*b[0]},0),sign=area<0?-1:1;for(let i=0;i<polygon.length&&range;i++){const a=polygon[i],b=polygon[(i+1)%polygon.length],dx=b[0]-a[0],dy=b[1]-a[1];range=clipRange(range,sign*(dx*(origin[1]-a[1])-dy*(origin[0]-a[0])),sign*(dx*normal[1]-dy*normal[0]),0,Infinity)}return range};
 let samples=0;
 for(const source of parts){const candidates=parts.filter(v=>v.box[0]<=source.box[1]&&v.box[1]>=source.box[0]&&v.box[2]<=source.box[3]&&v.box[3]>=source.box[2]),h=Math.max(step??jointStep,source.res.length/1600),nx=Math.max(32,Math.min(1024,Math.round(crossSamples??jointCrossSamples))),feature=preview?4:Math.max(12,Math.round(nx/16)),zones=[];
  for(const v of candidates){const sine=Math.abs(source.dx*v.dy-source.dy*v.dx);if(v===source||sine<1e-8)continue;const clipped=clipPolygon(source.polygon,v.pipePolygon);if(clipped.length<3)continue;const positions=clipped.map(q=>(q[0]-source.start.x)*source.dx+(q[1]-source.start.y)*source.dy);zones.push({lo:Math.max(0,Math.min(...positions)),hi:Math.min(source.length,Math.max(...positions)),h:v.radius/feature/sine})}
  for(const pit of pits)for(const polygon of pit.polygons){const clipped=clipPolygon(source.polygon,polygon);if(clipped.length<3)continue;const positions=clipped.map(q=>(q[0]-source.start.x)*source.dx+(q[1]-source.start.y)*source.dy);zones.push({lo:Math.max(0,Math.min(...positions)),hi:Math.min(source.length,Math.max(...positions)),h})}for(const along of cells(0,source.length,h,zones)){const ds=along.step,c=source.evaluate(source.lo+along.mid),left=-c.width/2-c.left*c.depth,right=c.width/2+c.right*c.depth,xZones=[];
   for(const v of candidates){const footprintRange=slice(v.polygon,[c.x,c.y],[-source.dy,source.dx],[left,right]);if(footprintRange)xZones.push({lo:footprintRange[0],hi:footprintRange[1],h:(right-left)/nx});const ox=c.x-v.start.x,oy=c.y-v.start.y,normalX=-source.dy,normalY=source.dx,lateral=-ox*v.dy+oy*v.dx,coefficient=-normalX*v.dy+normalY*v.dx;let range=clipRange([left,right],lateral,coefficient,-v.radius,v.radius);if(range)range=clipRange(range,ox*v.dx+oy*v.dy,normalX*v.dx+normalY*v.dy,0,v.length);if(range)xZones.push({lo:range[0],hi:range[1],h:Math.abs(coefficient)>1e-8?v.radius/feature/Math.abs(coefficient):(right-left)/nx})}
   for(const pit of pits)for(const polygon of pit.polygons){const range=slice(polygon,[c.x,c.y],[-source.dy,source.dx],[left,right]);if(range)xZones.push({lo:range[0],hi:range[1],h:(right-left)/nx})}for(const across of cells(left,right,(right-left)/nx,xZones)){const dx=across.step,lat=across.mid,x=c.x-source.dy*lat,y=c.y+source.dx*lat,columns=candidates.map(v=>column(v,x,y)).filter(Boolean),own=columns.find(v=>v.part===source);if(!own)continue;samples++;
    const cuts=pits.map(({w,g})=>pitInterval(w,g,x,y)).filter(Boolean),breaks=[...own.range,...cuts.flat(),...columns.flatMap(v=>[...v.range,...(v.pipe||[]),...v.bed,...(v.around||[]),...(v.protection||[]),...v.soils.flatMap(s=>s.range)])].filter(z=>z>=own.range[0]-EPS&&z<=own.range[1]+EPS).sort((a,b)=>a-b);
    for(let k=1;k<breaks.length;k++){const low=breaks[k-1],high=breaks[k];if(high-low<EPS)continue;const z=(low+high)/2;if(cuts.some(v=>inside(z,v)))continue;const active=columns.filter(v=>inside(z,v.range));if(!active.length||active[0].part!==source)continue;
     const ids=[...new Set(active.map(v=>v.part.e.id))].sort(),key=ids.join('|');let target;if(ids.length>1){if(!joints.has(key))joints.set(key,{...empty(p),id:'joint-'+key,edgeIds:ids,names:ids.map(id=>members.find(e=>e.id===id).name),sampleLocation:[x,y]});target=joints.get(key)}else target=rows[ids[0]];
     const volume=(high-low)*ds*dx;target.excavation+=volume;
     const category=active.some(v=>inside(z,v.pipe))?'pipe':active.some(v=>inside(z,v.bed))?'bedding':active.some(v=>inside(z,v.around))?'around':active.some(v=>inside(z,v.protection))?'protection':'backfill';target[category]+=volume;
     if(category==='backfill'){const specs=[...new Set(active.map(v=>backfillSource(v.part.e)+':'+backfillName(v.part.e)))];target[backfillSource(active[0].part.e)==='imported'?'importedBackfill':'nativeBackfill']+=volume;if(specs.length>1&&!backfillConflicts.has(key))backfillConflicts.set(key,{edgeIds:ids,location:[x,y,z]})}

     const soilValues=active.map(v=>({id:v.soils.find(s=>inside(z,s.range))?.soil,edge:v.part.e.id})),soil=soilValues[0]?.id;
     if(soil!==undefined&&Object.hasOwn(target.soils,soil))target.soils[soil]+=volume;
     const soilIds=[...new Set(soilValues.map(v=>v.id))];if(soilIds.length>1){const conflictKey=ids.join('|')+':'+[...soilIds].sort().join('|');if(!conflicts.has(conflictKey))conflicts.set(conflictKey,{edgeIds:ids,soilIds,location:[x,y,z],volume:0});conflicts.get(conflictKey).volume+=volume}
    }
   }
  }
 }
 for(const v of [...Object.values(rows),...joints.values()]){v.fill=v.bedding+v.around+v.protection;v.backfill=v.excavation-v.pipe-v.fill;if(Math.abs(v.backfill)<1e-8)v.backfill=0}
 return {backfillConflicts:[...backfillConflicts.values()],edges:rows,joints:[...joints.values()].filter(v=>v.excavation>1e-7),conflicts:[...conflicts.values()].filter(v=>v.volume>1e-5),numerical:{method:'vertical-column-union',step:step??jointStep,crossSamples:crossSamples??jointCrossSamples,samples}};
}
