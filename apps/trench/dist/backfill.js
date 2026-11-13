export const backfillSource=o=>o.backfillSource||'excavated';
export const backfillName=o=>backfillSource(o)==='imported'?(o.backfillMaterial||'Песок'):'Вынутый грунт';
export function assignBackfill(r,o){if(!r)return r;return {...r,nativeBackfill:backfillSource(o)==='excavated'?r.backfill:0,importedBackfill:backfillSource(o)==='imported'?r.backfill:0}}
export function validateBackfill(o){if(o.backfillSource!==undefined&&!['excavated','imported'].includes(o.backfillSource))throw Error('Выберите материал засыпки.');if(o.backfillMaterial!==undefined&&(typeof o.backfillMaterial!=='string'||!o.backfillMaterial.trim()||o.backfillMaterial.length>180))throw Error('Укажите материал засыпки.')}
