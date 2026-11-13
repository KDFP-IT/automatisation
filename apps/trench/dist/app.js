import {defaults,calculate,stringFields} from './model.js';
const $=id=>document.getElementById(id),f=(n,d=2)=>n.toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d});
let view='3d',last=null;
try{
 const current=localStorage.getItem('trench-v3');
 let saved=JSON.parse(current||localStorage.getItem('trench-v2')||localStorage.getItem('trench-v1'));
 if(saved&&typeof saved==='object'){
  if(!current){
   const wasExample=saved.length===6.79&&saved.bottom===1.16&&saved.depth===2.45&&saved.depthEnd===2.66&&saved.objectType==='none';
   if(wasExample)saved={...defaults};
   else saved.objectType='pipe';
  }
  for(const k of Object.keys(defaults)){
   if(stringFields.includes(k)){if(typeof saved[k]==='string'&&Array.from($(k).options).some(o=>o.value===saved[k]))$(k).value=saved[k]}
   else if(typeof saved[k]==='number'&&Number.isFinite(saved[k]))$(k).value=saved[k];
  }
 }
}catch{}
function read(){return Object.fromEntries(Object.keys(defaults).map(k=>[k,stringFields.includes(k)?$(k).value:$(k).value.trim()===''?NaN:Number($(k).value)]))}
function update(){
 const p=read(),r=calculate(p);last={p,r};
 $('slope-field').hidden=p.mode!=='slope';$('top-field').hidden=p.mode!=='width';
 $('end-depth-field').hidden=p.depthMode!=='variable';$('viewend').hidden=p.depthMode!=='variable';
 $('pipe-fields').hidden=p.objectType!=='pipe';$('box-fields').hidden=p.objectType!=='box';
 const objectName=p.objectType==='pipe'?'Труба':p.objectType==='box'?'Конструкция':'Без конструкции';
 $('legend-object').textContent=objectName;$('object-result-label').textContent=p.objectType==='pipe'?'Вытеснение трубами':'Вытеснение конструкцией';
 $('top-value').textContent=Number.isFinite(r.top)?f(r.top)+' м':'—';
 const valid=!r.errors.length;
 $('errors').hidden=valid;$('errors').textContent=r.errors.join(' ');
 for(const k of Object.keys(defaults))if(!stringFields.includes(k))$(k).setAttribute('aria-invalid',String(!Number.isFinite(p[k])));
 for(const [id,key]of Object.entries({excavation:'excavation',backfill:'backfill','backfill-detail':'backfill','pipe-result':'occupied','bed-result':'fill',surplus:'displaced'}))$(id).textContent=valid?f(r[key],3)+(id.includes('result')||id.includes('detail')||id==='surplus'?' м³':''):'—';
 $('area').textContent=valid?'Среднее сечение '+f(r.area,3)+' м²':'Сечение —';
 $('end-values').textContent=valid?`F₁ = ${f(r.areaStart,3)} м² · F₂ = ${f(r.areaEnd,3)} м² · B₁ = ${f(r.top)} м · B₂ = ${f(r.topEnd)} м · Покрытие над конструкцией: ${p.objectType==='none'?'—':f(r.cover)+' м'}`:'';
 $('balance-bar').innerHTML=valid?['backfill','occupied','fill'].map((key,i)=>`<span class="${['soil','pipe','bed'][i]}" style="width:${100*r[key]/r.excavation}%" title="${f(r[key],3)} м³"></span>`).join(''):'';
 if(valid){draw(p,r);try{localStorage.setItem('trench-v3',JSON.stringify(p))}catch{}}
 else $('scene').innerHTML='<text x="450" y="210" text-anchor="middle">Скорректируйте параметры</text><text x="450" y="237" text-anchor="middle" style="font-size:11px;fill:#9aa798">Схема появится для допустимых размеров</text>';
}
function draw(p,r){
 const svg=$('scene'),in3d=view==='3d',a=Number($('rotation').value),end=view==='end',B=end?r.topEnd:r.top,b=p.bottom,h=end?r.h2:p.depth,t=p.bedding,d=r.d,farB=in3d?r.topEnd:B,farH=in3d?r.h2:h;
 // The longitudinal direction is shortened to keep cross-section details readable.
 const zlen=in3d?Math.max(B,h,farB,farH)*1.15:0;
 const raw=(x,y,z=0)=>[x+z*(.72+a),-y-z*(.33-a*.18)];
 const corners=[raw(-B/2,h,0),raw(B/2,h,0),raw(-farB/2,farH,zlen),raw(farB/2,farH,zlen),raw(-b/2,0,0),raw(b/2,0,0)];
 const xs=corners.map(c=>c[0]),ys=corners.map(c=>c[1]);
 const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
 const scale=Math.min(620/(xmax-xmin),285/(ymax-ymin));
 const P=(x,y,z=0)=>{const v=raw(x,y,z);return [450+(v[0]-(xmin+xmax)/2)*scale,216+(v[1]-(ymin+ymax)/2)*scale]};
 const fmt=v=>v.map(n=>n.toFixed(2)).join(',');
 const poly=(points,fill,stroke='#9aa5ad',extra='')=>`<polygon points="${points.map(fmt).join(' ')}" fill="${fill}" stroke="${stroke}" stroke-width="1.2" stroke-linejoin="round" ${extra}/>`;
 const line=(v,w,color='#9fa9b0',extra='')=>`<line x1="${v[0]}" y1="${v[1]}" x2="${w[0]}" y2="${w[1]}" stroke="${color}" stroke-width="1" ${extra}/>`;
 const text=(v,str,extra='')=>`<text x="${v[0]}" y="${v[1]}" text-anchor="middle" ${extra}>${str}</text>`;
 const dim=(v,w,label,dx=0,dy=0)=>{let q=[v[0]+dx,v[1]+dy],s=[w[0]+dx,w[1]+dy];return line(v,q,'#cbd0d4')+line(w,s,'#cbd0d4')+line(q,s,'#a1aab1','marker-start="url(#arrow)" marker-end="url(#arrow)"')+text([(q[0]+s[0])/2,(q[1]+s[1])/2-8],label,'style="font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round"')};
 const bl=P(-b/2,0),br=P(b/2,0),tl=P(-B/2,h),tr=P(B/2,h),BL=P(-b/2,0,zlen),BR=P(b/2,0,zlen),TL=P(-farB/2,farH,zlen),TR=P(farB/2,farH,zlen);
 let out=`<defs><pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.75" fill="#dce0e3"/></pattern><pattern id="sand" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 9L9 0" stroke="#c7b797" stroke-width="0.6"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 5L0 1L0 9Z" fill="#a1aab1"/></marker></defs><rect width="900" height="440" fill="url(#grid)" opacity=".55"/>`;
 if(in3d){out+=poly([BL,BR,TR,TL],'#e0e5e888','#aab4bc','stroke-dasharray="4 4"');out+=poly([bl,br,BR,BL],'#bdc8d090');out+=poly([bl,BL,TL,tl],'#b4c0ca75');out+=poly([br,BR,TR,tr],'#d3dbe080');}
 else out+=poly([bl,br,tr,tl],'#e5eaee90');
 if(t>0){const w=b/2+r.m*t,v=[P(-b/2,0),P(b/2,0),P(w,t),P(-w,t)];if(in3d)out+=poly([P(-w,t),P(w,t),P(w,t,zlen),P(-w,t,zlen)],'#e8d9bc','#c6b18a');out+=poly(v,'#e9d9bc','#c6b18a')+poly(v,'url(#sand)','#c6b18a');}
 const rad=d/2,cy=t+rad;
 const circle=(cx,z,rr=rad)=>Array.from({length:65},(_,i)=>{const th=2*Math.PI*i/64;return P(cx+rr*Math.cos(th),cy+rr*Math.sin(th),z)});
 for(let j=p.objectType==='pipe'?p.count-1:-1;j>=0;j--){let cx=(j-(p.count-1)/2)*(d+p.gap),front=circle(cx,0),rear=circle(cx,zlen);
 if(in3d){out+=poly(rear,'#fd7a3d','#cf5318');for(let i=0;i<64;i++){const shade=Math.round(110+24*Math.sin(2*Math.PI*i/64));out+=poly([front[i],rear[i],rear[i+1],front[i+1]],`rgb(${Math.min(255,shade+125)},${shade},${Math.max(20,shade-70)})`,'none');}}
 out+=poly(front,'#fd6017','#cb4d12')+poly(circle(cx,0,rad*.76),'#515b62','#b94b18');
 if(d*scale>22)out+=poly(circle(cx,0,rad*.64),'#30383e','none');
 }
 if(p.objectType==='box'){
 const w=p.boxWidth/2,yt=t+p.boxHeight;
 if(in3d)out+=poly([P(-w,yt),P(w,yt),P(w,yt,zlen),P(-w,yt,zlen)],'#f5a274','#cf6c38')+poly([P(w,t),P(w,t,zlen),P(w,yt,zlen),P(w,yt)],'#e9844f','#cf6c38');
 out+=poly([P(-w,t),P(w,t),P(w,yt),P(-w,yt)],'#ffb58f','#cf6c38');
 }
 out+=line(bl,br,'#8999a5')+line(bl,tl,'#8999a5')+line(br,tr,'#8999a5')+line(tl,tr,'#9ba8b1','stroke-dasharray="5 5"');
 if(in3d)out+=line(tl,TL,'#8999a5')+line(tr,TR,'#8999a5');
 out+=dim(in3d?TL:tl,in3d?TR:tr,`B${in3d||end?'₂':'₁'} = ${f(in3d?farB:B)} м`,0,-26);
 if(in3d&&p.depthMode==='variable')out+=dim(tl,tr,`B₁ = ${f(B)} м`,0,-20);
 out+=dim(bl,br,`b = ${f(b)} м`,0,34);
 const rightX=Math.max(tr[0],br[0],TR[0])+30,midY=(tr[1]+br[1])/2;
 out+=line(tr,[rightX,tr[1]],'#cbd0d4')+line(br,[rightX,br[1]],'#cbd0d4')+line([rightX,tr[1]],[rightX,br[1]],'#a1aab1','marker-start="url(#arrow)" marker-end="url(#arrow)"')+text([rightX+17,midY],`H${end?'₂':'₁'} = ${f(h)} м`,`transform="rotate(-90 ${rightX+17} ${midY})" style="font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:4px"`);
 if(in3d&&p.depthMode==='variable'){
 const leftX=Math.min(TL[0],BL[0])-30;
 out+=line(TL,[leftX,TL[1]],'#cbd0d4')+line(BL,[leftX,BL[1]],'#cbd0d4')+dim([leftX,BL[1]],[leftX,TL[1]],`H₂ = ${f(farH)} м`,-10,0);
 }
 const first=-(p.count-1)*(d+p.gap)/2,pc=P(first,cy),target=[Math.max(90,pc[0]-100),Math.min(398,pc[1]+63)];
 if(p.objectType==='pipe')out+=line(pc,[target[0]+25,target[1]-5],'#e77b43')+text(target,`Ø ${f(p.diameter,0)} мм`,'style="fill:#ca581e;font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:4px"');
 if(in3d)out+=dim(br,BR,`L = ${f(p.length)} м`,40,30);
 svg.innerHTML=out;svg.setAttribute('aria-label',`${in3d?'Объёмная схема':'Поперечное сечение'}: ширина дна ${f(b)} м, глубины ${f(p.depth)} и ${f(r.h2)} м, ${p.objectType==='pipe'?p.count+' труб, диаметр '+p.diameter+' мм':p.objectType==='box'?'прямоугольная конструкция':'без конструкции'}.`);
}
function setView(next){view=next;for(const name of ['3d','2d','end']){$('view'+name).classList.toggle('active',name===view);$('view'+name).setAttribute('aria-pressed',String(name===view))}$('rotation-label').hidden=view!=='3d';update()}
$('parameters').addEventListener('input',e=>{if(e.target.id==='mode'&&last){if($('mode').value==='width'&&Number.isFinite(last.r.top))$('top').value=last.r.top;if($('mode').value==='slope'&&Number.isFinite(last.r.m))$('slope').value=last.r.m}if(e.target.id==='depthMode'){if($('depthMode').value==='variable')$('depthEnd').value=$('depth').value;else if(view==='end'){setView('2d');return}}update()});$('parameters').addEventListener('submit',e=>e.preventDefault());
$('view3d').onclick=()=>setView('3d');$('view2d').onclick=()=>setView('2d');$('viewend').onclick=()=>setView('end');$('rotation').oninput=update;
$('reset').onclick=()=>{for(const[k,v]of Object.entries(defaults))$(k).value=v;$('rotation').value=.12;setView('3d')};$('print').onclick=()=>window.print();update();
