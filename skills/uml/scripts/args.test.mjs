import assert from 'node:assert/strict'
import { test } from 'node:test'

import { DIAGRAM_TYPES, parseInvocation } from './args.mjs'

const NINE = ['class', 'sequence', 'state', 'profile', 'composite', 'component', 'deployment', 'object', 'package']
const nothingExists = () => false
const everythingExists = () => true

test('args: no text is repo mode', () => {
  const result = parseInvocation([], { exists: nothingExists })
  assert.equal(result.mode, 'repo')
})

test('args: existing path is path mode', () => {
  const result = parseInvocation(['src/orders'], { exists: everythingExists })
  assert.deepEqual([result.mode, result.target], ['path', 'src/orders'])
})

test('args: free text is description mode', () => {
  const result = parseInvocation(['an order service with carts'], { exists: nothingExists })
  assert.deepEqual([result.mode, result.target], ['description', 'an order service with carts'])
})

test('args: flags are pulled out of the text', () => {
  const result = parseInvocation(['--diagrams=class', 'a', 'shop'], { exists: nothingExists })
  assert.deepEqual([result.mode, result.target, result.diagrams], ['description', 'a shop', ['class']])
})

test('args: no flag selects nine in page order', () => {
  const result = parseInvocation([], { exists: nothingExists })
  assert.deepEqual(result.diagrams, NINE)
})

test('args: the exported types are the nine in page order', () => {
  assert.deepEqual(DIAGRAM_TYPES, NINE)
})

test('args: activity is unknown', () => {
  const result = parseInvocation(['--diagrams=activity'], { exists: nothingExists })
  assert.match(result.error, /Unknown diagram type: activity/)
})

test('args: usecase is unknown', () => {
  const result = parseInvocation(['--diagrams=usecase'], { exists: nothingExists })
  assert.match(result.error, /Unknown diagram type: usecase/)
})

test('args: subset in page order', () => {
  const result = parseInvocation(['--diagrams=package,class'], { exists: nothingExists })
  assert.deepEqual(result.diagrams, ['class', 'package'])
})

test('args: duplicates dropped', () => {
  const result = parseInvocation(['--diagrams=class,class'], { exists: nothingExists })
  assert.deepEqual(result.diagrams, ['class'])
})

test('args: diagrams flag also takes a separate value', () => {
  const result = parseInvocation(['--diagrams', 'state,sequence'], { exists: nothingExists })
  assert.deepEqual(result.diagrams, ['sequence', 'state'])
})

test('args: unknown name lists valid names', () => {
  const result = parseInvocation(['--diagrams=class,flow'], { exists: nothingExists })
  assert.equal(
    result.error,
    'Unknown diagram type: flow. Valid types: class, sequence, state, profile, composite, component, deployment, object, package.'
  )
})

test('args: unknown name checked before path', () => {
  const calls = []
  parseInvocation(['--diagrams=flow', './src'], { exists: (path) => calls.push(path) })
  assert.deepEqual(calls, [])
})

test('args: missing path-like argument stops naming it', () => {
  const result = parseInvocation(['./nope'], { exists: nothingExists })
  assert.equal(result.error, 'Path not found: ./nope')
})

test('args: a single token with a slash is path-like', () => {
  const result = parseInvocation(['src/missing'], { exists: nothingExists })
  assert.equal(result.error, 'Path not found: src/missing')
})

test('args: a home path is path-like', () => {
  const result = parseInvocation(['~/nowhere'], { exists: nothingExists })
  assert.equal(result.error, 'Path not found: ~/nowhere')
})

test('args: --regenerate sets regenerate true', () => {
  const result = parseInvocation(['--regenerate'], { exists: nothingExists })
  assert.equal(result.regenerate, true)
})

test('args: regenerate is false by default', () => {
  const result = parseInvocation([], { exists: nothingExists })
  assert.equal(result.regenerate, false)
})

test('args: an unknown flag is an error', () => {
  const result = parseInvocation(['--colour=red'], { exists: nothingExists })
  assert.equal(result.error, 'Unknown flag: --colour=red. Valid flags: --diagrams=a,b and --regenerate.')
})
