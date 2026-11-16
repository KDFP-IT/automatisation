import assert from 'node:assert/strict'
import fs from 'node:fs'
import test from 'node:test'

const canonical = new URL('../../../../packages/tokens/tokens.css', import.meta.url)
const copies = {
  'apps/kac/ui': new URL('../src/assets/tokens.css', import.meta.url),
  'apps/portal': new URL('../../../../apps/portal/src/assets/tokens.css', import.meta.url)
}

test('vendored tokens match the canonical file', () => {
  const source = fs.readFileSync(canonical, 'utf8')
  for (const [name, path] of Object.entries(copies)) {
    assert.equal(fs.readFileSync(path, 'utf8'), source, name)
  }
})

test('canonical tokens define the brand ramp and typography', () => {
  const css = fs.readFileSync(canonical, 'utf8')
  for (const name of ['--k-font-sans', '--k-brand-500', '--k-ink', '--k-paper', '--k-focus-color']) {
    assert.match(css, new RegExp(`${name}:`), name)
  }
})
