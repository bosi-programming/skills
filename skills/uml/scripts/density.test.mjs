import assert from 'node:assert/strict'
import { test } from 'node:test'

import { MAX_ARROWS, MAX_ELEMENTS, countDensity, densityWarning } from './density.mjs'

const lines = (...body) => ['@startuml', ...body, '@enduml'].join('\n')

const arrowsBetween = (count) => Array.from({ length: count }, (_, index) => `A${index} --> B${index}`)

const classes = (count) => Array.from({ length: count }, (_, index) => `class C${index}`)

test('density: the limits are 15 arrows and 12 elements', () => {
  assert.deepEqual([MAX_ARROWS, MAX_ELEMENTS], [15, 12])
})

test('density: counts each arrow kind once per line', () => {
  const source = lines('A --> B', 'B ..> C', 'C <|-- D', 'D *-- E', 'E o-- F', 'Alice -> Bob : hi', 'Bob ->> Alice', 'class Order {', '  -id: String', '  --', '}')
  assert.equal(countDensity(source).arrows, 7)
})

test('density: counts declared elements of every keyword', () => {
  const keywords = ['class', 'interface', 'enum', 'abstract', 'abstract class', 'package', 'component', 'node', 'state', 'participant', 'actor', 'database', 'object', 'rectangle', 'artifact', 'frame', 'folder', 'queue', 'card']
  const source = lines(...keywords.map((keyword, index) => `${keyword} "E${index}"`))
  assert.equal(countDensity(source).elements, keywords.length)
})

test('density: counts a bracket component once however often it is named', () => {
  const source = lines('[Web] --> [Api]', '[Api] ..> Db : uses', 'component [Api] as Api', 'database Db')
  assert.equal(countDensity(source).elements, 3)
})

test('density: arrow colours, start states and label guards are not elements', () => {
  const source = lines('[*] --> Draft', 'Draft -[#red]-> Paid : pay() [card ok]')
  assert.equal(countDensity(source).elements, 0)
})

test('density: text in notes and legends is not counted', () => {
  const source = lines('legend bottom', 'Cycles: a --> b --> a', 'class X', 'endlegend', 'note right of A : x --> y')
  assert.deepEqual(countDensity(source), { arrows: 0, elements: 0 })
})

test('density: a diagram inside both limits gets no warning', () => {
  assert.equal(densityWarning(lines(...classes(12), ...arrowsBetween(15))), null)
})

test('density: too many arrows names the counts and the limits', () => {
  assert.equal(
    densityWarning(lines(...classes(3), ...arrowsBetween(16))),
    'Hard to read: 16 arrows and 3 elements. Keep a diagram to at most 15 arrows and 12 elements.'
  )
})

test('density: too many elements warns too', () => {
  assert.match(densityWarning(lines(...classes(13))) ?? '', /^Hard to read: 0 arrows and 13 elements\./)
})
