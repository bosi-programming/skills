import assert from 'node:assert/strict'
import { resolve } from 'node:path'
import { test } from 'node:test'

import { planSources } from './plan.mjs'

const resolvePath = (path) => resolve('/repo', path)

const entry = (type) => ({ type, file: `${type}.puml`, why: type === 'class' ? null : 'Checkout.', noBasis: null })

const onDisk = (overrides = {}) => ({
  state: 'ok',
  manifest: { origin: 'code', source: '.', diagrams: ['class', 'state'].map(entry), ...overrides },
})

const asked = (overrides = {}) => ({ mode: 'repo', target: null, diagrams: ['class', 'state'], regenerate: false, ...overrides })

const plan = (invocation, manifest) => planSources({ invocation, manifest, resolvePath })

test('plan: the same request reuses the sources on disk', () => {
  assert.deepEqual(plan(asked(), onDisk()), { sources: 'reuse', reason: null })
})

test('plan: --regenerate writes new sources', () => {
  assert.deepEqual(plan(asked({ regenerate: true }), onDisk()), { sources: 'write', reason: '--regenerate was given.' })
})

test('plan: a missing manifest writes sources', () => {
  assert.deepEqual(plan(asked(), { state: 'missing' }), { sources: 'write', reason: 'uml.json is missing.' })
})

test('plan: an unreadable manifest writes sources and quotes why', () => {
  assert.deepEqual(plan(asked(), { state: 'unreadable', error: 'uml.json: diagrams must be a list.' }), {
    sources: 'write',
    reason: 'uml.json is unreadable: uml.json: diagrams must be a list.',
  })
})

test('plan: other diagrams than the manifest holds writes sources', () => {
  assert.deepEqual(plan(asked({ diagrams: ['class'] }), onDisk()), {
    sources: 'write',
    reason: 'uml.json holds class, state, but this run asks for class.',
  })
})

test('plan: a path other than the manifest source writes sources', () => {
  assert.deepEqual(plan(asked({ mode: 'path', target: 'src/orders' }), onDisk()), {
    sources: 'write',
    reason: 'uml.json was drawn from the code in ., but this run asks for the code in src/orders.',
  })
})

test('plan: the same path written another way reuses', () => {
  const manifest = onDisk({ source: 'src/orders' })
  assert.deepEqual(plan(asked({ mode: 'path', target: './src/orders/' }), manifest), { sources: 'reuse', reason: null })
})

test('plan: a description run over code sources writes sources', () => {
  assert.deepEqual(plan(asked({ mode: 'description', target: 'a shop' }), onDisk()), {
    sources: 'write',
    reason: 'uml.json was drawn from the code in ., but this run asks for the description "a shop".',
  })
})

test('plan: another description writes sources', () => {
  const manifest = onDisk({ origin: 'description', source: 'a shop' })
  assert.deepEqual(plan(asked({ mode: 'description', target: 'a bank' }), manifest), {
    sources: 'write',
    reason: 'uml.json was drawn from the description "a shop", but this run asks for the description "a bank".',
  })
})

test('plan: the same description reuses', () => {
  const manifest = onDisk({ origin: 'description', source: 'a shop' })
  assert.deepEqual(plan(asked({ mode: 'description', target: 'a shop' }), manifest), { sources: 'reuse', reason: null })
})
