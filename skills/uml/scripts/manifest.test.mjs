import assert from 'node:assert/strict'
import { test } from 'node:test'

import { readManifest, validateManifest } from './manifest.mjs'

const drawn = (type, extra = {}) => ({ type, file: `${type}.puml`, why: null, noBasis: null, ...extra })

const valid = (diagrams) => ({ origin: 'code', source: 'src', diagrams })

const enoent = () => {
  const error = new Error('no such file')
  error.code = 'ENOENT'
  throw error
}

test('manifest: a valid manifest is accepted', () => {
  const result = validateManifest(valid([drawn('class')]))
  assert.equal(result.ok, true)
})

test('manifest: origin must be code or description', () => {
  const result = validateManifest({ ...valid([drawn('class')]), origin: 'guess' })
  assert.equal(result.error, 'uml.json: origin must be "code" or "description", got "guess".')
})

test('manifest: diagrams must be a list', () => {
  const result = validateManifest({ origin: 'code', source: 'src' })
  assert.equal(result.error, 'uml.json: diagrams must be a list.')
})

test('manifest: sequence without why rejected', () => {
  const result = validateManifest(valid([drawn('sequence')]))
  assert.equal(result.error, 'uml.json: sequence needs a "why" naming the flow or entity chosen and why.')
})

test('manifest: state without why rejected', () => {
  const result = validateManifest(valid([drawn('state')]))
  assert.equal(result.error, 'uml.json: state needs a "why" naming the flow or entity chosen and why.')
})

test('manifest: a no-basis sequence needs no why', () => {
  const result = validateManifest(valid([drawn('sequence', { file: null, noBasis: 'No flows.' })]))
  assert.equal(result.ok, true)
})

test('manifest: unknown type rejected', () => {
  const result = validateManifest(valid([drawn('activity')]))
  assert.equal(result.error, 'uml.json: unknown diagram type "activity".')
})

test('manifest: duplicate type rejected', () => {
  const result = validateManifest(valid([drawn('class'), drawn('class')]))
  assert.equal(result.error, 'uml.json: class is listed twice.')
})

test('manifest: file with noBasis rejected', () => {
  const result = validateManifest(valid([drawn('class', { noBasis: 'Nothing here.' })]))
  assert.equal(result.error, 'uml.json: class has both a file and a noBasis note; a no-basis diagram has file null.')
})

test('manifest: a drawn diagram without a file rejected', () => {
  const result = validateManifest(valid([drawn('class', { file: null })]))
  assert.equal(result.error, 'uml.json: class needs a file or a noBasis note.')
})

test('manifest: sections returned in page order', () => {
  const result = validateManifest(valid([drawn('state', { why: 'Order lifecycle.' }), drawn('class')]))
  assert.deepEqual(result.manifest.diagrams.map((diagram) => diagram.type), ['class', 'state'])
})

test('manifest: missing file reported as missing', async () => {
  const result = await readManifest('/out', { readFile: async () => enoent() })
  assert.deepEqual(result, { state: 'missing' })
})

test('manifest: bad JSON reported as unreadable', async () => {
  const result = await readManifest('/out', { readFile: async () => '{ not json' })
  assert.equal(result.state, 'unreadable')
})

test('manifest: an invalid schema is reported as unreadable with the reason', async () => {
  const result = await readManifest('/out', { readFile: async () => JSON.stringify({ origin: 'code', source: '' }) })
  assert.deepEqual(result, { state: 'unreadable', error: 'uml.json: diagrams must be a list.' })
})

test('manifest: reads uml.json from the output folder', async () => {
  const paths = []
  await readManifest('/out', {
    readFile: async (path) => {
      paths.push(path)
      return JSON.stringify(valid([drawn('class')]))
    },
  })
  assert.deepEqual(paths, ['/out/uml.json'])
})

test('manifest: an ok read returns the ordered manifest', async () => {
  const result = await readManifest('/out', {
    readFile: async () => JSON.stringify(valid([drawn('package'), drawn('class')])),
  })
  assert.deepEqual([result.state, result.manifest.diagrams.map((diagram) => diagram.type)], ['ok', ['class', 'package']])
})
