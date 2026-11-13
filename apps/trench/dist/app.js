import {defaults,calculate} from './model.js';
const $=id=>document.getElementById(id),f=(n,d=2)=>n.toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d});
let view='3d',last=null;
try{const saved=JSON.parse(localStorage.getItem('trench-v1'));if(saved&&typeof saved==='object')for(const k of Object.keys(defaults)){if(k==='mode'){if(['slope','width'].includes(saved[k]))$(k).value=saved[k]}else if(typeof saved[k]==='number'&&Number.isFinite(saved[k]))$(k).value=saved[k]}}catch{}
function read(){return Object.fromEntries(Object.keys(defaults).map(k=>[k,k==='mode'?$(k).value:$(k).value.trim()===''?NaN:Number($(k).value)]))}
function update(){
 const p=read(),r=calculate(p);last={p,r};
 $('slope-field').hidden=p.mode!=='slope';$('top-field').hidden=p.mode!=='width';
 $('top-value').textContent=Number.isFinite(r.top)?f(r.top)+' м':'—';
 const valid=!r.errors.length;
 $('errors').hidden=valid;$('errors').textContent=r.errors.join(' ');
 for(const k of Object.keys(defaults))if(k!=='mode')$(k).setAttribute('aria-invalid',String(!Number.isFinite(p[k])));
 for(const [id,key]of Object.entries({excavation:'excavation',backfill:'backfill','backfill-detail':'backfill','pipe-result':'pipe','bed-result':'bed',surplus:'displaced'}))$(id).textContent=valid?f(r[key])+(id.includes('result')||id.includes('detail')||id==='surplus'?' м³':''):'—';
 $('area').textContent=valid?'Сечение '+f(r.area)+' м²':'Сечение —';
 $('balance-bar').innerHTML=valid?['backfill','pipe','bed'].map((key,i)=>`<span class="${['soil','pipe','bed'][i]}" style="width:${100*r[key]/r.excavation}%" title="${f(r[key])} м³"></span>`).join(''):'';
 if(valid){draw(p,r);try{localStorage.setItem('trench-v1',JSON.stringify(p))}catch{}}
 else $('scene').innerHTML='<text x="450" y="210" text-anchor="middle">Скорректируйте параметры</text><text x="450" y="237" text-anchor="middle" style="font-size:11px;fill:#9aa798">Схема появится для допустимых размеров</text>';
}
function draw(p,r){
 const svg=$('scene'),in3d=view==='3d',a=Number($('rotation').value),B=r.top,b=p.bottom,h=p.depth,t=p.bedding,d=r.d;
 // The longitudinal direction is shortened to keep cross-section details readable.
 const zlen=in3d?Math.max(B,h)*1.15:0;
 const raw=(x,y,z=0)=>[x+z*(.72+a),-y-z*(.33-a*.18)];
 const corners=[raw(-B/2,h,0),raw(B/2,h,0),raw(-B/2,h,zlen),raw(B/2,h,zlen),raw(-b/2,0,0),raw(b/2,0,0)];
 const xs=corners.map(c=>c[0]),ys=corners.map(c=>c[1]);
 const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
 const scale=Math.min(620/(xmax-xmin),285/(ymax-ymin));
 const P=(x,y,z=0)=>{const v=raw(x,y,z);return [450+(v[0]-(xmin+xmax)/2)*scale,216+(v[1]-(ymin+ymax)/2)*scale]};
 const fmt=v=>v.map(n=>n.toFixed(2)).join(',');
 const poly=(points,fill,stroke='#77917b',extra='')=>`<polygon points="${points.map(fmt).join(' ')}" fill="${fill}" stroke="${stroke}" stroke-width="1.2" stroke-linejoin="round" ${extra}/>`;
 const line=(v,w,color='#9aa896',extra='')=>`<line x1="${v[0]}" y1="${v[1]}" x2="${w[0]}" y2="${w[1]}" stroke="${color}" stroke-width="1" ${extra}/>`;
 const text=(v,str,extra='')=>`<text x="${v[0]}" y="${v[1]}" text-anchor="middle" ${extra}>${str}</text>`;
 const dim=(v,w,label,dx=0,dy=0)=>{let q=[v[0]+dx,v[1]+dy],s=[w[0]+dx,w[1]+dy];return line(v,q,'#c8d1c3')+line(w,s,'#c8d1c3')+line(q,s,'#a8b69e','marker-start="url(#arrow)" marker-end="url(#arrow)"')+text([(q[0]+s[0])/2,(q[1]+s[1])/2-8],label,'style="font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round"')};
 const bl=P(-b/2,0),br=P(b/2,0),tl=P(-B/2,h),tr=P(B/2,h),BL=P(-b/2,0,zlen),BR=P(b/2,0,zlen),TL=P(-B/2,h,zlen),TR=P(B/2,h,zlen);
 let out=`<defs><pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.75" fill="#d6dfd0"/></pattern><pattern id="sand" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 9L9 0" stroke="#c9b574" stroke-width="0.6"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 5L0 1L0 9Z" fill="#a8b69e"/></marker></defs><rect width="900" height="440" fill="url(#grid)" opacity=".55"/>`;
 if(in3d){out+=poly([BL,BR,TR,TL],'#e2eadb88','#b5c3ac','stroke-dasharray="4 4"');out+=poly([bl,br,BR,BL],'#c9d5ba90');out+=poly([bl,BL,TL,tl],'#b7c9a675');out+=poly([br,BR,TR,tr],'#d5dfc680');}
 else out+=poly([bl,br,tr,tl],'#e7eddf90');
 if(t>0){const w=b/2+r.m*t,v=[P(-b/2,0),P(b/2,0),P(w,t),P(-w,t)];if(in3d)out+=poly([P(-w,t),P(w,t),P(w,t,zlen),P(-w,t,zlen)],'#e0d2a5','#bdaa79');out+=poly(v,'#e8d9ac','#bdaa79')+poly(v,'url(#sand)','#bdaa79');}
 const rad=d/2,cy=t+rad;
 const circle=(cx,z,rr=rad)=>Array.from({length:65},(_,i)=>{const th=2*Math.PI*i/64;return P(cx+rr*Math.cos(th),cy+rr*Math.sin(th),z)});
 for(let j=p.count-1;j>=0;j--){let cx=(j-(p.count-1)/2)*(d+p.gap),front=circle(cx,0),rear=circle(cx,zlen);
 if(in3d){out+=poly(rear,'#ca9464','#a9754e');for(let i=0;i<64;i++){const shade=Math.round(151+40*Math.sin(2*Math.PI*i/64));out+=poly([front[i],rear[i],rear[i+1],front[i+1]],`rgb(${shade+47},${shade},${shade-45})`,'none');}}
 out+=poly(front,'#ce9363','#8f603d')+poly(circle(cx,0,rad*.76),'#5c6c5b','#9e6e47');
 if(d*scale>22)out+=poly(circle(cx,0,rad*.64),'#3e5145','none');
 }
 out+=line(bl,br,'#678366')+line(bl,tl,'#678366')+line(br,tr,'#678366')+line(tl,tr,'#a7b897','stroke-dasharray="5 5"');
 if(in3d)out+=line(tl,TL,'#78916e')+line(tr,TR,'#78916e');
 out+=dim(in3d?TL:tl,in3d?TR:tr,`B = ${f(B)} м`,0,-26);
 out+=dim(bl,br,`b = ${f(b)} м`,0,34);
 const rightX=Math.max(tr[0],br[0],TR[0])+30,midY=(tr[1]+br[1])/2;
 out+=line(tr,[rightX,tr[1]],'#c8d1c3')+line(br,[rightX,br[1]],'#c8d1c3')+line([rightX,tr[1]],[rightX,br[1]],'#a8b69e','marker-start="url(#arrow)" marker-end="url(#arrow)"')+text([rightX+17,midY],`H = ${f(h)} м`,`transform="rotate(-90 ${rightX+17} ${midY})" style="font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:4px"`);
 const first=-(p.count-1)*(d+p.gap)/2,pc=P(first,cy),target=[Math.max(90,pc[0]-100),Math.min(398,pc[1]+63)];
 out+=line(pc,[target[0]+25,target[1]-5],'#b1845c')+text(target,`Ø ${f(p.diameter,0)} мм`,'style="fill:#a06d43;font-size:12px;paint-order:stroke;stroke:#fff;stroke-width:4px"');
 if(in3d)out+=dim(br,BR,`L = ${f(p.length)} м`,40,30);
 svg.innerHTML=out;svg.setAttribute('aria-label',`${in3d?'Объёмная схема':'Поперечное сечение'}: ширина дна ${f(b)} м, ширина поверху ${f(B)} м, глубина ${f(h)} м, труб ${p.count}, диаметр ${p.diameter} мм.`);
}
function setView(next){view=next;for(const name of ['3d','2d']){$('view'+name).classList.toggle('active',name===view);$('view'+name).setAttribute('aria-pressed',String(name===view))}$('rotation-label').hidden=view==='2d';update()}
$('parameters').addEventListener('input',e=>{if(e.target.id==='mode'&&$('mode').value==='width'&&last&&Number.isFinite(last.r.top))$('top').value=last.r.top;update()});$('parameters').addEventListener('submit',e=>e.preventDefault());
$('view3d').onclick=()=>setView('3d');$('view2d').onclick=()=>setView('2d');$('rotation').oninput=update;
$('reset').onclick=()=>{for(const[k,v]of Object.entries(defaults))$(k).value=v;$('rotation').value=.12;update()};$('print').onclick=()=>window.print();update();
