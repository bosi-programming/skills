import assert from 'node:assert/strict'
import { test } from 'node:test'
import { inflateRawSync } from 'node:zlib'

import { decodeBase64, encodePlantUml } from './encode.mjs'

test('encode: known vector', () => {
  assert.equal(encodePlantUml('Bob -> Alice : hello'), 'SyfFKj2rKt3CoKnELR1Io4ZDoSa70000')
})

test('encode: the known vector inflates to its source', () => {
  const bytes = decodeBase64('SyfFKj2rKt3CoKnELR1Io4ZDoSa70000')
  assert.equal(inflateRawSync(bytes).toString('utf8'), 'Bob -> Alice : hello')
})

test('encode: round trip through inflateRaw', () => {
  const source = '@startuml\nclass Pedido {\n  +total: number\n}\n@enduml\n'
  const bytes = decodeBase64(encodePlantUml(source))
  assert.equal(inflateRawSync(bytes).toString('utf8'), source)
})

test('encode: uses only the PlantUML alphabet', () => {
  assert.match(encodePlantUml('A -> B : ção ✓\n'.repeat(20)), /^[0-9A-Za-z_-]+$/)
})
