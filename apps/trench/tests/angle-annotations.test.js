import test from 'node:test';
import assert from 'node:assert/strict';
import {seedProject,resolveEdge,crossSection,setSlopeMode} from '../dist/network-model.js';
import {angleMetrics} from '../dist/angle-annotations.js';
import {drawProfile,drawSection,drawEdge3d} from '../dist/network-views.js';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
test('local pipe angle follows the selected profile leg with consistent falling/rising signs',()=>{
 const p=seedProject(),e=p.edges[0];e.waypoints[0].invert=118.7;const res=resolveEdge(p,e),a=angleMetrics(e,res,.2),b=angleMetrics(e,res,.9);
 near(a.beta,Math.atan((res.portA.invert-118.7)/res.points[1].s)*180/Math.PI);assert.ok(a.beta<0);assert.equal(a.direction,'подъём');assert.ok(b.beta>0);assert.equal(b.direction,'падение');near(b.perMille,Math.tan(b.beta*Math.PI/180)*1000);
 assert.equal(angleMetrics(e,res,-2).s,0);near(angleMetrics(e,res,2).s,res.length);
});
test('slope annotations use actual asymmetric angles and remain equivalent after upper-width conversion',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e),s=e.sections[0];s.left=60;s.right=35;let m=angleMetrics(e,res,.1);near(m.left,60);near(m.right,35);
 const html=drawSection(p,e,res,.1);const values=[...html.matchAll(/data-slope-angle="([^"]+)"/g)].map(v=>Number(v[1]));near(values[0],60);near(values[1],35);
 s.left=s.right=55;const before=angleMetrics(e,res,.1);setSlopeMode(e,res,s,'top');m=angleMetrics(e,res,.1);near(m.left,before.left);near(m.right,before.right);
});
test('displayed pipe angle is invariant under 3D camera, based on real length, and rendering does not mutate input',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e),before=structuredClone(p),expected=angleMetrics(e,res,.8).beta;
 for(const camera of [{yaw:0,pitch:10},{yaw:130,pitch:75}]){
  const html=drawEdge3d(p,e,res,{...camera,ratio:.8});near(Number(html.match(/data-beta="([^"]+)"/)[1]),expected);assert.match(html,/Камера:/);
 }
 near(Number(drawProfile(p,e,res,true,.8).match(/data-beta="([^"]+)"/)[1]),expected);assert.deepEqual(p,before);
});
test('supports display pipe inclination without inventing trench slope annotations',()=>{
 const p=seedProject(),e=p.edges[0];for(const s of e.sections)s.method='supports';const res=resolveEdge(p,e),section=drawSection(p,e,res,.5),mesh=drawEdge3d(p,e,res,{});
 assert.doesNotMatch(section,/data-slope-angle/);assert.doesNotMatch(section,/Откосы от горизонтали/);assert.doesNotMatch(mesh,/Откосы от горизонтали/);assert.match(mesh,/data-beta=/);
});
