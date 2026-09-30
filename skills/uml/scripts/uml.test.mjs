import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'
import { connect } from 'node:net'
import { PassThrough } from 'node:stream'
import { test } from 'node:test'

import { NO_JAVA } from './render.mjs'
import { openerFor, run } from './uml.mjs'

const MANIFEST = JSON.stringify({ origin: 'code', source: '.', diagrams: [{ type: 'class', file: 'class.puml', why: null, noBasis: null }] })

const enoent = () => Object.assign(new Error('missing'), { code: 'ENOENT' })

const fakeChild = ({ pid = 4242, line = null } = {}) => {
  const child = new EventEmitter()
  child.pid = pid
  child.stdout = new PassThrough()
  child.unref = () => {
    child.unrefed = true
  }
  if (line) setImmediate(() => child.stdout.write(`${line}\n`))
  return child
}

const deps = (overrides = {}) => {
  const out = []
  const err = []
  const spawned = []
  const base = {
    stdout: (text) => out.push(text),
    stderr: (text) => err.push(text),
    cwd: '/repo',
    env: { PATH: '/usr/bin' },
    homedir: '/home/ana',
    platform: 'linux',
    scriptPath: '/skill/scripts/uml.mjs',
    execPath: '/usr/bin/node',
    exists: () => false,
    readFile: async () => MANIFEST,
    writeFile: async () => {},
    mkdir: async () => {},
    spawnSync: () => ({ status: 0 }),
    spawn: (command, args, options) => {
      spawned.push({ command, args, options })
      return fakeChild({ line: command === '/usr/bin/node' ? JSON.stringify({ url: 'http://127.0.0.1:5123' }) : null })
    },
    fetch: async () => new Response('jar'),
    ...overrides,
  }
  return { deps: base, out, err, spawned }
}

const jsonOut = (out) => JSON.parse(out.join(''))

test('uml: check prints the parsed invocation as JSON', async () => {
  const { deps: d, out } = deps()
  const code = await run(['check', '--diagrams=state,class'], d)
  assert.deepEqual([code, jsonOut(out)], [0, { mode: 'repo', target: null, diagrams: ['class', 'state'], regenerate: false }])
})

test('uml: check resolves a path against the working folder', async () => {
  const checked = []
  const { deps: d, out } = deps({ exists: (path) => checked.push(path) })
  await run(['check', 'src/orders'], d)
  assert.deepEqual([checked, jsonOut(out).mode], [['/repo/src/orders'], 'path'])
})

test('uml: check exits non-zero on error', async () => {
  const { deps: d, err } = deps()
  const code = await run(['check', '--diagrams=activity'], d)
  assert.deepEqual([code, /Unknown diagram type: activity/.test(err.join(''))], [1, true])
})

test('uml: status reports java, dot, jar and manifest state as JSON', async () => {
  const { deps: d, out } = deps({
    exists: (path) => ['/usr/bin/dot', '/home/ana/.cache/bosi-skills/uml/plantuml.jar'].includes(path),
  })
  await run(['status', '--output-dir', 'docs/uml', '--jar', '', '--server', 'local'], d)
  assert.deepEqual(jsonOut(out), {
    manifest: 'ok',
    manifestError: null,
    server: 'local',
    java: true,
    dot: '/usr/bin/dot',
    layout: 'graphviz',
    jar: '/home/ana/.cache/bosi-skills/uml/plantuml.jar',
    jarCachePath: '/home/ana/.cache/bosi-skills/uml/plantuml.jar',
  })
})

test('uml: status reads the manifest from the output folder', async () => {
  const paths = []
  const { deps: d } = deps({ readFile: async (path) => paths.push(path) && MANIFEST })
  await run(['status', '--output-dir', 'docs/uml'], d)
  assert.deepEqual(paths, ['/repo/docs/uml/uml.json'])
})

test('uml: status manifest missing', async () => {
  const { deps: d, out } = deps({ readFile: async () => { throw enoent() } })
  await run(['status', '--output-dir', 'docs/uml'], d)
  assert.equal(jsonOut(out).manifest, 'missing')
})

test('uml: status manifest unreadable', async () => {
  const { deps: d, out } = deps({ readFile: async () => '{' })
  await run(['status', '--output-dir', 'docs/uml'], d)
  assert.equal(jsonOut(out).manifest, 'unreadable')
})

test('uml: status with no java and no dot', async () => {
  const { deps: d, out } = deps({ spawnSync: () => ({ status: 1 }) })
  await run(['status'], d)
  const status = jsonOut(out)
  assert.deepEqual([status.java, status.dot, status.layout, status.jar], [false, null, 'smetana', null])
})

test('uml: download-jar writes to the cache path', async () => {
  const written = []
  const { deps: d, out } = deps({ writeFile: async (path) => written.push(path) })
  const code = await run(['download-jar'], d)
  assert.deepEqual([code, written, jsonOut(out)], [0, ['/home/ana/.cache/bosi-skills/uml/plantuml.jar'], { path: '/home/ana/.cache/bosi-skills/uml/plantuml.jar' }])
})

test('uml: download-jar writes to the configured jar path', async () => {
  const written = []
  const { deps: d } = deps({ writeFile: async (path) => written.push(path) })
  await run(['download-jar', '--jar', '~/tools/plantuml.jar'], d)
  assert.deepEqual(written, ['/home/ana/tools/plantuml.jar'])
})

