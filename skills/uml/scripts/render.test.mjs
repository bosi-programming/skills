import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'
import { PassThrough } from 'node:stream'
import { test } from 'node:test'

import { inflateRawSync } from 'node:zlib'

import { MISSING_JAR, NO_JAVA, createRenderer, renderLocal, renderRemote } from './render.mjs'
import { decodeBase64 } from './test-helpers.mjs'

const SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
const ERROR_SVG = ['Add your own dedication into PlantUML', 'PlantUML version 1.2026.9', '[From string (line 73) ]', 'skinparam noteFontColor #e6edf3', '[*] --&gt;', 'Syntax Error? (Assumed diagram type: sequence)']
  .map((text) => `<text x="1">${text}</text>`)
  .join('')

const fakeSpawn = ({ stdout = '', stderr = '', code = 0, error = null } = {}) => {
  const calls = []
  const spawn = (command, args) => {
    const child = new EventEmitter()
    const stdin = new PassThrough()
    const chunks = []
    stdin.on('data', (chunk) => chunks.push(chunk))
    child.stdin = stdin
    child.stdout = new PassThrough()
    child.stderr = new PassThrough()
    stdin.on('finish', () => {
      calls.push({ command, args, input: Buffer.concat(chunks).toString('utf8') })
      if (error) return child.emit('error', error)
      child.stdout.end(stdout)
      child.stderr.end(stderr)
      setImmediate(() => child.emit('close', code))
    })
    return child
  }
  return { spawn, calls }
}

const enoent = () => Object.assign(new Error('spawn java ENOENT'), { code: 'ENOENT' })

test('render: local spawns java -jar jar -tsvg -pipe with source on stdin', async () => {
  const { spawn, calls } = fakeSpawn({ stdout: SVG })
  await renderLocal('@startuml\nA -> B\n@enduml', { jar: '/j/plantuml.jar', dotPath: null, spawn })
  assert.deepEqual(calls, [{
    command: 'java',
    args: ['-jar', '/j/plantuml.jar', '-tsvg', '-pipe', '-charset', 'UTF-8'],
    input: '@startuml\nA -> B\n@enduml',
  }])
})

test('render: local passes the dot path to PlantUML when found', async () => {
  const { spawn, calls } = fakeSpawn({ stdout: SVG })
  await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: '/opt/bin/dot', spawn })
  assert.deepEqual(calls[0].args.slice(-2), ['-graphvizdot', '/opt/bin/dot'])
})

test('render: local returns the svg without the xml prolog', async () => {
  const { spawn } = fakeSpawn({ stdout: `<?xml version="1.0"?>${SVG}` })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { svg: SVG })
})

test('render: a local syntax error returns the error text', async () => {
  const { spawn } = fakeSpawn({ stdout: ERROR_SVG, code: 200 })
  const result = await renderLocal('@startuml\nA ->\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: Syntax Error? (Assumed diagram type: sequence) at "[*] -->"' })
})

test('render: a local failure with stderr returns stderr', async () => {
  const { spawn } = fakeSpawn({ stderr: 'Error: Invalid or corrupt jarfile\n', code: 1 })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: Error: Invalid or corrupt jarfile' })
})

test('render: java ENOENT gives the no-Java message naming uml.plantumlServer', async () => {
  const { spawn } = fakeSpawn({ error: enoent() })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual([result, NO_JAVA.includes('uml.plantumlServer'), NO_JAVA.includes('Java')], [{ error: NO_JAVA }, true, true])
})

test('render: missing jar gives message naming uml.plantumlJar and download-jar', async () => {
  const { spawn, calls } = fakeSpawn({ stdout: SVG })
  const result = await renderLocal('@startuml\n@enduml', { jar: null, dotPath: null, spawn })
  assert.deepEqual([result, calls, /uml\.plantumlJar/.test(MISSING_JAR), /download-jar/.test(MISSING_JAR)], [{ error: MISSING_JAR }, [], true, true])
})

test('render: remote GETs server/svg/encoded', async () => {
  const urls = []
  const fetch = async (url) => {
    urls.push(url)
    return new Response(SVG)
  }
  const result = await renderRemote('Bob -> Alice : hello', { server: 'https://plantuml.example/plantuml/', fetch })
  assert.deepEqual([result, urls], [{ svg: SVG }, ['https://plantuml.example/plantuml/svg/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000']])
})

test('render: remote syntax error returns the error text', async () => {
  const fetch = async () => new Response(ERROR_SVG, { status: 400 })
  const result = await renderRemote('A ->', { server: 'https://plantuml.example', fetch })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: Syntax Error? (Assumed diagram type: sequence) at "[*] -->"' })
})

test('render: an error svg with no error line keeps its last text', async () => {
  const { spawn } = fakeSpawn({ stdout: '<svg><text>one</text><text>Cannot find Graphviz</text></svg>', code: 200 })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: Cannot find Graphviz' })
})

test('render: remote unreachable gives one message naming the server', async () => {
  const fetch = async () => {
    throw new TypeError('fetch failed')
  }
  const result = await renderRemote('A -> B', { server: 'https://plantuml.example', fetch })
  assert.deepEqual(result, {
    error: 'Could not reach the PlantUML server at https://plantuml.example (fetch failed). Check the URL in uml.plantumlServer, or set it to local.',
  })
})

test('render: the renderer themes the source before a local render', async () => {
  const { spawn, calls } = fakeSpawn({ stdout: SVG })
  const render = createRenderer({ server: 'local', jar: '/j.jar', dotPath: null, spawn, fetch: null })
  await render('@startuml\nclass A\n@enduml', 'class')
  assert.deepEqual([calls[0].input.split('\n')[1], calls[0].input.includes('!pragma layout smetana')], ['skinparam backgroundColor #0b0e14', true])
})

test('render: the renderer sends a themed source to a remote server', async () => {
  const urls = []
  const fetch = async (url) => {
    urls.push(url)
    return new Response(SVG)
  }
  const render = createRenderer({ server: 'https://plantuml.example', jar: null, dotPath: null, spawn: null, fetch })
  await render('@startuml\nclass A\n@enduml', 'class')
  const sent = inflateRawSync(decodeBase64(urls[0].split('/svg/')[1])).toString('utf8')
  assert.deepEqual([sent.split('\n')[1], sent.includes('!pragma layout')], ['skinparam backgroundColor #0b0e14', false])
})

test('render: error text from the svg has its entities decoded', async () => {
  const { spawn } = fakeSpawn({ stdout: '<svg><text>A -&gt; &quot;B&quot; &amp; C</text><text>Syntax Error?</text></svg>', code: 200 })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: Syntax Error? at "A -> \"B\" & C"' })
})

test('render: remote returns the svg without the xml prolog', async () => {
  const fetch = async () => new Response(`<?xml version="1.0" encoding="UTF-8" standalone="no"?>${SVG}`)
  const result = await renderRemote('A -> B', { server: 'https://plantuml.example', fetch })
  assert.deepEqual(result, { svg: SVG })
})

test('render: a spawn error other than ENOENT is a render failure', async () => {
  const { spawn } = fakeSpawn({ error: Object.assign(new Error('spawn java EACCES'), { code: 'EACCES' }) })
  const result = await renderLocal('@startuml\n@enduml', { jar: '/j.jar', dotPath: null, spawn })
  assert.deepEqual(result, { error: 'PlantUML could not render this diagram: spawn java EACCES' })
})
