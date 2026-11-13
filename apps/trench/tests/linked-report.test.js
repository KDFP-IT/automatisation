import test from 'node:test';
import assert from 'node:assert/strict';
import {seedProject,resolveEdge,calculateNetwork} from '../dist/network-model.js';
import {nearestStationRatio,profileRatio,stationInfo,linkedViews,networkReport,reportTable} from '../dist/network-linked.js';
const near=(a,b,t=1e-7)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);

test('plan selection projects onto a bent route by chainage, not endpoint distance',()=>{
 const res={length:7,points:[{x:0,y:0,s:0},{x:3,y:0,s:3},{x:3,y:4,s:7}]};
 near(nearestStationRatio(res,1,1),1/7);near(nearestStationRatio(res,5,2),5/7);
 near(nearestStationRatio(res,-3,0),0);near(nearestStationRatio(res,3,9),1);
 near(profileRatio(85),0);near(profileRatio(450),.5);near(profileRatio(815),1);
 near(profileRatio(-100),0);near(profileRatio(950),1);
});
test('one station supplies interpolated levels, local section and layer boundaries to all views',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e);
 e.layers[0].start=1;e.layers[0].end=2;
 const ratio=.7,info=stationInfo(e,res,ratio);
 near(info.s,res.length*ratio);const j=res.points.findIndex(v=>v.s>=info.s),a=res.points[j-1],b=res.points[j];near(info.c.invert,a.invert+(b.invert-a.invert)*(info.s-a.s)/(b.s-a.s));
 near(info.layers[0].bottom,1.7);near(info.layers[1].top,1.7);
 assert.equal(info.section,e.sections.find(v=>v.a<=ratio&&v.b>ratio));
 const views=linkedViews(p,calculateNetwork(p),e,res,ratio,true);
 assert.match(views.plan,/class="linked-station"/);assert.match(views.profile,/station-marker-label/);
 assert.match(views.section,/Сечение/);assert.match(views.metrics,/Границы грунтов/);
 const world=views.unmap([450,260]);assert.ok(world.every(Number.isFinite));
});
test('report reconciles trenches plus each shared well exactly once, including all soils',()=>{
 const p=seedProject(),result=calculateNetwork(p),report=networkReport(p,result);
 assert.equal(report.rows.length,2);assert.ok(report.valid);near(report.length,21.02+8.75);
 for(const key of ['excavation','backfill'])near(report.edges[key]+report.wells[key],report.total[key]);
 for(const soil of p.soils)near(report.edges.soils[soil.id]+report.wells.soils[soil.id],result.total.soils[soil.id]);
 near(Object.values(report.edges.soils).reduce((a,b)=>a+b,0),report.edges.excavation,.001);
 assert.equal(report.rows[0].from,'Д12');assert.equal(report.rows[0].to,'КК2-12');
 const html=reportTable(p,result,p.edges[0].id);assert.match(html,/Итого траншеи участков/);assert.match(html,/Котлованы колодцев · 3 шт./);assert.match(html,/Всего по проекту/);
});
test('invalid geometry gives no authoritative total or fabricated zero-valued edge result',()=>{
 const p=seedProject();p.edges[0].diameter=-1;
 const result=calculateNetwork(p),report=networkReport(p,result),html=reportTable(p,result,null);
 assert.equal(report.valid,false);assert.equal(report.rows[0].valid,false);
 assert.match(html,/Общий итог не подтверждён/);assert.match(html,/class=" invalid"/);
 const footer=html.slice(html.indexOf('<tfoot>'),html.indexOf('</tfoot>'));
 assert.doesNotMatch(footer,/\d+,\d{3}/);
});
