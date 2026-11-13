export const defaults = {length:100,bottom:0.8,depth:1.8,depthEnd:1.8,depthMode:'constant',sectionRounding:'full',mode:'slope',slope:0.5,top:2.6,diameter:315,count:1,gap:0.2,bedding:0.1,extraFill:0,objectType:'pipe',boxWidth:0.4,boxHeight:0.4};
export const stringFields=['mode','depthMode','objectType','sectionRounding'];
export function calculate(p){
 p={...defaults,...p};
 const errors=[];
 const fields=['length','bottom','depth','bedding','extraFill',p.mode==='slope'?'slope':'top'];
 if(p.depthMode==='variable')fields.push('depthEnd');
 if(p.objectType==='pipe')fields.push('diameter','count','gap');
 if(p.objectType==='box')fields.push('boxWidth','boxHeight');
 for(const k of fields) if(!Number.isFinite(p[k])) errors.push('Заполните все используемые числовые поля.');
 if(!['slope','width'].includes(p.mode)||!['constant','variable'].includes(p.depthMode)||!['pipe','box','none'].includes(p.objectType)||!['full','3'].includes(p.sectionRounding))errors.push('Неизвестный режим расчёта.');
 const h2=p.depthMode==='variable'?p.depthEnd:p.depth,minDepth=Math.min(p.depth,h2);
 if(p.length<=0||p.bottom<=0||p.depth<=0||h2<=0) errors.push('Длина, ширина дна и обе глубины должны быть больше нуля.');
 if((p.mode==='slope'&&p.slope<0)||p.bedding<0) errors.push('Откос и подсыпка не могут быть отрицательными.');
 if(p.extraFill<0)errors.push('Объём других материалов не может быть отрицательным.');
 if(p.objectType==='pipe'&&(!Number.isInteger(p.count)||p.count<1||p.count>20)) errors.push('Количество труб — целое число от 1 до 20.');
 const top=p.mode==='slope'?p.bottom+2*p.slope*p.depth:p.top;
 if(top<p.bottom) errors.push('Ширина поверху должна быть не меньше ширины дна.');
 const d=p.diameter/1000,r=d/2,m=(top-p.bottom)/(2*p.depth),center=p.bedding+r;
 if(p.bedding>minDepth)errors.push('Подсыпка превышает меньшую глубину траншеи.');
 if(p.objectType==='pipe'){
 if(p.diameter<=0||p.gap<0)errors.push('Диаметр должен быть больше нуля, зазор — неотрицательным.');
 if(p.bedding+d>minDepth) errors.push('Труба с подсыпкой не помещается по глубине.');
 // A circle fits the sloped wall only if its centre is at least r away from the wall.
 const outerCenter=(p.count-1)*(d+p.gap)/2;
 if(outerCenter+r*Math.sqrt(1+m*m)>p.bottom/2+m*center+1e-9) errors.push('Трубы не помещаются между откосами. Увеличьте ширину или уменьшите диаметр / количество.');
 }
 if(p.objectType==='box'){
 if(p.boxWidth<=0||p.boxHeight<=0)errors.push('Ширина и высота конструкции должны быть больше нуля.');
 if(p.bedding+p.boxHeight>minDepth)errors.push('Конструкция с подсыпкой не помещается по глубине.');
 if(p.boxWidth>p.bottom+2*m*p.bedding+1e-9)errors.push('Конструкция не помещается между откосами на уровне основания.');
 }
 const topEnd=p.bottom+2*m*h2;
 const rawAreaStart=p.bottom*p.depth+m*p.depth*p.depth,rawAreaEnd=p.bottom*h2+m*h2*h2;
 const rounded=p.sectionRounding==='3';
 const areaStart=rounded?Math.round(rawAreaStart*1000)/1000:rawAreaStart,areaEnd=rounded?Math.round(rawAreaEnd*1000)/1000:rawAreaEnd;
 const excavation=((areaStart+areaEnd)/2-m*(p.depth-h2)**2/6)*p.length,area=excavation/p.length;
 const pipe=p.objectType==='pipe'?Math.PI*r*r*p.length*p.count:0;
 const structure=p.objectType==='box'?p.boxWidth*p.boxHeight*p.length:0;
 const occupied=pipe+structure;
 const bed=(p.bottom*p.bedding+m*p.bedding*p.bedding)*p.length;
 const fill=bed+p.extraFill;
 const backfill=excavation-occupied-fill;
 if(backfill<-.001)errors.push('Отрицательная засыпка. Проверьте размеры и промежуточное округление.');
 return {top,topEnd,h2,m,d,area,areaStart,areaEnd,rawAreaStart,rawAreaEnd,excavation,pipe,structure,occupied,bed,fill,extraFill:p.extraFill,backfill,displaced:occupied+fill,cover:minDepth-p.bedding-(p.objectType==='pipe'?d:p.objectType==='box'?p.boxHeight:0),errors:[...new Set(errors)]};
}
