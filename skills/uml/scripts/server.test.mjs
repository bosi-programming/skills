import assert from 'node:assert/strict'
import { mkdtemp, readdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { PassThrough } from 'node:stream'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { createUmlServer, listen, readBody } from './server.mjs'

const SCRIPTS = new URL('.', import.meta.url)
const SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
const CLASS_SOURCE = '@startuml\nclass Order\n@enduml\n'

let outputDir
let running

const manifest = {
  origin: 'code',
  source: 'src',
  diagrams: [
    { type: 'class', file: 'class.puml', why: null, noBasis: null },
    { type: 'object', file: null, why: null, noBasis: 'No instances.' },
    { type: 'package', file: '../escape.puml', why: null, noBasis: null },
  ],
}

const start = async ({ render = async () => ({ svg: SVG }), onRequest = () => {} } = {}) => {
  const server = createUmlServer({ outputDir, manifest, render, readFile, writeFile, smetana: false, onRequest })
  running = server
  return listen(server, { host: '127.0.0.1' })
}

const post = (url, type, body, headers = { 'Content-Type': 'application/json' }) =>
  fetch(`${url}/api/diagram/${type}`, { method: 'POST', headers, body: typeof body === 'string' ? body : JSON.stringify(body) })

beforeEach(async () => {
  outputDir = await mkdtemp(join(tmpdir(), 'uml-server-'))
  await writeFile(join(outputDir, 'class.puml'), CLASS_SOURCE)
})

afterEach(async () => {
  await new Promise((resolve) => running.close(resolve))
  await rm(outputDir, { recursive: true, force: true })
})

test('server: GET / returns the page', async () => {
  const { url } = await start()
  const response = await fetch(url)
  const html = await response.text()
  assert.deepEqual(
    [response.status, response.headers.get('content-type'), html.includes('id="class"'), html.includes('id="object"'), html.includes(SVG)],
    [200, 'text/html; charset=utf-8', true, true, true]
  )
})

test('server: the page editor holds the source from disk', async () => {
  const { url } = await start()
  const html = await (await fetch(url)).text()
  assert.ok(html.includes('class Order\n@enduml\n</textarea>'))
})

test('server: a source file that is gone shows its error in its section', async () => {
  await rm(join(outputDir, 'class.puml'))
  const { url } = await start()
  const response = await fetch(url)
  assert.deepEqual([response.status, (await response.text()).includes('Could not read class.puml')], [200, true])
})

test('server: a manifest file outside the output folder is never read', async () => {
  const reads = []
  const server = createUmlServer({
    outputDir,
    manifest,
    render: async () => ({ svg: SVG }),
    readFile: async (path, encoding) => reads.push(path) && readFile(path, encoding),
    writeFile,
    smetana: false,
    onRequest: () => {},
  })
  running = server
  const { url } = await listen(server, { host: '127.0.0.1' })
  await fetch(url)
  assert.deepEqual(reads, [join(outputDir, 'class.puml')])
})

test('server: POST writes source and returns svg', async () => {
  const { url } = await start({ render: async () => ({ svg: '<svg>new</svg>' }) })
  const response = await post(url, 'class', { source: '@startuml\nclass Cart\n@enduml\n' })
  assert.deepEqual(
    [response.status, await response.json(), await readFile(join(outputDir, 'class.puml'), 'utf8')],
    [200, { svg: '<svg>new</svg>' }, '@startuml\nclass Cart\n@enduml\n']
  )
})

test('server: the renderer gets the posted source and its type', async () => {
  const calls = []
  const { url } = await start({ render: async (source, type) => calls.push([source, type]) && { svg: SVG } })
  await post(url, 'class', { source: 'class Cart' })
  assert.deepEqual(calls, [['class Cart', 'class']])
})

test('server: file on disk holds no theme lines after write-back', async () => {
  const { url } = await start({ render: async () => ({ svg: SVG }) })
  await post(url, 'class', { source: '@startuml\nclass Cart\n@enduml\n' })
  const onDisk = await readFile(join(outputDir, 'class.puml'), 'utf8')
  assert.equal(/skinparam|!pragma/.test(onDisk), false)
})

test('server: parse error saves file and returns error', async () => {
  const { url } = await start({ render: async () => ({ error: 'Syntax Error?' }) })
  const response = await post(url, 'class', { source: 'class {' })
  assert.deepEqual([await response.json(), await readFile(join(outputDir, 'class.puml'), 'utf8')], [{ error: 'Syntax Error?' }, 'class {'])
})

test('server: after a parse error the page keeps the last good svg, dimmed', async () => {
  const replies = [{ svg: '<svg>good</svg>' }, { error: 'Syntax Error?' }]
  const { url } = await start({ render: async () => replies.shift() })
  await fetch(url)
  await post(url, 'class', { source: 'class {' })
  const html = await (await fetch(url)).text()
  assert.ok(html.includes('<div class="drawing stale"><svg>good</svg></div>'))
})

test('server: guard failure is 403 and writes nothing', async () => {
  const { url } = await start()
  const response = await post(url, 'package', { source: 'x' })
  const files = await readdir(join(outputDir, '..'))
  assert.deepEqual([response.status, files.includes('escape.puml')], [403, false])
})

test('server: a no-basis type is 403', async () => {
  const { url } = await start()
  const response = await post(url, 'object', { source: 'x' })
  assert.equal(response.status, 403)
})

test('server: a body over 1 MiB is 413 and writes nothing', async () => {
  const { url } = await start()
  const response = await post(url, 'class', { source: 'x'.repeat(1_048_577) })
  assert.deepEqual([response.status, await readFile(join(outputDir, 'class.puml'), 'utf8')], [413, CLASS_SOURCE])
})

test('server: readBody stops collecting once the body passes 1 MiB', async () => {
  const request = new PassThrough()
  const reading = readBody(request)
  request.write(Buffer.alloc(1_048_577))
  await assert.rejects(reading, { status: 413 })
  request.write(Buffer.alloc(16))
  assert.deepEqual([request.listenerCount('data'), request.readableFlowing], [0, true])
})

test('server: a body that is not JSON is 400', async () => {
  const { url } = await start()
  const response = await post(url, 'class', '{ nope')
  assert.equal(response.status, 400)
})

test('server: a body without a source string is 400', async () => {
  const { url } = await start()
  const response = await post(url, 'class', { text: 'x' })
  assert.equal(response.status, 400)
})

test('server: a POST that is not JSON typed is 415 and writes nothing', async () => {
  const { url } = await start()
  const response = await post(url, 'class', JSON.stringify({ source: 'x' }), { 'Content-Type': 'text/plain' })
  assert.deepEqual([response.status, await readFile(join(outputDir, 'class.puml'), 'utf8')], [415, CLASS_SOURCE])
})

test('server: a request for another host name is 403', async () => {
  const { port } = await start()
  const { request } = await import('node:http')
  const status = await new Promise((resolve) => {
    request({ host: '127.0.0.1', port, path: '/', headers: { Host: 'evil.example' } }, (response) => resolve(response.statusCode)).end()
  })
  assert.equal(status, 403)
})

test('server: unknown route 404', async () => {
  const { url } = await start()
  const response = await fetch(`${url}/nope`)
  assert.equal(response.status, 404)
})

test('server: binds 127.0.0.1 on an OS port', async () => {
  const { host, port, url } = await start()
  assert.deepEqual([host, port > 0, url], ['127.0.0.1', true, `http://127.0.0.1:${port}`])
})

test('server: each request touches idle', async () => {
  const onRequest = mock.fn()
  const { url } = await start({ onRequest })
  await fetch(url)
  await fetch(`${url}/nope`)
  await post(url, 'class', { source: 'x' })
  assert.equal(onRequest.mock.callCount(), 3)
})

test('server: imports only node: modules', async () => {
  const files = (await readdir(SCRIPTS)).filter((name) => name.endsWith('.mjs') && !name.endsWith('.test.mjs'))
  const texts = await Promise.all(files.map((name) => readFile(new URL(name, SCRIPTS), 'utf8')))
  const specifiers = texts.flatMap((text) => [...text.matchAll(/^import .* from '([^']+)'/gm)].map((match) => match[1]))
  assert.deepEqual(specifiers.filter((specifier) => !specifier.startsWith('node:') && !specifier.startsWith('./')), [])
})
