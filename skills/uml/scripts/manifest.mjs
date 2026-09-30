import { join } from 'node:path'

import { DIAGRAM_TYPES } from './args.mjs'

export const MANIFEST_FILE = 'uml.json'

const ORIGINS = ['code', 'description']
const NEEDS_WHY = ['sequence', 'state']
const PREFIX = `${MANIFEST_FILE}:`

const diagramError = (diagram, seen) => {
  const { type, file, why, noBasis } = diagram ?? {}
  if (!DIAGRAM_TYPES.includes(type)) return `${PREFIX} unknown diagram type "${type}".`
  if (seen.has(type)) return `${PREFIX} ${type} is listed twice.`
  if (noBasis && file) return `${PREFIX} ${type} has both a file and a noBasis note; a no-basis diagram has file null.`
  if (!noBasis && !file) return `${PREFIX} ${type} needs a file or a noBasis note.`
  if (!noBasis && NEEDS_WHY.includes(type) && !why) return `${PREFIX} ${type} needs a "why" naming the flow or entity chosen and why.`
  return null
}

const byPageOrder = (left, right) => DIAGRAM_TYPES.indexOf(left.type) - DIAGRAM_TYPES.indexOf(right.type)

export const validateManifest = (value) => {
  if (!ORIGINS.includes(value?.origin)) return { error: `${PREFIX} origin must be "code" or "description", got "${value?.origin}".` }
  if (typeof value.source !== 'string') return { error: `${PREFIX} source must be a string.` }
  if (!Array.isArray(value.diagrams)) return { error: `${PREFIX} diagrams must be a list.` }
  const seen = new Set()
  for (const diagram of value.diagrams) {
    const error = diagramError(diagram, seen)
    if (error) return { error }
    seen.add(diagram.type)
  }
  return { ok: true, manifest: { ...value, diagrams: [...value.diagrams].sort(byPageOrder) } }
}

const parse = (text) => {
  try {
    return { value: JSON.parse(text) }
  } catch (error) {
    return { error: `${PREFIX} not valid JSON (${error.message}).` }
  }
}

export const readManifest = async (outputDir, { readFile }) => {
  let text
  try {
    text = await readFile(join(outputDir, MANIFEST_FILE), 'utf8')
  } catch (error) {
    if (error.code === 'ENOENT') return { state: 'missing' }
    return { state: 'unreadable', error: `${PREFIX} ${error.message}` }
  }
  const parsed = parse(text)
  if (parsed.error) return { state: 'unreadable', error: parsed.error }
  const checked = validateManifest(parsed.value)
  if (checked.error) return { state: 'unreadable', error: checked.error }
  return { state: 'ok', manifest: checked.manifest }
}
