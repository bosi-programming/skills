import assert from 'node:assert/strict'
import { test } from 'node:test'

import { ACCENTS, MEANINGS, injectTheme } from './theme.mjs'

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

test('theme: start and end states are coloured through a style block', () => {
  const themed = injectTheme('@startuml\n[*] --> Open\nOpen --> [*]\n@enduml', 'state', { smetana: false })
  const expected = [
    'stateDiagram {',
    `start { BackgroundColor ${MEANINGS.initialState}; LineColor ${MEANINGS.initialState} }`,
    `end { BackgroundColor ${MEANINGS.finalState}; LineColor ${MEANINGS.finalState} }`,
    '}',
  ].join('\n')
  const style = themed.slice(themed.indexOf('<style>'), themed.indexOf('</style>'))
  assert.ok(style.includes(expected))
})

test('theme: every style rule sits in one style block', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  assert.deepEqual([themed.split('<style>').length, themed.split('</style>').length], [2, 2])
})

test('theme: no start or end skinparam that PlantUML ignores', () => {
  const themed = injectTheme('@startuml\n[*] --> Open\n@enduml', 'state', { smetana: false })
  assert.equal(/skinparam state(Start|End)Color/.test(themed), false)
})

test('theme: spacing and font sizes are set', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  const expected = [
    'skinparam nodesep 40',
    'skinparam ranksep 70',
    'skinparam defaultFontSize 12',
    'skinparam noteFontSize 10',
    'skinparam ArrowFontSize 10',
    'skinparam titleFontSize 16',
    'root { Padding 4 }',
  ]
  assert.deepEqual(expected.filter((line) => !themed.split('\n').includes(line)), [])
})

test('theme: padding goes through the style block, as skinparam padding prints a warning in the drawing', () => {
  assert.equal(/skinparam padding/i.test(injectTheme(SOURCE, 'class', { smetana: false })), false)
})

for (const type of Object.keys(ACCENTS)) {
  test(`theme: ${type} output never sets a line type`, () => {
    for (const smetana of [false, true]) {
      assert.equal(/linetype/i.test(injectTheme(SOURCE, type, { smetana })), false)
    }
  })
}

test('theme: smetana adds pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: true })
  assert.ok(themed.includes('\n!pragma layout smetana\n'))
})

test('theme: no smetana adds no pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  assert.equal(themed.includes('!pragma layout'), false)
})
