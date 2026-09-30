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

test('density: activity actions are elements, one line or several', () => {
  const source = lines('start', ':POST /orders;', ':check the cart', 'and the stock;', ':charge card;', ':charge card;', 'stop')
  assert.equal(countDensity(source, 'activity').elements, 4)
})

test('density: activity arrows are the paths out of branches, forks and loops', () => {
  const source = lines(
    'if (cart empty?) then (yes)',
    '  :reject;',
    'elseif (stock short?) then (yes)',
    '  :wait;',
    'else (no)',
    'endif',
    'fork',
    '  :reserve;',
    'fork again',
    '  :charge;',
    'end fork',
    'repeat',
    '  :send;',
    'repeat while (failed?) is (yes) -> no;',
    'while (items left?) is (yes)',
    '  :ship;',
    'endwhile (no)'
  )
  assert.equal(countDensity(source, 'activity').arrows, 7)
})

test('density: activity guards, labels and swimlanes are not counted as arrows or elements', () => {
  const source = lines('|Client|', 'start', '-> submit;', ':send order;', '|Api|', 'if (a -> b?) then (yes)', 'endif', 'note right: x --> y', 'stop')
  assert.deepEqual(countDensity(source, 'activity'), { arrows: 1, elements: 1 })
})

test('density: too many activity actions warn', () => {
  const source = lines('start', ...Array.from({ length: 13 }, (_, index) => `:step ${index};`), 'stop')
  assert.match(densityWarning(source, 'activity') ?? '', /^Hard to read: 0 arrows and 13 elements\./)
})

test('density: er entities are elements and crow-foot lines are arrows', () => {
  const source = lines(
    'entity customers {',
    '  *id : bigint <<PK>>',
    '  --',
    '  email : varchar',
    '}',
    'entity orders',
    'entity "line_items" as items',
    'customers ||--o{ orders : places',
    'orders ||..|{ items',
    'items }o--|| products',
    'a |o--o| b'
  )
  assert.deepEqual(countDensity(source, 'er'), { arrows: 4, elements: 3 })
})
