export const defaults = {length:100,bottom:0.8,depth:1.8,mode:'slope',slope:0.5,top:2.6,diameter:315,count:1,gap:0.2,bedding:0.1};
export function calculate(p){
 const errors=[];
 for(const k of ['length','bottom','depth','slope','top','diameter','count','gap','bedding']) if(!Number.isFinite(p[k])) errors.push('Заполните все числовые поля.');
 if(p.length<=0||p.bottom<=0||p.depth<=0||p.diameter<=0) errors.push('Длина, ширина дна, глубина и диаметр должны быть больше нуля.');
 if(p.slope<0||p.bedding<0||p.gap<0) errors.push('Откос, подсыпка и зазор не могут быть отрицательными.');
 if(!Number.isInteger(p.count)||p.count<1||p.count>20) errors.push('Количество труб — целое число от 1 до 20.');
 const top=p.mode==='slope'?p.bottom+2*p.slope*p.depth:p.top;
 if(top<p.bottom) errors.push('Ширина поверху должна быть не меньше ширины дна.');
 const d=p.diameter/1000,r=d/2,m=(top-p.bottom)/(2*p.depth),center=p.bedding+r;
 if(p.bedding+d>p.depth) errors.push('Труба с подсыпкой не помещается по глубине.');
 // A circle fits the sloped wall only if its centre is at least r away from the wall.
 const outerCenter=(p.count-1)*(d+p.gap)/2;
 if(outerCenter+r*Math.sqrt(1+m*m)>p.bottom/2+m*center+1e-9) errors.push('Трубы не помещаются между откосами. Увеличьте ширину или уменьшите диаметр / количество.');
 const area=(p.bottom+top)*p.depth/2,excavation=area*p.length;
 const pipe=Math.PI*r*r*p.length*p.count;
 const bed=(p.bottom*p.bedding+m*p.bedding*p.bedding)*p.length;
 const backfill=excavation-pipe-bed;
 return {top,m,d,area,excavation,pipe,bed,backfill,displaced:pipe+bed,cover:p.depth-p.bedding-d,errors:[...new Set(errors)]};
}
