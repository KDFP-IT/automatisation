import {makeWell,makeEdge,makeSection} from './network-model.js';
// Manual transcription of drawing 30/09-ТКР10.1, sheet 3, revision 4 (16.09.26).
// A geometric illustration, not an approved earthworks quantity takeoff.
export function kulkoD13(){
 const p={version:3,id:'kulko-d13-reference',name:'Кулько · Д13 → Д13′ · по листу 3',notes:'Источник: «30_09-ТКР10.1 изм.-Профили Лист 3.pdf», папка «Кулько/Не убирать!/ли», изменение 4 от 16.09.2026. С листа: L=28,06 м; труба КОРСИС ПРО DN/OD400 SN16; проектная земля 121,605 → 121,607; отметки низа/лотка 117,756 → 117,196; футляр ПЭ100 SDR17 Ø710×42,1 L=27,06 м; ЩПС 0,15 м; колодцы Ø1000. Допущения: координаты локальные, участок выпрямлен; отметки «низа или лотка» приняты за наружный низ для визуализации; футляр расположен симметрично с отступами по 0,50 м, его границы не привязаны на профиле; стенка трубы 24 мм условная; ширина траншеи 1,31 м, откосы 45°, защитный слой 0,30 м и размеры конструкций колодцев условные. Внутреннее дно колодцев принято на 0,15 м ниже низа трубы, горловина 0,60 м, стенки 0,12 м, днище/перекрытие 0,20 м; заложение котлована 1:1 и щебёночная подготовка 0,30 м взяты из примечаний листа 11, прочие размеры условные. Геология не оцифрована: один неопределённый грунт, группа II условная. Все объёмы предварительные; геологические штриховки исходного листа не заменены вымышленными слоями.',soils:[{id:'unconfirmed',name:'Грунт не определён · группа II условная',group:'II',color:'#b9c2c9'}],wells:[],edges:[]};
 const a=makeWell('Д13',0,0),b=makeWell('Д13′',28.06,0);
 for(const [w,ground,invert] of [[a,121.605,117.756],[b,121.607,117.196]]){
  w.ground=ground;w.diameter=1;w.neckHeight=.6;w.slab=.2;w.base=.2;w.workingHeight=ground-w.neckHeight-w.slab-(invert-.15);w.pad=.3;w.pitSlope=1;w.layers=[{soil:'unconfirmed',bottom:20}];
 }
 p.wells=[a,b];const e=makeEdge(p,a.id,b.id);a.ports[0].invert=117.756;b.ports[0].invert=117.196;
 e.pipeWall=.024;e.sections=[makeSection(0,.5/28.06),makeSection(.5/28.06,27.56/28.06),makeSection(27.56/28.06,1)];
 for(const s of e.sections){s.width=1.31;s.left=45;s.right=45;s.bedding=.15;s.protection=.3}
 e.sections[1].casing=.710;e.sections[1].casingWall=.0421;
 e.layers=[{soil:'unconfirmed',start:20,end:20}];p.edges=[e];return p;
}
