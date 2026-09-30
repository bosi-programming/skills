export const PALETTE = Object.freeze({
  background: '#0b0e14',
  panel: '#11151d',
  element: '#161b25',
  line: '#222a36',
  text: '#e6edf3',
  muted: '#8b98a9',
})

export const NOTICES = Object.freeze({
  warningBorder: '#d29922',
  warningBackground: '#26200f',
  warningText: '#e3b341',
  errorBorder: '#f85149',
  errorBackground: '#2a1315',
  errorText: '#ff7b72',
})

export const ACCENTS = Object.freeze({
  class: '#58a6ff',
  sequence: '#3fb950',
  state: '#d29922',
  profile: '#bc8cff',
  composite: '#39c5cf',
  component: '#f0883e',
  deployment: '#db61a2',
  object: '#ff7b72',
  package: '#a5d6ff',
})

export const MEANINGS = Object.freeze({
  class: '#58a6ff',
  interface: '#bc8cff',
  abstract: '#e3b341',
  enum: '#3fb950',
  initialState: '#3fb950',
  finalState: '#f85149',
  note: '#26200f',
  noteBorder: '#d29922',
})

const ELEMENTS = [
  'class',
  'object',
  'state',
  'component',
  'node',
  'package',
  'participant',
  'actor',
  'database',
  'artifact',
  'rectangle',
  'frame',
  'folder',
  'cloud',
  'collections',
  'queue',
  'card',
]

const START = '@startuml'
const END = '@enduml'
const SMETANA = '!pragma layout smetana'

const elementLines = (accent) =>
  ELEMENTS.flatMap((element) => [
    `skinparam ${element}BackgroundColor ${PALETTE.element}`,
    `skinparam ${element}BorderColor ${accent}`,
    `skinparam ${element}FontColor ${PALETTE.text}`,
  ])

const meaningLines = () => [
  `skinparam stereotypeCBackgroundColor ${MEANINGS.class}`,
  `skinparam stereotypeIBackgroundColor ${MEANINGS.interface}`,
  `skinparam stereotypeABackgroundColor ${MEANINGS.abstract}`,
  `skinparam stereotypeEBackgroundColor ${MEANINGS.enum}`,
  `skinparam interfaceBackgroundColor ${PALETTE.element}`,
  `skinparam interfaceBorderColor ${MEANINGS.interface}`,
  `skinparam noteBackgroundColor ${MEANINGS.note}`,
  `skinparam noteBorderColor ${MEANINGS.noteBorder}`,
  `skinparam noteFontColor ${PALETTE.text}`,
]

const styleLines = () => [
  '<style>',
  'stateDiagram {',
  `start { BackgroundColor ${MEANINGS.initialState}; LineColor ${MEANINGS.initialState} }`,
  `end { BackgroundColor ${MEANINGS.finalState}; LineColor ${MEANINGS.finalState} }`,
  '}',
  '</style>',
]

const themeLines = (type, { smetana }) => {
  const accent = ACCENTS[type]
  return [
    `skinparam backgroundColor ${PALETTE.background}`,
    `skinparam defaultFontColor ${PALETTE.text}`,
    'skinparam shadowing false',
    'skinparam roundCorner 8',
    `skinparam ArrowColor ${accent}`,
    `skinparam ArrowFontColor ${PALETTE.muted}`,
    `skinparam sequenceLifeLineBorderColor ${PALETTE.muted}`,
    `skinparam sequenceGroupBorderColor ${accent}`,
    `skinparam sequenceGroupBackgroundColor ${PALETTE.panel}`,
    ...elementLines(accent),
    ...meaningLines(),
    ...styleLines(),
    ...(smetana ? [SMETANA] : []),
  ]
}

export const injectTheme = (source, type, options) => {
  const block = themeLines(type, options).join('\n')
  const lines = source.split('\n')
  const start = lines.findIndex((line) => line.trim().startsWith(START))
  if (start === -1) return `${START}\n${block}\n${source}\n${END}\n`
  return [...lines.slice(0, start + 1), block, ...lines.slice(start + 1)].join('\n')
}