test('uml: a failed download exits non-zero with the reason', async () => {
  const { deps: d, err } = deps({ fetch: async () => new Response('', { status: 503 }) })
  const code = await run(['download-jar'], d)
  assert.deepEqual([code, /HTTP 503/.test(err.join(''))], [1, true])
})

test('uml: serve prints url, pid and stop command and opens browser', async () => {
  const { deps: d, out } = deps({ exists: () => true })
  const code = await run(['serve', '--output-dir', 'docs/uml', '--jar', '', '--server', 'local', '--idle-minutes', '15'], d)
  const text = out.join('')
  assert.deepEqual(
    [code, text.includes('http://127.0.0.1:5123'), text.includes('4242'), text.includes('kill 4242'), text.includes('15 minutes')],
    [0, true, true, true, true]
  )
})

test('uml: serve starts a detached foreground child with the same settings', async () => {
  const { deps: d, spawned } = deps({ exists: () => true })
  await run(['serve', '--output-dir', 'docs/uml', '--jar', '', '--server', 'local', '--idle-minutes', '15'], d)
  assert.deepEqual([spawned[0].command, spawned[0].args, spawned[0].options.detached], [
    '/usr/bin/node',
    ['/skill/scripts/uml.mjs', 'serve-foreground', '--output-dir', '/repo/docs/uml', '--jar', '/home/ana/.cache/bosi-skills/uml/plantuml.jar', '--server', 'local', '--idle-minutes', '15'],
    true,
  ])
})

test('uml: serve opens the page in the browser', async () => {
  const { deps: d, spawned } = deps({ exists: () => true })
  await run(['serve'], d)
  assert.deepEqual([spawned[1].command, spawned[1].args], ['xdg-open', ['http://127.0.0.1:5123']])
})

test('uml: serve still reports the URL when no browser opener exists', async () => {
  const children = []
  const spawn = (command) => {
    const child = fakeChild({ line: command === '/usr/bin/node' ? JSON.stringify({ url: 'http://127.0.0.1:5123' }) : null })
    children.push(child)
    if (command !== '/usr/bin/node') setImmediate(() => child.emit('error', Object.assign(new Error('spawn xdg-open ENOENT'), { code: 'ENOENT' })))
    return child
  }
  const { deps: d, out } = deps({ exists: () => true, spawn })
  const code = await run(['serve'], d)
  await new Promise((resolve) => setImmediate(resolve))
  assert.deepEqual([code, out.join('').includes('http://127.0.0.1:5123')], [0, true])
})

test('uml: serve with no java in local mode stops with the no-Java message', async () => {
  const { deps: d, err, spawned } = deps({ exists: () => true, spawnSync: () => ({ status: 1 }) })
  const code = await run(['serve'], d)
  assert.deepEqual([code, err.join('').trim(), spawned], [1, NO_JAVA, []])
})

test('uml: serve with a missing manifest stops and says so', async () => {
  const { deps: d, err } = deps({ exists: () => true, readFile: async () => { throw enoent() } })
  const code = await run(['serve'], d)
  assert.deepEqual([code, /uml\.json/.test(err.join(''))], [1, true])
})

test('uml: serve against a remote server needs no java', async () => {
  const { deps: d, spawned } = deps({ spawnSync: () => ({ status: 1 }) })
  const code = await run(['serve', '--server', 'https://plantuml.example'], d)
  assert.deepEqual([code, spawned[0].args.includes('https://plantuml.example')], [0, true])
})

test('uml: a child that dies before it reports a URL is an error', async () => {
  const child = fakeChild()
  setImmediate(() => child.emit('exit', 1))
  const { deps: d, err } = deps({ exists: () => true, spawn: () => child })
  const code = await run(['serve'], d)
  assert.deepEqual([code, /page server stopped before it started/.test(err.join(''))], [1, true])
})

const foreground = async () => {
  const { deps: d, out } = deps({ fetch: async () => new Response('<svg/>') })
  const code = await run(['serve-foreground', '--server', 'https://plantuml.example', '--idle-minutes', '1'], d)
  return { code, url: new URL(JSON.parse(out.join('')).url) }
}

const refuses = (port) =>
  new Promise((resolve) => {
    const socket = connect(port, '127.0.0.1')
    socket.once('connect', () => socket.destroy() && resolve(false))
    socket.once('error', () => resolve(true))
  })

test('uml: serve-foreground listens on 127.0.0.1', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  const { code, url } = await foreground()
  context.mock.timers.tick(60_000)
  assert.deepEqual([code, url.hostname, Number(url.port) > 0], [0, '127.0.0.1', true])
})

test('uml: serve-foreground stops after the idle minutes', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  const { url } = await foreground()
  context.mock.timers.tick(60_000)
  context.mock.timers.reset()
  assert.equal(await refuses(Number(url.port)), true)
})

test('uml: an unknown subcommand prints usage', async () => {
  const { deps: d, err } = deps()
  const code = await run(['draw'], d)
  assert.deepEqual([code, /Usage: uml\.mjs/.test(err.join(''))], [2, true])
})

test('uml: browser opener on macOS is open', () => {
  assert.deepEqual(openerFor('darwin', 'http://x'), { command: 'open', args: ['http://x'] })
})

test('uml: browser opener on Linux is xdg-open', () => {
  assert.deepEqual(openerFor('linux', 'http://x'), { command: 'xdg-open', args: ['http://x'] })
})

test('uml: browser opener on Windows is start', () => {
  assert.deepEqual(openerFor('win32', 'http://x'), { command: 'cmd', args: ['/c', 'start', '', 'http://x'] })
})
