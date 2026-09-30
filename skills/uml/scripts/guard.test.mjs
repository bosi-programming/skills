import assert from 'node:assert/strict'
import { test } from 'node:test'

import { resolveSource } from './guard.mjs'

const manifestWith = (diagrams) => ({ origin: 'code', source: '.', diagrams })

test('guard: a manifest file inside the output folder is writable', () => {
  const manifest = manifestWith([{ type: 'class', file: 'class.puml', why: null, noBasis: null }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'class'), { path: '/repo/docs/uml/class.puml' })
})

test('guard: type not in manifest rejected', () => {
  const manifest = manifestWith([{ type: 'class', file: 'class.puml', why: null, noBasis: null }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'state'), {
    error: 'uml.json names no file for state.',
  })
})

test('guard: noBasis type rejected', () => {
  const manifest = manifestWith([{ type: 'object', file: null, why: null, noBasis: 'No instances.' }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'object'), {
    error: 'uml.json names no file for object.',
  })
})

test('guard: path escaping outputDir rejected', () => {
  const manifest = manifestWith([{ type: 'class', file: '../x.puml', why: null, noBasis: null }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'class'), {
    error: 'class file ../x.puml is outside /repo/docs/uml.',
  })
})

test('guard: an absolute path elsewhere rejected', () => {
  const manifest = manifestWith([{ type: 'class', file: '/etc/x.puml', why: null, noBasis: null }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'class'), {
    error: 'class file /etc/x.puml is outside /repo/docs/uml.',
  })
})

test('guard: a file that is not .puml rejected', () => {
  const manifest = manifestWith([{ type: 'class', file: 'class.html', why: null, noBasis: null }])
  assert.deepEqual(resolveSource('/repo/docs/uml', manifest, 'class'), {
    error: 'class file class.html is not a .puml file.',
  })
})
