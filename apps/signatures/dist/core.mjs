// Reads CMS structure only. This module does not validate digital signatures or trust.
import {digestHex} from './vendor/hash.mjs';
const dec = new TextDecoder();
const norm = s => s.toLocaleLowerCase('ru').replaceAll('ё','е').replace(/[^а-яa-z-]/g,'');
export function parseName(value) {
  const s = value.trim().replace(/\s+/g,' ');
  const surname = '[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?';
  let m = s.match(new RegExp(`^(${surname})\\s+([А-ЯЁ])\\.?(?:\\s*([А-ЯЁ])\\.?)?$`));
  if (m) return {surname:m[1], initials:[m[2],m[3]].filter(Boolean), display:s};
  m = s.match(new RegExp(`^([А-ЯЁ])\\.\\s*(?:([А-ЯЁ])\\.\\s*)?(${surname})$`));
  if (m) return {surname:m[3], initials:[m[1],m[2]].filter(Boolean), display:s};
  m = s.match(new RegExp(`^(${surname})\\s+(${surname})(?:\\s+(${surname}))?$`));
  if (m) return {surname:m[1], given:m[2], patronymic:m[3], initials:[m[2][0],m[3]?.[0]].filter(Boolean),display:s};
  if (new RegExp(`^${surname}$`).test(s)) return {surname:s,initials:[],display:s};
  return null;
}
export function extractExpected(lines,dictionary={surname:[],given:[]}) {
  const found = [];
  const knownSurnames=new Set(dictionary.unambiguous||dictionary.surname),knownGiven=new Set(dictionary.given);
  const allSurnames=new Set(dictionary.surname);
  const stop=/^(?:Гл|Зам|Нач|Инж|Контр|Должность|Подпись|Инженер|Технический|Главный|Начальник|Разработал|Разраб|Проверил|Нормоконтроль|Согласовано|Утвердил|Формат|Лист|Листов|Стадия|Самотечная|Проектов|По|Для|Новых|Кабели|Количество|Расстояние|Наименование|Примечание|Сведения)$/i;
  const street=/(?:ул\s*\.?|улиц[аеы]?|просп\s*\.?|пр\s*-\s*кт|проспект[ае]?|переул[а-я]*|им\s*\.?|имени|города|г\s*\.)\s*$/i;
  const streetNames=new Set();
  for(const {text} of lines)for(const m of text.matchAll(/(?:ул\s*\.?|улиц[аеы]?|просп\s*\.?|пр\s*-\s*кт|проспект[ае]?)\s*((?:[А-ЯЁ]\.\s*){0,2}[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)/g))for(const w of m[1].split(/\s+/))streetNames.add(norm(w));
  const surname = '[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?';
  const patterns = [new RegExp(`(?<![А-Яа-яЁё])[А-ЯЁ]\\.\\s*(?:[А-ЯЁ]\\.\\s*)?${surname}(?![А-Яа-яЁё])`,'g'),new RegExp(`(?<![А-Яа-яЁё])${surname}\\s+[А-ЯЁ]\\.\\s*(?:[А-ЯЁ]\\.)?`,'g')];
  const roles = /директор|инженер|разраб|провер|норм.?контр|соглас|утверд|начальник|руководитель|выполн|гип|г[.]?а[.]?п/i;
  for (const line of lines) {
    const {text,page,rect}=line;
    const matches=line.drawing&&parseName(line.stampName)?[{0:line.stampName,index:text.lastIndexOf(line.stampName)}]:[];
    for(const pattern of patterns)for(const m of text.matchAll(pattern)) {
      const p=parseName(m[0]);if(!p||stop.test(p.surname))continue;
      if(street.test(text.slice(0,m.index)))continue;
      if(p.initials.length<2&&!knownSurnames.has(norm(p.surname)))continue;
      if(p.initials.length===1&&/^\s*контр/i.test(text.slice(m.index+m[0].length)))continue;
      if(!matches.some(x=>m.index<x.index+x[0].length&&x.index<m.index+m[0].length))matches.push(m);
    }
    const rolePattern=new RegExp(`(?:Разраб(?:отал|отчик)?\\.?|Провер(?:ил)?\\.?|ГИП|ГАП|Н\\s*\\.?\\s*контр\\s*\\.?|Нормоконтроль|Начальник отдела|Директор)\\s+(${surname})`,'gi');
    for(const m of text.matchAll(rolePattern)){const name=m[1];if(stop.test(name))continue;const at=m.index+m[0].lastIndexOf(name);if(!matches.some(x=>at<x.index+x[0].length&&x.index<at+name.length))matches.push({0:name,index:at});}
    // Full names and bare surnames are candidates even outside signature title blocks.
    const full = new RegExp(`${surname}\\s+${surname}\\s+${surname}`,'g');
    for(const m of text.matchAll(full)) {
      const words=m[0].split(/\s+/);if(!knownGiven.has(norm(words[1])))continue;
      if(!matches.some(x=>m.index<x.index+x[0].length&&x.index<m.index+m[0].length))matches.push(m);
    }
    const bare = new RegExp(`(?<![А-Яа-яЁё])${surname}(?![А-Яа-яЁё])`,'g');
    const endings=/(?:ов|ев|ёв|ин|ова|ева|ёва|ина|ский|цкий|ская|цкая|енко|ко|ук|юк|ич|ян|дзе|швили|ых|их)$/;
    for(const m of text.matchAll(bare)) {
      if(matches.some(x=>m.index<x.index+x[0].length&&x.index<m.index+m[0].length))continue;
      const isolated=text.trim()===m[0];
      if(knownSurnames.size?!(knownSurnames.has(norm(m[0]))||isolated&&allSurnames.has(norm(m[0]))):!endings.test(m[0]))continue;
      if(stop.test(m[0]))continue;
      if(streetNames.has(norm(m[0])))continue;
      const before=text.slice(Math.max(0,m.index-35),m.index);
      if(/(?:ул\.?|улиц[аеы]?|просп\.?|пр-кт|проспект[ае]?|переул[а-я]*|им\.?|имени|города|г\.)\s*$/i.test(before))continue;
      if(/[«"]\s*$/.test(before))continue;
      matches.push(m);
    }
    for (const m of matches) {
      const person = parseName(m[0]);
      if (!person || !line.drawing&&stop.test(person.surname)) continue;
      const source={page,text,matched:m[0],drawing:!!(line.drawing||line.drawingPage),...(line.rawText&&line.rawText!==text?{rawText:line.rawText}:{}),...(rect?{rect}: {}),...(line.drawing?{signatureRect:line.signatureRect,signatureScreenRect:line.signatureScreenRect,handwriting:line.handwriting||{status:'unchecked'}}:{})};
      const key = norm(person.surname) + ':' + person.initials.join('');
      const old = found.find(x=>x.key===key);
      if (old) { if (!old.pages.includes(page)) old.pages.push(page); if(!old.sources.some(s=>s.page===page&&s.text===text))old.sources.push(source); continue; }
      const context=text.slice(0,m.index).trim();
      found.push({...person,key,pages:[page],sources:[source],role:line.stampRole||(roles.test(context)?context:''),candidate:person.initials.length===0,incomplete:!!line.drawing&&person.surname.length<=4});
    }
  }
  // A surname-only mention of an already identified person adds evidence, not a second person.
  return found.filter(p=>{
    if(p.initials.length)return true;
    const detailed=found.filter(x=>norm(x.surname)===norm(p.surname)&&x.initials.length);
    if(detailed.length!==1)return true;
    detailed[0].pages=[...new Set([...detailed[0].pages,...p.pages])].sort((a,b)=>a-b);
    for(const source of p.sources)if(!detailed[0].sources.some(s=>s.page===source.page&&s.text===source.text))detailed[0].sources.push(source);
    return false;
  });
}
export function correctExpected(person,display,role=person.role) {
  const parsed=parseName(display.trim());
  if(!parsed)throw Error('Укажите фамилию, фамилию с инициалами или полное ФИО.');
  return {...person,...parsed,key:norm(parsed.surname)+':'+parsed.initials.join(''),role:role.trim(),corrected:true,incomplete:false};
}
export function includeHandwriting(row){
 const sources=row.sources?.length?row.sources:(row.pages?.length?row.pages:[null]).map(page=>({page,drawing:false}));
 const drawing=sources.filter(s=>s.drawing),text=sources.filter(s=>!s.drawing);
 const present=drawing.filter(s=>['present','detected'].includes(s.handwriting?.status)),candidates=drawing.filter(s=>s.handwriting?.status==='candidate'),empty=drawing.filter(s=>['empty','absent'].includes(s.handwriting?.status));
 const handwriting={present,candidates,empty};
 const occurrences=sources.map(source=>{
  if(!source.drawing)return {source,page:source.page,type:'text',status:row.status,method:'sig'};
  const hand=source.handwriting?.status;
  return {source,page:source.page,type:'drawing',method:'handwritten',status:['present','detected'].includes(hand)?'found':['empty','absent'].includes(hand)?'missing':'review'};
 });
 const sigAppliedPages=row.status==='found'?[...new Set(text.map(s=>s.page).filter(n=>n!==null))]:[];
 const result={...row,handwriting,occurrences,sigAppliedPages,sigExcludedFromDrawings:!!drawing.length&&!!row.matches?.length};
 if(row.incomplete&&!row.corrected)return {...result,status:'review',reason:'В штампе прочитан короткий фрагмент фамилии. Проверьте соседние ячейки.'};
 const found=occurrences.filter(o=>o.status==='found').length,review=occurrences.some(o=>o.status==='review');
 const status=found===occurrences.length?'found':found||review?'review':'missing';
 const evidenceType=found&&found<occurrences.length?'partial':status==='found'?(drawing.length?(text.length?'combined':'handwritten'):'electronic'):candidates.length?'candidate':undefined;
 const pageList=values=>{const pages=[...new Set(values.map(v=>v.page).filter(n=>n!==null))].sort((a,b)=>a-b);return pages.length?` (стр. ${pages.slice(0,12).join(', ')}${pages.length>12?', …':''})`:'';};
 const reasons=[];
 if(text.length)reasons.push(`Текстовая часть: ${row.status==='found'?'ЭП из SIG найдена':row.status==='review'?'совпадение с SIG требует проверки':'ЭП из SIG не найдена'}${pageList(text)}.`);
 if(drawing.length){
  if(present.length)reasons.push(`Чертежи: рукописная найдена${pageList(present)}.`);
  if(empty.length)reasons.push(`Рукописная не найдена${pageList(empty)}.`);
  const uncertain=occurrences.filter(o=>o.type==='drawing'&&o.status==='review');if(uncertain.length)reasons.push(`Графы требуют проверки${pageList(uncertain)}.`);
  if(row.matches?.length)reasons.push('SIG не засчитывается на чертежах.');
 }
 return {...result,status,evidenceType,reason:reasons.join(' ')};
}
export function restoreHandwriting(expected,previous){
 const key=s=>JSON.stringify([s.page,(s.signatureRect||s.rect||[]).map(n=>Math.round(n*10)/10),s.text]);
 const saved=new Map(previous.flatMap(p=>(p.sources||[]).filter(s=>s.handwriting?.manual).map(s=>[key(s),s.handwriting])));
 for(const p of expected)for(const source of p.sources||[]){const old=saved.get(key(source));if(old)source.handwriting={...old};}
 return expected;
}
export function matchPeople(expected,signers) {
  return expected.map(person=>{
    const p = parseName(person.display);
    if (!p) return {...person,status:'review',reason:'Не удалось разобрать имя'};
    const sameSurname = signers.filter(s=>norm(s.surname||parseName(s.name)?.surname||'')===norm(p.surname));
    const matches = sameSurname.filter(s=>{
      const parsed = parseName(s.name);
      const given = s.given || parsed?.given || '';
      const patronymic = s.patronymic || parsed?.patronymic || '';
      if (p.given && norm(p.given)!==norm(given)) return false;
      if (p.patronymic && norm(p.patronymic)!==norm(patronymic)) return false;
      const initials = [given[0],patronymic[0]].filter(Boolean);
      return p.initials.every((x,i)=>norm(x)===norm(initials[i]||''));
    });
    const identities = [...new Set(matches.map(x=>norm(x.name)))];
    if (!matches.length) return {...person,status:'missing',matches:[],reason:'В прочитанных записях подписи совпадение не найдено'};
    if (identities.length>1 || p.initials.length===0) return {...person,status:'review',matches,reason:p.initials.length===0?'Указана только фамилия — подтвердите совпадение':'Несколько людей с одинаковыми фамилией и инициалами'};
    return {...person,status:'found',matches,reason:'Фамилия и указанные имя / инициалы совпадают'};
  });
}
function tree(bytes) {
  let count=0;
  function read(start,limit,depth=0) {
    if (++count>60000 || depth>60 || start+2>limit) throw Error('Повреждённая структура ASN.1');
    let at=start; const tag=bytes[at++];
    if ((tag&31)===31) throw Error('Неподдерживаемый тег ASN.1');
    let len=bytes[at++], indefinite=len===128;
    if (len>128) { const n=len&127; if(n>4||at+n>limit) throw Error('Некорректная длина ASN.1'); len=0; for(let i=0;i<n;i++)len=len*256+bytes[at++]; }
    const content=at, end=indefinite?limit:at+len;
    if(end>limit)throw Error('Файл подписи обрезан');
    const children=[];
    if(tag&32) {
      while(at<end) {
        if(indefinite&&bytes[at]===0&&bytes[at+1]===0)break;
        const child=read(at,end,depth+1);children.push(child);at=child.end;
      }
    } else {if(indefinite)throw Error('Некорректная неопределённая длина');at=end;}
    if(indefinite && (at+1>=limit||bytes[at]!==0||bytes[at+1]!==0))throw Error('ASN.1 без завершающего маркера');
    return {tag,start,content,contentEnd:indefinite?at:end,end:indefinite?at+2:end,children};
  }
  const root=read(0,bytes.length); if(root.end!==bytes.length)throw Error('Лишние данные после CMS'); return root;
}
const hex = b=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
function oid(bytes,n) {
  const b=bytes.subarray(n.content,n.contentEnd);let values=[],v=0;
  for(const x of b){v=v*128+(x&127);if(!(x&128)){values.push(v);v=0;}}
  const first=values.shift();return [first<40?0:first<80?1:2,first<40?first:first<80?first-40:first-80,...values].join('.');
}
function string(bytes,n) {
  const b=bytes.subarray(n.content,n.contentEnd);
  if(n.tag===30){let s='';for(let i=0;i+1<b.length;i+=2)s+=String.fromCharCode(b[i]*256+b[i+1]);return s;}
  return dec.decode(b);
}
function attributes(bytes,n) {
  const a={}; for(const set of n.children) for(const pair of set.children){if(pair.children.length>=2)a[oid(bytes,pair.children[0])]=string(bytes,pair.children[1]);} return a;
}
export function decodeCms(input,filename='подпись.sig') {
  let bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  const head=dec.decode(bytes.subarray(0,80));
  if(head.trimStart().startsWith('-----BEGIN') || /^[A-Za-z0-9+/=\s]+$/.test(dec.decode(bytes))) {
    const b64=dec.decode(bytes).replace(/-----[^-]+-----/g,'').replace(/\s/g,'');
    try {bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));}catch{throw Error('Некорректная Base64-подпись');}
  }
  const root=tree(bytes);
  if(root.tag!==48||oid(bytes,root.children[0])!=='1.2.840.113549.1.7.2')throw Error('Ожидается подпись CMS / PKCS#7 SignedData');
  const sd=root.children[1]?.children[0];
  if(!sd||sd.children.length<4)throw Error('Неполный контейнер SignedData');
  const certNode=sd.children.find((x,i)=>i>=3&&x.tag===160);
  const certs=(certNode?.children||[]).filter(x=>x.tag===48).map(c=>{
    const tbs=c.children[0]; const off=tbs.children[0]?.tag===160?1:0;
    const serial=hex(bytes.subarray(tbs.children[off].content,tbs.children[off].contentEnd));
    const issuer=tbs.children[off+2], subject=tbs.children[off+4];
    const attrs=attributes(bytes,subject);
    let ski=''; const ext=tbs.children.find(x=>x.tag===163);
    for(const e of ext?.children[0]?.children||[]){if(oid(bytes,e.children[0])==='2.5.29.14'){const v=e.children.at(-1);try {const b=bytes.subarray(v.content,v.contentEnd),r=tree(b);ski=hex(b.subarray(r.content,r.contentEnd));}catch{}}}
    const surname=attrs['2.5.4.4']||'', g=(attrs['2.5.4.42']||'').split(/\s+/);
    const name=attrs['2.5.4.3']||[surname,...g].filter(Boolean).join(' '), parsed=parseName(name);
    return {serial,issuer:hex(bytes.subarray(issuer.start,issuer.end)),ski,name,surname:surname||parsed?.surname||'',given:g[0]||parsed?.given||'',patronymic:g.slice(1).join(' ')||parsed?.patronymic||''};
  });
  const infos=sd.children.at(-1);
  if(infos.tag!==49||!infos.children.length)throw Error('В контейнере нет записей подписи SignerInfo');
  const signers=infos.children.map((si,index)=>{
    const sid=si.children[1];let cert;
    if(sid.tag===48){const issuer=sid.children[0],serial=sid.children[1];cert=certs.find(c=>c.serial===hex(bytes.subarray(serial.content,serial.contentEnd))&&c.issuer===hex(bytes.subarray(issuer.start,issuer.end)));}
    else if(sid.tag===128){cert=certs.find(c=>c.ski&&c.ski===hex(bytes.subarray(sid.content,sid.contentEnd)));}
    const digestAlgorithm=oid(bytes,si.children[2].children[0]);
    const attrs=si.children.find((c,i)=>i>=3&&c.tag===160);let digest=null;
    for(const a of attrs?.children||[])if(oid(bytes,a.children[0])==='1.2.840.113549.1.9.4'){const n=a.children[1]?.children[0];if(n?.tag===4)digest=hex(bytes.subarray(n.content,n.contentEnd));}
    const signature=si.children.find((c,i)=>i>=3&&c.tag===4);
    if(!signature||signature.contentEnd===signature.content)throw Error('Пустое значение подписи в SignerInfo');
    return {...(cert||{name:'Сертификат подписанта отсутствует',surname:'',given:'',patronymic:''}),identified:!!cert,file:filename,index:index+1,digestAlgorithm,digest};
  });
  return {signers,detached:sd.children[2].children.length===1,certificateCount:certs.length};
}
export async function checkDigest(signer,pdfBytes) {
  const algo={'1.3.14.3.2.26':'SHA-1','2.16.840.1.101.3.4.2.1':'SHA-256','2.16.840.1.101.3.4.2.2':'SHA-384','2.16.840.1.101.3.4.2.3':'SHA-512'}[signer.digestAlgorithm];
  if(!signer.digest)return {status:'unchecked',text:'В подписи нет атрибута хеша; связь с PDF не проверена'};
  if(!algo)return {status:'unchecked',text:signer.digestAlgorithm.startsWith('1.2.643.')?'ГОСТ: связь с PDF и действительность подписи требуют проверки в КриптоПро':'Алгоритм хеша не поддержан; связь с PDF не проверена'};
  const actual=await digestHex(algo,pdfBytes);
  return actual===signer.digest?{status:'digest-match',text:'Хеш PDF совпадает. Криптографическая подпись и доверие сертификату не проверены'}:{status:'mismatch',text:'Хеш не совпадает с выбранным PDF — подпись исключена из сопоставления'};
}
