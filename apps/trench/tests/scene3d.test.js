import test from 'node:test';
import assert from 'node:assert/strict';
import {cameraTransform,cameraFrame,drawEdgeMesh,drawWellMesh} from '../dist/scene3d.js';
import {seedProject,resolveEdge,calculateNetwork} from '../dist/network-model.js';
const near=(a,b,e=1e-9)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
test('camera rotates an orthonormal coordinate frame without shearing or rescaling',()=>{
 for(const yaw of [-180,-90,-35,0,45,90,180])for(const pitch of [10,30,60,80]){
  const axes=[[1,0,0],[0,1,0],[0,0,1]].map(v=>cameraTransform(v,{yaw,pitch}));for(const axis of axes)near(Math.hypot(...axis),1);
  for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)near(axes[i].reduce((s,v,k)=>s+v*axes[j][k],0),0);
 }
});
test('orbit uses a stable centre and scale and keeps the bounding volume in view',()=>{
 const bounds=[[-4,-6,-2],[4,6,2]],base=cameraFrame(bounds,{yaw:0,pitch:30});
 for(const yaw of [-180,-100,-35,0,80,180])for(const pitch of [10,45,80]){const frame=cameraFrame(bounds,{yaw,pitch});near(frame.scale,base.scale);assert.deepEqual(frame.centre,base.centre);for(const p of bounds){const q=frame.project(p);assert.ok(q[0]>0&&q[0]<900&&q[1]>0&&q[1]<520)}}
});
test('edge and well 3D scenes contain real soil bands; hiding them removes soil faces',()=>{
 const p=seedProject(),e=p.edges[0],res=resolveEdge(p,e),w=p.wells[2];
 for(const yaw of [-170,-35,60,170]){
  const edge=drawEdgeMesh(p,e,res,{yaw,pitch:35,showSoils:true}),well=drawWellMesh(p,w,{yaw,pitch:35,showSoils:true});
  assert.ok(edge.includes('data-soil="ige1"'));assert.ok(edge.includes('data-soil="ige3"'));assert.ok(well.includes('data-soil="ige5"'));
  assert.ok(!/NaN|Infinity|undefined/.test(edge+well));
 }
 assert.ok(!drawEdgeMesh(p,e,res,{showSoils:false}).includes('data-soil='));assert.ok(!drawWellMesh(p,w,{showSoils:false}).includes('data-soil='));
});
test('editing soil boundaries changes both soil geometry and allocated excavation',()=>{
 const p=seedProject(),e=p.edges[0],before=drawEdgeMesh(p,e,resolveEdge(p,e),{}),vol=calculateNetwork(p).edges[e.id].soils.ige1;
 e.layers[0].start=.3;e.layers[0].end=.4;
 assert.notEqual(drawEdgeMesh(p,e,resolveEdge(p,e),{}),before);assert.ok(calculateNetwork(p).edges[e.id].soils.ige1<vol);
});
