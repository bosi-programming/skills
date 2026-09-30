import assert from 'node:assert/strict'
import { test } from 'node:test'

import { JAR_RELEASE_URL, cachedJarPath, downloadJar, hasJava, locateJar } from './jar.mjs'

const HOME = '/home/ana'

test('jar: configured path wins', () => {
  const found = locateJar({ configured: '/opt/plantuml.jar', env: {}, homedir: HOME, exists: () => true })
  assert.equal(found, '/opt/plantuml.jar')
})

test('jar: a configured path under ~ is expanded', () => {
  const found = locateJar({ configured: '~/tools/plantuml.jar', env: {}, homedir: HOME, exists: () => true })
  assert.equal(found, '/home/ana/tools/plantuml.jar')
})

test('jar: empty config uses XDG cache path', () => {
  assert.equal(cachedJarPath({ env: { XDG_CACHE_HOME: '/xdg' }, homedir: HOME }), '/xdg/bosi-skills/uml/plantuml.jar')
})

test('jar: no XDG uses ~/.cache path', () => {
  assert.equal(cachedJarPath({ env: {}, homedir: HOME }), '/home/ana/.cache/bosi-skills/uml/plantuml.jar')
})

test('jar: empty config finds the jar in the cache', () => {
  const found = locateJar({ configured: '', env: {}, homedir: HOME, exists: (path) => path.endsWith('.cache/bosi-skills/uml/plantuml.jar') })
  assert.equal(found, '/home/ana/.cache/bosi-skills/uml/plantuml.jar')
})

test('jar: missing jar returns null', () => {
  assert.equal(locateJar({ configured: '', env: {}, homedir: HOME, exists: () => false }), null)
})

test('jar: a configured jar that does not exist returns null', () => {
  assert.equal(locateJar({ configured: '/opt/none.jar', env: {}, homedir: HOME, exists: () => false }), null)
})

test('jar: release URL points at PlantUML GitHub releases', () => {
  assert.equal(JAR_RELEASE_URL, 'https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar')
})

test('jar: download writes to cache path via injected fetch, following redirects', async () => {
  const requests = []
  const written = []
  const result = await downloadJar({
    dest: '/cache/bosi-skills/uml/plantuml.jar',
    fetch: async (url, options) => {
      requests.push([url, options.redirect])
      return new Response(new Uint8Array([80, 75, 3, 4]))
    },
    mkdir: async () => {},
    writeFile: async (path, bytes) => written.push([path, [...bytes]]),
  })
  assert.deepEqual([result, requests, written], [
    { path: '/cache/bosi-skills/uml/plantuml.jar' },
    [[JAR_RELEASE_URL, 'follow']],
    [['/cache/bosi-skills/uml/plantuml.jar', [80, 75, 3, 4]]],
  ])
})

test('jar: download creates the cache folder', async () => {
  const folders = []
  await downloadJar({
    dest: '/cache/bosi-skills/uml/plantuml.jar',
    fetch: async () => new Response('jar'),
    mkdir: async (path, options) => folders.push([path, options.recursive]),
    writeFile: async () => {},
  })
  assert.deepEqual(folders, [['/cache/bosi-skills/uml', true]])
})

test('jar: a failed download names the status and writes nothing', async () => {
  const written = []
  const result = await downloadJar({
    dest: '/cache/plantuml.jar',
    fetch: async () => new Response('gone', { status: 404 }),
    mkdir: async () => {},
    writeFile: async (path) => written.push(path),
  })
  assert.deepEqual([result, written], [
    { error: `Could not download the PlantUML jar from ${JAR_RELEASE_URL} (HTTP 404). Download it by hand and set uml.plantumlJar to its path.` },
    [],
  ])
})

test('jar: an unreachable release names the network', async () => {
  const result = await downloadJar({
    dest: '/cache/plantuml.jar',
    fetch: async () => {
      throw new TypeError('fetch failed')
    },
    mkdir: async () => {},
    writeFile: async () => {},
  })
  assert.equal(result.error, `Could not reach ${JAR_RELEASE_URL} (fetch failed). Check the network, or download the jar by hand and set uml.plantumlJar to its path.`)
})

test('jar: java is found when java -version exits 0', () => {
  assert.equal(hasJava({ spawnSync: () => ({ status: 0 }) }), true)
})

test('jar: the macOS java stub that exits 1 is no java', () => {
  assert.equal(hasJava({ spawnSync: () => ({ status: 1 }) }), false)
})

test('jar: no java binary at all is no java', () => {
  assert.equal(hasJava({ spawnSync: () => ({ status: null, error: new Error('ENOENT') }) }), false)
})
