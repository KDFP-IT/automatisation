// Rebuild from installed, MIT-licensed hash.js packages; no downloads or runtime dependencies.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const modulesRoot=path.resolve(process.argv[2]||'node_modules');
const packages=['hash.js','inherits','minimalistic-assert'];
const roots=packages.map(name=>path.join(modulesRoot,name));
const modules=[],ids=new Map();
function visit(file){
 file=fs.realpathSync(file);if(!roots.some(root=>file.startsWith(fs.realpathSync(root)+path.sep)))throw Error('Unexpected dependency outside hash packages');
 if(ids.has(file))return ids.get(file);
 const id=modules.length;ids.set(file,id);const source=fs.readFileSync(file,'utf8'),entry={source,map:{}};modules.push(entry);
 for(const match of source.matchAll(/require\(['"]([^'"]+)['"]\)/g)){
  const spec=match[1],resolved=spec==='inherits'?path.join(modulesRoot,'inherits','inherits_browser.js'):createRequire(file).resolve(spec);
  entry.map[spec]=visit(resolved);
 }return id;
}
visit(path.join(modulesRoot,'hash.js','lib','hash.js'));
const output=`// Bundled hash.js 1.1.7 and MIT dependencies; licenses: HASH-LICENSES.txt.\nconst modules=[\n${modules.map(m=>`[function(module,exports,require){\n${m.source}\n},${JSON.stringify(m.map)}]`).join(',\n')}\n];
const cache=new Map();
function load(id){if(cache.has(id))return cache.get(id).exports;const module={exports:{}};cache.set(id,module);const [fn,map]=modules[id];fn(module,module.exports,spec=>{if(!(spec in map))throw Error('Unknown hash dependency');return load(map[spec]);});return module.exports;}
const hashes=load(0);
export async function digestBytes(algorithm,input,{native=true}={}){
 const bytes=input instanceof Uint8Array?input:ArrayBuffer.isView(input)?new Uint8Array(input.buffer,input.byteOffset,input.byteLength):new Uint8Array(input);
 const name={'SHA-1':'sha1','SHA-256':'sha256','SHA-384':'sha384','SHA-512':'sha512'}[algorithm];if(!name)throw Error('Unsupported hash algorithm: '+algorithm);
 if(native&&globalThis.crypto?.subtle){try{return new Uint8Array(await globalThis.crypto.subtle.digest(algorithm,bytes));}catch{}}
 const hash=hashes[name]();for(let offset=0;offset<bytes.length;offset+=65536){hash.update(bytes.subarray(offset,offset+65536));if(offset>0&&offset%1048576===0)await new Promise(resolve=>setTimeout(resolve,0));}return new Uint8Array(hash.digest());
}
export async function digestHex(algorithm,input,options){return Array.from(await digestBytes(algorithm,input,options),n=>n.toString(16).padStart(2,'0')).join('');}
`;
fs.writeFileSync('dist/vendor/hash.mjs',output);
const licenses=packages.map(name=>{const root=path.join(modulesRoot,name),pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')),license=['LICENSE','LICENSE-MIT','LICENSE.txt'].map(n=>path.join(root,n)).find(p=>fs.existsSync(p));const readme=path.join(root,'README.md');const licenseText=license?fs.readFileSync(license,'utf8'):fs.readFileSync(readme,'utf8').split('#### LICENSE')[1];if(!licenseText)throw Error('Missing license: '+name);return `${name} ${pkg.version}\n${pkg.homepage||JSON.stringify(pkg.repository)}\n\n${licenseText}`;});
fs.writeFileSync('dist/vendor/HASH-LICENSES.txt',licenses.join('\n\n----------------\n\n'));
console.log(`Bundled ${modules.length} hash modules; ${Buffer.byteLength(output)} bytes`);
