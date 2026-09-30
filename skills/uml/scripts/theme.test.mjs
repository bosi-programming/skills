import assert from 'node:assert/strict'
import { test } from 'node:test'

import { ACCENTS, injectTheme } from './theme.mjs'

const SOURCE = '@startuml\nclass Order\n@enduml\n'

test('theme: block inserted right after @startuml', () => {
  const lines = injectTheme(SOURCE, 'class', { smetana: false }).split('\n')
  assert.deepEqual([lines[0], lines[1]], ['@startuml', 'skinparam backgroundColor #0b0e14'])
})

test('theme: the original body follows the block unchanged', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  assert.ok(themed.endsWith('\nclass Order\n@enduml\n'))
})

test('theme: a source with no @startuml is wrapped', () => {
  const themed = injectTheme('class Order', 'class', { smetana: false })
  assert.deepEqual([themed.split('\n')[0], themed.trimEnd().split('\n').at(-1)], ['@startuml', '@enduml'])
})

test('theme: accent differs per type', () => {
  assert.equal(new Set(Object.values(ACCENTS)).size, 9)
})

test('theme: the type accent colours borders and arrows', () => {
  const themed = injectTheme(SOURCE, 'deployment', { smetana: false })
  assert.ok(themed.includes(`skinparam ArrowColor ${ACCENTS.deployment}`))
})

test('theme: meaning colours present for interface, abstract and enum', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  const spots = ['stereotypeIBackgroundColor', 'stereotypeABackgroundColor', 'stereotypeEBackgroundColor']
  assert.deepEqual(spots.filter((name) => !themed.includes(`skinparam ${name} `)), [])
})

test('theme: meaning colours present for final states', () => {
  const themed = injectTheme('@startuml\n[*] --> Open\nOpen --> [*]\n@enduml', 'state', { smetana: false })
  assert.ok(themed.includes('skinparam stateEndColor '))
})

test('theme: smetana adds pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: true })
  assert.ok(themed.includes('\n!pragma layout smetana\n'))
})

test('theme: no smetana adds no pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  assert.equal(themed.includes('!pragma layout'), false)
})
