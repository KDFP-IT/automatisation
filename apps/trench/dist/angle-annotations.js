// Engineering angles are computed in real coordinates, independently of drawing scales/camera.
import {atStation,sectionAt,crossSection,degrees} from './network-model.js';
const fmt=(v,d=2)=>Number.isFinite(v)?v.toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
export function angleMetrics(e,res,ratio=.5){
 if(!(res.length>0))return null;const t=Math.max(0,Math.min(1,Number.isFinite(ratio)?ratio:.5)),s=t*res.length,section=sectionAt(e,res,s),c=crossSection(e,res,section,s),beta=Math.atan(-c.grade)*180/Math.PI;
 if(!Number.isFinite(beta))return null;
 return {s,section,c,beta,perMille:-c.grade*1000,left:degrees(c.left),right:degrees(c.right),direction:Math.abs(c.grade)<1e-10?'горизонтально':c.grade<0?'падение':'подъём'};
}
export function sectionAngleMarks(metrics,P){
 if(!metrics||metrics.section.method!=='trench')return '';const {c,left,right}=metrics;if(![left,right].every(Number.isFinite))return '';
 return [-1,1].map(sign=>{const alpha=sign<0?left:right,v=P(sign*c.width/2,c.bottom),top=P(sign*(c.width/2+(sign<0?c.left:c.right)*c.depth),c.ground),r=Math.max(12,Math.min(35,Math.hypot(top[0]-v[0],top[1]-v[1])*.22)),a=alpha*Math.PI/180,start=[v[0]+sign*r,v[1]],end=[v[0]+sign*r*Math.cos(a),v[1]-r*Math.sin(a)];return `<g class="angle-mark" data-slope-angle="${alpha}" pointer-events="none"><path d="M${v[0]},${v[1]}h${sign*(r+14)}" stroke="#a86939" stroke-dasharray="4 3" fill="none"/><path d="M${start}A${r},${r} 0 0 ${sign<0?1:0} ${end}" stroke="#d7692c" stroke-width="2" fill="none"/><text x="${v[0]+sign*(r+9)}" y="${v[1]-12}" text-anchor="${sign<0?'end':'start'}" class="angle-label">α${sign<0?'л':'п'} ${fmt(alpha,1)}°</text></g>`}).join('');
}
