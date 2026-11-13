import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,randomBytes} from 'node:crypto';
import {digestHex} from '../dist/vendor/hash.mjs';
for(const algorithm of ['SHA-1','SHA-256','SHA-384','SHA-512'])test(`${algorithm}: HTTP fallback matches native implementation`,async()=>{
 for(const bytes of [new Uint8Array(),new TextEncoder().encode('abc'),new TextEncoder().encode('КДФП'),randomBytes(131073)])assert.equal(await digestHex(algorithm,bytes,{native:false}),createHash(algorithm.toLowerCase().replace('-','')).update(bytes).digest('hex'));
});
test('fallback hashes only the selected typed-array slice',async()=>{
 const bytes=new Uint8Array([1,2,3,4,5]).subarray(1,4);assert.equal(await digestHex('SHA-256',bytes,{native:false}),createHash('sha256').update(bytes).digest('hex'));
});
