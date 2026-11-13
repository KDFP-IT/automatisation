const keys=well=>well?['bottom']:['start','end'];
export function layerThicknesses(layers,well=false){
 const previous=Object.fromEntries(keys(well).map(k=>[k,0]));
 return layers.map(layer=>{const out={...layer};for(const key of keys(well)){out[key]=layer[key]-previous[key];previous[key]=layer[key];if(!Number.isFinite(out[key])||out[key]<=0)throw Error('Сначала исправьте глубины слоёв: границы должны возрастать.')}return out});
}
function cumulative(thicknesses,well){
 const depth=Object.fromEntries(keys(well).map(k=>[k,0]));
 return thicknesses.map(layer=>{const out={...layer};for(const key of keys(well)){depth[key]+=layer[key];out[key]=Number(depth[key].toFixed(9))}return out});
}
export function moveLayer(layers,from,to,well=false){
 if(!Number.isInteger(from)||!Number.isInteger(to)||from<0||to<0||from>=layers.length||to>=layers.length)throw Error('Неверный номер слоя.');
 const thicknesses=layerThicknesses(layers,well),[moved]=thicknesses.splice(from,1);thicknesses.splice(to,0,moved);return cumulative(thicknesses,well);
}
export function setLayerThickness(layers,index,key,value,well=false){
 if(!keys(well).includes(key)||!Number.isInteger(index)||index<0||index>=layers.length||!Number.isFinite(value)||value<=0)throw Error('Толщина слоя должна быть больше нуля.');
 const thicknesses=layerThicknesses(layers,well);thicknesses[index][key]=value;return cumulative(thicknesses,well);
}
