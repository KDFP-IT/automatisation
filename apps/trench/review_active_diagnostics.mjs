import {readFileSync} from 'node:fs';import {calculateNetwork} from './dist/network-model.js';
const p=JSON.parse(readFileSync('diagnostics-current.json','utf8')),r=calculateNetwork(p);console.log(JSON.stringify(r.issues.filter(v=>v.severity==='error').map(v=>({code:v.code,kind:v.kind,message:v.message})),null,2));
