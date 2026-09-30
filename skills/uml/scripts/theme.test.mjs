import assert from 'node:assert/strict'
import { test } from 'node:test'

import { ACCENTS, ARROW_COLOURS, MEANINGS, PALETTE, injectTheme } from './theme.mjs'

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

const bodyOf = (source, type) => {
  const themed = injectTheme(source, type, { smetana: false })
  return themed.slice(themed.indexOf('</style>') + '</style>'.length).trim().split('\n')
}

test('theme: the four arrow kinds get four colours', () => {
  assert.deepEqual([Object.keys(ARROW_COLOURS), new Set(Object.values(ARROW_COLOURS)).size], [['inheritance', 'wholePart', 'association', 'dependency'], 4])
})

test('theme: the style block colours each arrow kind by stereotype', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  const expected = [
    'arrow {',
    `.umlInheritance { LineColor ${ARROW_COLOURS.inheritance} }`,
    `.umlWholePart { LineColor ${ARROW_COLOURS.wholePart} }`,
    `.umlAssociation { LineColor ${ARROW_COLOURS.association} }`,
    `.umlDependency { LineColor ${ARROW_COLOURS.dependency} }`,
    '}',
  ].join('\n')
  assert.ok(themed.slice(themed.indexOf('<style>'), themed.indexOf('</style>')).includes(expected))
})

test('theme: each arrow is tagged with its kind, before any label', () => {
  const source = ['@startuml', 'A <|-- B', 'Order "1" *-- "1..*" LineItem : lines', 'Web ..> Domain : <<import>>', 'Api --> Db', '@enduml'].join('\n')
  assert.deepEqual(bodyOf(source, 'class'), [
    'A <|-- B <<umlInheritance>>',
    'Order "1" *-- "1..*" LineItem <<umlWholePart>> : lines',
    'Web ..> Domain <<umlDependency>> : <<import>>',
    'Api --> Db <<umlAssociation>>',
    '@enduml',
  ])
})

test('theme: arrows with no kind, a stereotype of their own, or in notes stay as written', () => {
  const body = ['N .. A', 'A --> B <<flow>> : x', 'note right of A', 'a --> b', 'end note', 'legend bottom', 'c ..> d', 'endlegend']
  assert.deepEqual(bodyOf(['@startuml', ...body, '@enduml'].join('\n'), 'component'), [...body, '@enduml'])
})

for (const type of ['sequence', 'state']) {
  test(`theme: ${type} arrows are not tagged`, () => {
    const body = ['A --> B : go', 'B ..> C']
    assert.deepEqual(bodyOf(['@startuml', ...body, '@enduml'].join('\n'), type), [...body, '@enduml'])
  })
}

const styleOf = (type) => {
  const themed = injectTheme(SOURCE, type, { smetana: false })
  return themed.slice(themed.indexOf('<style>'), themed.indexOf('</style>')).split('\n')
}

test('theme: every container kind shares one dashed group style', () => {
  const rule = `{ LineStyle 4-4; LineColor ${PALETTE.muted}; FontColor ${PALETTE.muted}; BackgroundColor ${PALETTE.panel}; RoundCorner 8 }`
  const missing = ['package', 'frame', 'node', 'rectangle', 'folder'].filter((name) => !styleOf('deployment').includes(`${name} ${rule}`))
  assert.deepEqual(missing, [])
})

test('theme: the legend sits on a panel with a line-colour border', () => {
  assert.ok(styleOf('package').includes(`legend { BackgroundColor ${PALETTE.panel}; LineColor ${PALETTE.line}; FontColor ${PALETTE.text}; FontSize 10 }`))
})

test('theme: smetana adds pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: true })
  assert.ok(themed.includes('\n!pragma layout smetana\n'))
})

test('theme: no smetana adds no pragma', () => {
  const themed = injectTheme(SOURCE, 'class', { smetana: false })
  assert.equal(themed.includes('!pragma layout'), false)
})
