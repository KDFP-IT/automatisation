// Labels refer to excavated geological strata, not replacement bedding/backfill.
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function sectionSoilLabels(p,e,c,ratio,P){
 let previous=0,html='',leaders=[];
 for(const layer of e.layers){
  const bottom=layer.start+(layer.end-layer.start)*ratio,lo=Math.max(c.bottom,c.ground-bottom),hi=Math.min(c.ground,c.ground-previous);previous=bottom;if(!(hi>lo))continue;
  const soil=p.soils.find(v=>v.id===layer.soil),name=soil?.name||'Грунт не определён',z=(lo+hi)/2,h=z-c.bottom,left=-c.width/2-c.left*h,right=c.width/2+c.right*h,a=P(left,z),b=P(right,z),q=P((left+right)/2,z),height=Math.abs(P(0,hi)[1]-P(0,lo)[1]),short=name.length>44?name.slice(0,43)+'…':name;
  const title=`<title>${esc(name)}</title>`,attrs=`data-soil-label="${esc(layer.soil)}" class="section-soil-label" pointer-events="none"`;
  if(height>=27&&Math.abs(b[0]-a[0])>short.length*7.4+20&&z>c.fillTop+.05)html+=`<text x="${q[0]}" y="${q[1]+5}" text-anchor="middle" ${attrs}>${title}${esc(short)}</text>`;
  else leaders.push({name,soil:layer.soil,at:b,y:q[1]});
 }
 const gap=22,low=90,high=337;let y=low-gap;
 leaders.forEach(l=>{l.labelY=Math.max(l.y,y+gap);y=l.labelY});if(y>high){const shift=y-high;for(const l of leaders)l.labelY-=shift}
 for(const l of leaders){const short=l.name.length>29?l.name.slice(0,28)+'…':l.name;html+=`<g data-soil-label="${esc(l.soil)}" pointer-events="none"><path d="M${l.at[0]},${l.at[1]} L635,${l.labelY} H650" fill="none" stroke="#758b99" stroke-width="1"/><text x="657" y="${l.labelY+5}" text-anchor="start" class="section-soil-label soil-callout"><title>${esc(l.name)}</title>${esc(short)}</text></g>`}
 return html;
}
