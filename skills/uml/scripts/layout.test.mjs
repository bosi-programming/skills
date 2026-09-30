import assert from 'node:assert/strict'
import { test } from 'node:test'

import { chooseLayout, findOnPath } from './layout.mjs'

test('layout: dot found means graphviz', () => {
  assert.equal(chooseLayout({ dotPath: '/usr/bin/dot', server: 'local' }), 'graphviz')
})

test('layout: dot missing means smetana', () => {
  assert.equal(chooseLayout({ dotPath: null, server: 'local' }), 'smetana')
})

test('layout: a remote server lays out with its own graphviz', () => {
  assert.equal(chooseLayout({ dotPath: null, server: 'https://plantuml.example' }), 'graphviz')
})

test('layout: findOnPath returns the first folder holding the command', () => {
  const found = findOnPath('dot', {
    pathEnv: '/usr/bin:/opt/homebrew/bin',
    exists: (path) => path === '/opt/homebrew/bin/dot',
    platform: 'darwin',
  })
  assert.equal(found, '/opt/homebrew/bin/dot')
})

test('layout: findOnPath returns null when no folder holds it', () => {
  assert.equal(findOnPath('dot', { pathEnv: '/usr/bin', exists: () => false, platform: 'linux' }), null)
})

test('layout: findOnPath tries .exe on Windows', () => {
  const found = findOnPath('dot', { pathEnv: 'C:\\bin', exists: (path) => path.endsWith('dot.exe'), platform: 'win32' })
  assert.equal(found, 'C:\\bin\\dot.exe')
})
