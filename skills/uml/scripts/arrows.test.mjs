import assert from 'node:assert/strict'
import { test } from 'node:test'

import { findArrow, freeText } from './arrows.mjs'

const KINDS = [
  ['A <|-- B', 'inheritance'],
  ['B --|> A', 'inheritance'],
  ['Contract <|.. Impl', 'inheritance'],
  ['Whole *-- Part', 'wholePart'],
  ['Order "1" o-- "0..1" Payment', 'wholePart'],
  ['Part --* Whole', 'wholePart'],
  ['A ..> B', 'dependency'],
  ['B <.. A : uses', 'dependency'],
  ['A --> B', 'association'],
  ['A -- B', 'association'],
  ['Api - OrdersRest', 'association'],
  ['A -> B : call', 'association'],
  ['A ->> B', 'association'],
  ['Pod -down-> Api', 'association'],
  ['[*] --> Draft', 'association'],
  ['[Api] ..> Domain : uses', 'dependency'],
  ['A .. B', null],
]

for (const [line, kind] of KINDS) {
  test(`arrows: "${line}" is ${kind ?? 'an arrow of no kind'}`, () => {
    assert.equal(findArrow(line)?.kind, kind)
  })
}

for (const line of ['--', '-- private --', '-token: String', '+refund(amount: Money): Result', 'class Order', '  status = SUBMITTED', '@startuml']) {
  test(`arrows: "${line}" holds no arrow`, () => {
    assert.equal(findArrow(line), null)
  })
}

test('arrows: the match gives the token and where it ends', () => {
  const line = 'Order "1" *-- "1..*" LineItem : lines'
  const arrow = findArrow(line)
  assert.deepEqual([arrow.token, line.slice(arrow.index, arrow.end)], ['*--', '*--'])
})

test('arrows: note and legend bodies and comments are free text', () => {
  const lines = ['A --> B', 'note right of A', 'a -> b', 'end note', 'legend bottom', 'x --> y', 'endlegend', "' A --> B", 'note left of B : c -> d', 'C --> D']
  assert.deepEqual(freeText(lines), [false, true, true, true, true, true, true, true, true, false])
})

test('arrows: a one-line note does not open a block', () => {
  assert.deepEqual(freeText(['note "x" as N', 'A --> B']), [true, false])
})
