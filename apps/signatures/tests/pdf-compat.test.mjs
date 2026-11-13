import test from 'node:test';
import assert from 'node:assert/strict';

function pdf(trailerId = '') {
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>',
  ];
  let data = '%PDF-1.4\n', offsets = [0];
  for (const [i, body] of objects.entries()) {
    offsets.push(data.length);
    data += `${i + 1} 0 obj\n${body}\nendobj\n`;
  }
  const xref = data.length;
  data += 'xref\n0 4\n0000000000 65535 f \n';
  data += offsets.slice(1).map(n => `${String(n).padStart(10, '0')} 00000 n \n`).join('');
  data += `trailer\n<< /Size 4 /Root 1 0 R ${trailerId} >>\nstartxref\n${xref}\n%%EOF\n`;
  return new TextEncoder().encode(data);
}

test('PDF opens without toHex: original, modified and generated fingerprints', async () => {
  const originalHex = Object.getOwnPropertyDescriptor(Uint8Array.prototype, 'toHex');
  const originalMatrix = globalThis.DOMMatrix;
  // Text-only Node test: rendering APIs are not used.
  globalThis.DOMMatrix ??= class {};
  Object.defineProperty(Uint8Array.prototype, 'toHex', {value: undefined, configurable: true});
  try {
    const {getDocument} = await import('../dist/vendor/pdf.mjs');
    for (const id of ['', '/ID [<000102030405060708090a0b0c0d0e0f> <101112131415161718191a1b1c1d1e1f>]', '/ID [<000102030405060708090a0b0c0d0e0f> <000102030405060708090a0b0c0d0e0f>]']) {
      const doc = await getDocument({data: pdf(id), isEvalSupported: false}).promise;
      try {
        assert.equal(doc.numPages, 1);
        assert.match(doc.fingerprints[0], /^[0-9a-f]{32}$/);
        assert.equal((await doc.getPage(1)).pageNumber, 1);
        if (id) assert.equal(doc.fingerprints[0], '000102030405060708090a0b0c0d0e0f');
        assert.equal(doc.fingerprints[1], id.includes('101112') ? '101112131415161718191a1b1c1d1e1f' : null);
      } finally { await doc.destroy(); }
    }
  } finally {
    if (originalHex) Object.defineProperty(Uint8Array.prototype, 'toHex', originalHex);
    else delete Uint8Array.prototype.toHex;
    if (originalMatrix) globalThis.DOMMatrix = originalMatrix;
    else delete globalThis.DOMMatrix;
  }
});
