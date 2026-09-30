export const DIAGRAM_TYPES = Object.freeze([
  'class',
  'sequence',
  'state',
  'profile',
  'composite',
  'component',
  'deployment',
  'object',
  'package',
  'activity',
  'er',
])

const DIAGRAMS_FLAG = '--diagrams'
const REGENERATE_FLAG = '--regenerate'
const PATH_PREFIXES = ['./', '../', '/', '~']

const unknownTypeError = (name) =>
  `Unknown diagram type: ${name}. Valid types: ${DIAGRAM_TYPES.join(', ')}.`

const unknownFlagError = (flag) =>
  `Unknown flag: ${flag}. Valid flags: ${DIAGRAMS_FLAG}=a,b and ${REGENERATE_FLAG}.`

const splitFlags = (argv) => {
  const words = []
  let names = null
  let regenerate = false
  let unknownFlag = null
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (token === REGENERATE_FLAG) {
      regenerate = true
    } else if (token === DIAGRAMS_FLAG) {
      names = argv[index + 1] ?? ''
      index += 1
    } else if (token.startsWith(`${DIAGRAMS_FLAG}=`)) {
      names = token.slice(DIAGRAMS_FLAG.length + 1)
    } else if (token.startsWith('--')) {
      unknownFlag ??= token
    } else {
      words.push(token)
    }
  }
  return { words, names, regenerate, unknownFlag }
}

const selectDiagrams = (names) => {
  if (names === null) return { diagrams: [...DIAGRAM_TYPES] }
  const requested = names.split(',').map((name) => name.trim()).filter(Boolean)
  const unknown = requested.find((name) => !DIAGRAM_TYPES.includes(name))
  if (unknown) return { error: unknownTypeError(unknown) }
  return { diagrams: DIAGRAM_TYPES.filter((type) => requested.includes(type)) }
}

const looksLikePath = (text) =>
  PATH_PREFIXES.some((prefix) => text.startsWith(prefix)) || (!/\s/.test(text) && text.includes('/'))

const classifyTarget = (text, exists) => {
  if (text === '') return { mode: 'repo', target: null }
  if (exists(text)) return { mode: 'path', target: text }
  if (looksLikePath(text)) return { error: `Path not found: ${text}` }
  return { mode: 'description', target: text }
}

export const parseInvocation = (argv, { exists }) => {
  const { words, names, regenerate, unknownFlag } = splitFlags(argv)
  if (unknownFlag) return { error: unknownFlagError(unknownFlag) }
  const selection = selectDiagrams(names)
  if (selection.error) return { error: selection.error }
  const target = classifyTarget(words.join(' ').trim(), exists)
  if (target.error) return { error: target.error }
  return { ...target, diagrams: selection.diagrams, regenerate }
}
