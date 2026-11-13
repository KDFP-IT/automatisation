import test from 'node:test';
import assert from 'node:assert/strict';
import {moveLayer,setLayerThickness,layerThicknesses} from '../dist/layer-editing.js';
import {seedProject,calculateNetwork,validateProject} from '../dist/network-model.js';
test('reordering strata preserves each thickness at both ends and total investigation depth',()=>{
 const layers=[{soil:'A',start:1,end:2},{soil:'B',start:4,end:6},{soil:'C',start:10,end:11}];
 const copy=structuredClone(layers),moved=moveLayer(layers,0,2);
 assert.deepEqual(moved,[{soil:'B',start:3,end:4},{soil:'C',start:9,end:9},{soil:'A',start:10,end:11}]);
 assert.deepEqual(layers,copy);
 assert.deepEqual(layerThicknesses(moved),[{soil:'B',start:3,end:4},{soil:'C',start:6,end:5},{soil:'A',start:1,end:2}]);
 assert.deepEqual(moveLayer(moved,2,0),layers);
});
test('well strata move with thickness; thickness edits shift deeper boundaries only',()=>{
 const layers=[{soil:'A',bottom:1},{soil:'B',bottom:3},{soil:'C',bottom:7}];
 assert.deepEqual(moveLayer(layers,2,0,true),[{soil:'C',bottom:4},{soil:'A',bottom:5},{soil:'B',bottom:7}]);
 assert.deepEqual(setLayerThickness(layers,1,'bottom',3,true),[{soil:'A',bottom:1},{soil:'B',bottom:4},{soil:'C',bottom:8}]);
 assert.throws(()=>setLayerThickness(layers,1,'bottom',0,true));
 assert.throws(()=>moveLayer([{soil:'A',bottom:2},{soil:'B',bottom:1}],0,1,true));
 assert.throws(()=>moveLayer(layers,0,3,true));
});
test('soil reorder changes soil allocation without changing excavation, backfill or total covered volume',()=>{
 const p=seedProject(),before=calculateNetwork(p);p.edges[0].layers=moveLayer(p.edges[0].layers,0,1);
 const after=calculateNetwork(p);assert.equal(after.valid,true);
 assert.ok(Math.abs(before.total.excavation-after.total.excavation)<1e-8);
 assert.ok(Math.abs(before.total.backfill-after.total.backfill)<1e-8);
 assert.notDeepEqual(before.edges[p.edges[0].id].soils,after.edges[p.edges[0].id].soils);
 assert.ok(Math.abs(Object.values(after.total.soils).reduce((a,b)=>a+b,0)-after.total.excavation)<.001);
});
test('bedding material metadata roundtrips legacy-compatible JSON and leaves geometric quantities unchanged',()=>{
 const p=seedProject(),before=calculateNetwork(p);p.edges[0].sections[0].beddingMaterial='Песок';
 const loaded=validateProject(JSON.parse(JSON.stringify(p))),after=calculateNetwork(loaded);
 assert.equal(loaded.edges[0].sections[0].beddingMaterial,'Песок');assert.equal(after.total.backfill,before.total.backfill);
 loaded.edges[0].sections[0].beddingMaterial={};assert.throws(()=>validateProject(loaded));
});
