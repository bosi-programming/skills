import { findArrow, freeText } from './arrows.mjs'

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
  activity: '#7ee787',
  er: '#f2cc60',
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

export const ARROW_COLOURS = Object.freeze({
  inheritance: '#bc8cff',
  wholePart: '#f0883e',
  association: '#58a6ff',
  dependency: '#8b98a9',
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
  'activity',
  'activityDiamond',
  'entity',
]

export const SIZES = Object.freeze({
  nodesep: 40,
  ranksep: 70,
  defaultFontSize: 12,
  noteFontSize: 10,
  ArrowFontSize: 10,
  titleFontSize: 16,
})

const PADDING = 4

const sizeLines = () => Object.entries(SIZES).map(([name, value]) => `skinparam ${name} ${value}`)

const START = '@startuml'
const END = '@enduml'
const SMETANA = '!pragma layout smetana'

const elementLines = (accent) =>
  ELEMENTS.flatMap((element) => [
    `skinparam ${element}BackgroundColor ${PALETTE.element}`,
    `skinparam ${element}BorderColor ${accent}`,
    `skinparam ${element}FontColor ${PALETTE.text}`,
  ])

const activityLines = (accent) => [
  `skinparam activityBarColor ${accent}`,
  `skinparam swimlaneBorderColor ${PALETTE.muted}`,
  `skinparam swimlaneTitleFontColor ${PALETTE.text}`,
]

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

const UNTAGGED_TYPES = ['sequence', 'state', 'activity', 'er']

const stereotypeOf = (kind) => `uml${kind[0].toUpperCase()}${kind.slice(1)}`

const arrowStyleLines = () => [
  'arrow {',
  ...Object.entries(ARROW_COLOURS).map(([kind, colour]) => `.${stereotypeOf(kind)} { LineColor ${colour} }`),
  '}',
]

const GROUPS = ['package', 'frame', 'node', 'rectangle', 'folder']

const CORNER = 8

const groupStyleLines = () =>
  GROUPS.map(
    (group) =>
      `${group} { LineStyle 4-4; LineColor ${PALETTE.muted}; FontColor ${PALETTE.muted}; BackgroundColor ${PALETTE.panel}; RoundCorner ${CORNER} }`
  )

const legendStyleLine = () =>
  `legend { BackgroundColor ${PALETTE.panel}; LineColor ${PALETTE.line}; FontColor ${PALETTE.text}; FontSize ${SIZES.noteFontSize} }`

const entityStyleLines = (type) =>
  type === 'er'
    ? [
        `spotEntity { BackgroundColor ${MEANINGS.class} }`,
        `visibilityIcon { BackgroundColor ${PALETTE.text}; LineColor ${PALETTE.text} }`,
      ]
    : []

const styleLines = (type) => [
  '<style>',
  `root { Padding ${PADDING} }`,
  ...arrowStyleLines(),
  ...groupStyleLines(),
  legendStyleLine(),
  ...entityStyleLines(type),
  'stateDiagram {',
  `start { BackgroundColor ${MEANINGS.initialState}; LineColor ${MEANINGS.initialState} }`,
  `end { BackgroundColor ${MEANINGS.finalState}; LineColor ${MEANINGS.finalState} }`,
  '}',
  'activityDiagram {',
  `start { BackgroundColor ${MEANINGS.initialState}; LineColor ${MEANINGS.initialState} }`,
  `stop { BackgroundColor ${MEANINGS.finalState}; LineColor ${MEANINGS.finalState} }`,
  `end { LineColor ${MEANINGS.finalState} }`,
  '}',
  '</style>',
]

const labelStart = (line, from) => {
  let quoted = false
  for (let index = from; index < line.length; index += 1) {
    if (line[index] === '"') quoted = !quoted
    if (line[index] === ':' && !quoted) return index
  }
  return line.length
}

const tagArrow = (line) => {
  const arrow = findArrow(line)
  if (!arrow?.kind) return line
  const cut = labelStart(line, arrow.end)
  const ends = line.slice(0, cut).trimEnd()
  if (ends.slice(arrow.end).includes('<<')) return line
  const label = line.slice(cut)
  return `${ends} <<${stereotypeOf(arrow.kind)}>>${label ? ` ${label}` : ''}`
}

const tagArrows = (source, type) => {
  if (UNTAGGED_TYPES.includes(type)) return source
  const lines = source.split('\n')
  const skipped = freeText(lines)
  return lines.map((line, index) => (skipped[index] ? line : tagArrow(line))).join('\n')
}

const themeLines = (type, { smetana }) => {
  const accent = ACCENTS[type]
  return [
    `skinparam backgroundColor ${PALETTE.background}`,
    `skinparam defaultFontColor ${PALETTE.text}`,
    'skinparam shadowing false',
    `skinparam roundCorner ${CORNER}`,
    ...sizeLines(),
    `skinparam ArrowColor ${accent}`,
    `skinparam ArrowFontColor ${PALETTE.muted}`,
    `skinparam sequenceLifeLineBorderColor ${PALETTE.muted}`,
    `skinparam sequenceGroupBorderColor ${accent}`,
    `skinparam sequenceGroupBackgroundColor ${PALETTE.panel}`,
    ...elementLines(accent),
    ...activityLines(accent),
    ...meaningLines(),
    ...styleLines(type),
    ...(smetana ? [SMETANA] : []),
  ]
}

export const injectTheme = (source, type, options) => {
  const block = themeLines(type, options).join('\n')
  const tagged = tagArrows(source, type)
  const lines = tagged.split('\n')
  const start = lines.findIndex((line) => line.trim().startsWith(START))
  if (start === -1) return `${START}\n${block}\n${tagged}\n${END}\n`
  return [...lines.slice(0, start + 1), block, ...lines.slice(start + 1)].join('\n')
}
