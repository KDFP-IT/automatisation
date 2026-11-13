// Geometry is expressed in the visible page, then converted back to PDF coordinates.
const clean=s=>s.replace(/[\s.]/g,'').toLowerCase().replaceAll('ё','е');
const role=/^(?:разраб(?:отал|отчик)?|провер(?:ил)?|гип|гап|нконтр|нормоконтроль|глинж|главныйинженер)$/;
export function repairCadEncoding(text){
 // A legacy CAD CMap uses U+01C9..U+0208 for Cyrillic U+0410..U+044F.
 // Repair only mixed Cyrillic words, leaving ordinary Latin text unchanged.
 return text.replace(/[А-Яа-яЁё\u01c9-\u0208]+/g,word=>/[А-Яа-яЁё]/.test(word)?word.replace(/[\u01c9-\u0208]/g,c=>String.fromCharCode(c.charCodeAt(0)+0x247)):word);
}
function pdfRect(view,r){const a=view.convertToPdfPoint(r[0],r[1]),b=view.convertToPdfPoint(r[2],r[3]);return [Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])];}
export function visibleItems(items,view){return items.filter(i=>i.str?.trim()).map(i=>{
 const t=i.transform,v=view.transform,tx=[v[0]*t[0]+v[2]*t[1],v[1]*t[0]+v[3]*t[1],v[0]*t[2]+v[2]*t[3],v[1]*t[2]+v[3]*t[3],v[0]*t[4]+v[2]*t[5]+v[4],v[1]*t[4]+v[3]*t[5]+v[5]];
 return {text:repairCadEncoding(i.str),raw:i.str,x:tx[4],y:tx[5],width:i.width*(view.scale||1),height:Math.max(Math.hypot(tx[2],tx[3]),i.height*(view.scale||1),2),horizontal:Math.abs(tx[1])<Math.abs(tx[0])*.25};
});}
export function joinFragments(parts){
 const sorted=[...parts].sort((a,b)=>a.x-b.x);let text='',previous;
 for(const p of sorted){const gap=previous?p.x-previous.x-previous.width:Infinity,letterWidth=previous?previous.width/Math.max(previous.text.length,1):0;
 const continuation=previous&&gap<Math.max(.9,letterWidth*.4)&&/[А-Яа-яЁё-]$/.test(text)&&/^[а-яё]/.test(p.text);
 text+=(text&&!continuation?' ':'')+p.text.trim();previous=p;
 }return text.replace(/\s+/g,' ').trim();
}
export function pageLines(items,view,page){
 const parts=visibleItems(items,view),groups=[];
 for(const p of parts.filter(p=>p.horizontal)){let group=groups.find(g=>Math.abs(g.y-p.y)<=Math.max(1.2,Math.min(g.height,p.height)*.24));if(!group){group={y:p.y,height:p.height,parts:[]};groups.push(group);}group.parts.push(p);}
 const lines=groups.sort((a,b)=>a.y-b.y).map(g=>{const r=[Math.min(...g.parts.map(p=>p.x))-2,Math.min(...g.parts.map(p=>p.y-p.height))-2,Math.max(...g.parts.map(p=>p.x+p.width))+2,Math.max(...g.parts.map(p=>p.y+p.height*.25))+2];return {page,text:joinFragments(g.parts),rawText:joinFragments(g.parts.map(p=>({...p,text:p.raw}))),screenRect:r,rect:pdfRect(view,r)};});
 const stamps=[];
 // Standard title block: the name and signature columns follow the role column.
 const candidates=parts.filter(p=>p.horizontal&&p.x>view.width-650&&p.y>view.height-180);
 const roleGroups=[];
 for(const p of candidates){let g=roleGroups.find(g=>Math.abs(g.y-p.y)<2&&Math.abs(g.x-p.x)<53);if(!g){g={x:p.x,y:p.y,parts:[]};roleGroups.push(g);}g.parts.push(p);}
 const anchors=roleGroups.map(g=>({...g,text:joinFragments(g.parts)})).filter(g=>role.test(clean(g.text)));
 for(const a of anchors){
  // If adjacent role fragments were in separate PDF text items, recombine them first.
  const x=a.x,near=anchors.filter(b=>Math.abs(b.x-x)<5&&b!==a).map(b=>Math.abs(b.y-a.y)).filter(d=>d>7),rowHeight=Math.min(14.17,...near),half=Math.max(5,rowHeight*.48);
  const nameLeft=x+52,nameRight=x+111,signatureLeft=x+111.5,signatureRight=x+154.5;
  const fragments=candidates.filter(p=>p.x>=nameLeft&&p.x<signatureRight&&Math.abs(p.y-a.y)<half);
  let name=joinFragments(fragments).replace(/\s+\d.*$/,'').trim();
  // CAD sometimes puts a surname on two text lines in the same cell.
  if(name&&name.length<=5){const below=candidates.filter(p=>p.x>=nameLeft&&p.x<nameRight&&p.y>a.y+half&&p.y<a.y+rowHeight*.95&&/^[а-яё]+$/.test(p.text.trim()));if(below.length)name+=joinFragments(below);}
  if(!/^[А-ЯЁ][а-яё-]{1,}(?:\s+[А-ЯЁ]\.\s*(?:[А-ЯЁ]\.)?)?$/.test(name))continue;
  const r=[x-3,a.y-11,nameRight+2,a.y+4],sig=[signatureLeft,a.y-10,signatureRight,a.y+3];
  stamps.push({page,text:`${a.text} ${name}`,rawText:joinFragments(a.parts.map(p=>({...p,text:p.raw})))+' '+joinFragments(fragments.map(p=>({...p,text:p.raw}))),matched:name,stampName:name,stampRole:a.text,drawing:true,screenRect:r,rect:pdfRect(view,r),signatureRect:pdfRect(view,sig),signatureScreenRect:sig});
 }
 const drawingPage=stamps.length>0||anchors.length>=2;
 const filtered=lines.filter(line=>!stamps.some(s=>Math.abs((line.screenRect[1]+line.screenRect[3])/2-(s.screenRect[1]+s.screenRect[3])/2)<7&&line.screenRect[0]<s.screenRect[2]&&line.screenRect[2]>s.screenRect[0])).map(line=>({...line,drawingPage}));
 return [...filtered,...stamps];
}
export function inkEvidence(data,width,height){
 const mask=new Uint8Array(width*height);let colored=0;
 for(let y=2;y<height-2;y++)for(let x=2;x<width-2;x++){const i=(y*width+x)*4,r=data[i],g=data[i+1],b=data[i+2];if(Math.min(r,g,b)<155&&(r+g+b)/3<215){mask[y*width+x]=1;if(b>r+25&&b>g+10)colored++;}}
 // Erase long table rules before looking for strokes; never interpret a grid as a signature.
 const eraseRows=[],eraseCols=[];
 for(let y=0;y<height;y++){let n=0;for(let x=0;x<width;x++)n+=mask[y*width+x];if(n>width*.68)eraseRows.push(y);}
 for(let x=0;x<width;x++){let n=0;for(let y=0;y<height;y++)n+=mask[y*width+x];if(n>height*.68)eraseCols.push(x);}
 for(const y of eraseRows)for(let yy=Math.max(0,y-1);yy<=Math.min(height-1,y+1);yy++)for(let x=0;x<width;x++)mask[yy*width+x]=0;
 for(const x of eraseCols)for(let xx=Math.max(0,x-1);xx<=Math.min(width-1,x+1);xx++)for(let y=0;y<height;y++)mask[y*width+xx]=0;
 let pixels=0,minX=width,minY=height,maxX=0,maxY=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(mask[y*width+x]){pixels++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
 const spanX=maxX-minX,spanY=maxY-minY,candidate=pixels>=18&&spanX>=8&&spanY>=4,density=pixels/Math.max(1,(spanX+1)*(spanY+1));
 const detected=candidate&&spanX>=12&&spanY>=6&&density>.015&&density<.6&&(colored>=20||pixels>=90);
 return {status:detected?'detected':candidate?'candidate':'empty',pixels,colored,automatic:true,reason:detected?'На изображении графы обнаружен росчерк; учитывается как подпись. Проверьте отметку при сомнении.':candidate?'Есть отдельные штрихи: требуется проверить, что это подпись':'Росчерк автоматически не обнаружен; можно проверить вручную'};
}
