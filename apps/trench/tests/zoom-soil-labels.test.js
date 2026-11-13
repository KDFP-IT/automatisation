import test from 'node:test';
import assert from 'node:assert/strict';
import {cameraFrame,clampCameraZoom,drawWellMesh} from '../dist/scene3d.js';
import {drawSection,drawEdge3d} from '../dist/network-views.js';
import {seedProject,resolveEdge} from '../dist/network-model.js';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('3D zoom scales about the same model centre and pan is in screen coordinates at every yaw',()=>{
 const bounds=[[-3,-8,-2],[3,8,2]],point=[1,2,1];
 for(const yaw of [-130,0,110]){const normal=cameraFrame(bounds,{yaw,pitch:30}),zoomed=cameraFrame(bounds,{yaw,pitch:30,zoom:3,panX:40,panY:-20}),a=normal.project(point),b=zoomed.project(point);assert.deepEqual(normal.centre,zoomed.centre);near(zoomed.scale,normal.scale*3);near(b[0],450+(a[0]-450)*3+40);near(b[1],250+(a[1]-250)*3-20)}
 assert.equal(clampCameraZoom(-4),.5);assert.equal(clampCameraZoom(1000),6);assert.equal(clampCameraZoom(NaN),1);assert.equal(clampCameraZoom(Infinity),1);
});
test('zoom changes rendered pipe and well geometry without modifying the project or longitudinal angle',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e),before=structuredClone(p),normal=drawEdge3d(p,e,res,{zoom:1}),nearer=drawEdge3d(p,e,res,{zoom:4});assert.notEqual(normal,nearer);assert.equal(normal.match(/data-beta="([^"]+)"/)[1],nearer.match(/data-beta="([^"]+)"/)[1]);assert.notEqual(drawWellMesh(p,p.wells[0],{zoom:1}),drawWellMesh(p,p.wells[0],{zoom:4}));assert.deepEqual(p,before);
});
test('section soil names follow visible geological bands, selected station and show-soils toggle',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e);const s=drawSection(p,e,res,.5);for(const soil of p.soils)assert.ok(s.includes('data-soil-label="'+soil.id+'"'));
 assert.ok(!drawSection(p,e,res,.5,false).includes('data-soil-label'));
 e.layers=[{soil:p.soils[0].id,start:20,end:20}];const single=drawSection(p,e,res,.5);assert.ok(single.includes('data-soil-label="ige1"'));assert.ok(!single.includes('data-soil-label="ige3"'));
});
test('thin stratum receives a leader, soil names are escaped and strata below the bottom are not labelled',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e);p.soils[0].name='Песок <script> & "тест"';e.layers=[{soil:'ige1',start:.001,end:.001},{soil:'ige3',start:20,end:20},{soil:'ige5',start:30,end:30}];const html=drawSection(p,e,res,.5);assert.ok(html.includes('soil-callout'));assert.ok(html.includes('Песок &lt;script&gt; &amp; &quot;тест&quot;'));assert.ok(!html.includes('data-soil-label="ige5"'));assert.ok(!html.includes('<script>'));
});
