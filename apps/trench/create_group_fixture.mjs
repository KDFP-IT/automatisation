import {seedProject} from './dist/network-model.js';import {writeFileSync} from 'node:fs';
const p=seedProject();p.name='Проверка стены и группы 6.1';const w=p.wells[2];Object.assign(w,{shape:'rect',width:2,length:2,rotationMode:'manual',rotation:17});writeFileSync('group-fixture.json',JSON.stringify(p));
