import { findArrow, freeText } from './arrows.mjs'

export const MAX_ARROWS = 15
export const MAX_ELEMENTS = 12

const DECLARATION =
  /^\s*(?:abstract(?:\s+class)?|class|interface|enum|package|component|node|state|participant|actor|database|object|rectangle|artifact|frame|folder|queue|card|entity)\s+("[^"]*"|\[[^\]]*\]|[^\s{]+)/i

const RELATION = /\s(?:\|\||\|o|\}o|\}\|)[-.]+(?:\|\||o\||o\{|\|\{)\s/

const ACTION_START = /^\s*:/
const ACTION_END = /[;|<>/\]}]\s*$/
const PATH = /^\s*(?:if|elseif|else|fork(?:\s+again)?|split(?:\s+again)?|repeat\s+while|while|case)\b/i

const BRACKET = /(?<![-.\w])\[([^\][*#]+)\]/g

const bare = (name) => name.replace(/^["[]|["\]]$/g, '').trim()

const beforeLabel = (line, from) => {
  const colon = line.indexOf(':', from)
  return colon === -1 ? line : line.slice(0, colon)
}

const lineFacts = (line) => {
  const declared = line.match(DECLARATION)
  if (declared) return { arrow: false, names: [bare(declared[1])] }
  const arrow = findArrow(line)
  const names = [...beforeLabel(line, arrow?.end ?? 0).matchAll(BRACKET)].map((match) => bare(match[1]))
  return { arrow: Boolean(arrow) || RELATION.test(` ${line} `), names }
}

const activityDensity = (lines) => {
  let inAction = false
  let arrows = 0
  let elements = 0
  for (const line of lines) {
    if (!inAction && ACTION_START.test(line)) {
      elements += 1
      inAction = true
    } else if (!inAction && PATH.test(line)) {
      arrows += 1
    }
    if (inAction && ACTION_END.test(line)) inAction = false
  }
  return { arrows, elements }
}

export const countDensity = (source, type) => {
  const lines = source.split('\n')
  const skipped = freeText(lines)
  const kept = lines.filter((line, index) => !skipped[index])
  if (type === 'activity') return activityDensity(kept)
  const facts = kept.map(lineFacts)
  const names = new Set(facts.flatMap((fact) => fact.names).filter(Boolean))
  return { arrows: facts.filter((fact) => fact.arrow).length, elements: names.size }
}

const counted = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`

export const densityWarning = (source, type) => {
  const { arrows, elements } = countDensity(source, type)
  if (arrows <= MAX_ARROWS && elements <= MAX_ELEMENTS) return null
  return `Hard to read: ${counted(arrows, 'arrow')} and ${counted(elements, 'element')}. Keep a diagram to at most ${MAX_ARROWS} arrows and ${MAX_ELEMENTS} elements.`
}
