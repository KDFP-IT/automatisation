import test from 'node:test'
import assert from 'node:assert/strict'
import { loadTools, loadAuth, login, logout } from '../src/tools.js'

test('catalog retains resolved iframe URLs and embedding policy', async () => {
  globalThis.location = { origin: 'https://portal.example' }
  globalThis.fetch = async () => Response.json([
    { id: 'trench', title: 'Траншеи', url: '/trench/', embed: true },
    { id: 'other', title: 'Другой', url: 'https://other.example/', embed: true }
  ])
  const tools = await loadTools()
  assert.equal(tools[0].url, 'https://portal.example/trench/')
  assert.equal(tools[0].embed, true)
  assert.equal(tools[1].embed, false)
})

test('AD session retains display name, tool permissions and admin flag', async () => {
  globalThis.fetch = async url => Response.json(url === '/auth/mode'
    ? { mode: 'ldap' }
    : { user: 'user', display_name: 'Иван Иванов', tools: ['bookmarks'], admin: true })
  assert.deepEqual(await loadAuth(), {
    mode: 'ldap', user: 'user', displayName: 'Иван Иванов', tools: ['bookmarks'], admin: true
  })
})

test('expired session grants no tools', async () => {
  globalThis.fetch = async url => url === '/auth/mode'
    ? Response.json({ mode: 'ldap' }) : new Response('', { status: 401 })
  assert.deepEqual(await loadAuth(), { mode: 'ldap', user: null, tools: [] })
})

test('login and logout keep existing auth endpoints and methods', async () => {
  const requests = []
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options })
    return Response.json({ user: 'user', display_name: 'Иван Иванов', tools: ['trench'] })
  }
  assert.equal((await login('user', 'test-password')).displayName, 'Иван Иванов')
  await logout()
  assert.equal(requests[0].url, '/auth/login')
  assert.equal(requests[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(requests[0].options.body), { login: 'user', password: 'test-password' })
  assert.equal(requests[1].url, '/auth/logout')
  assert.equal(requests[1].options.method, 'POST')
})
