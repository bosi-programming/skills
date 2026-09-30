const ARROW = /(?<=^|[\s"\]])(<\||<<|<|\*|o|\+|#|x|\})?([-.]+(?:(?:\[[^\]]*\]|left|right|down|up|le|ri|do|l|r|u|d)[-.]+)?)(\|>|>>|>|\*|o|\+|#|x|\{)?(?=$|[\s"[])/g

const INHERITANCE_HEADS = ['<|', '|>']
const WHOLE_PART_HEADS = ['*', 'o']
const POINTED = /[<>]/

const BLOCKS = [
  { open: /^\s*[rh]?note\b(?!.*[:"])/i, close: /^\s*end\s?[rh]?note\b/i },
  { open: /^\s*legend\b/i, close: /^\s*end\s?legend\b/i },
  { open: /^\s*\/'(?!.*'\/)/, close: /'\/\s*$/ },
]

const ONE_LINE_TEXT = /^\s*('|[rh]?note\b|title\b|\/'.*'\/\s*$)/i

const kindOf = (left = '', body, right = '') => {
  if (INHERITANCE_HEADS.includes(left) || INHERITANCE_HEADS.includes(right)) return 'inheritance'
  if (WHOLE_PART_HEADS.includes(left) || WHOLE_PART_HEADS.includes(right)) return 'wholePart'
  if (!body.replace(/\[[^\]]*\]/g, '').includes('.')) return 'association'
  return POINTED.test(left + right) ? 'dependency' : null
}

export const findArrow = (line) => {
  for (const match of line.matchAll(ARROW)) {
    const end = match.index + match[0].length
    if (!line.slice(0, match.index).trim() || !line.slice(end).trim()) continue
    const [token, left, body, right] = match
    return { token, index: match.index, end, kind: kindOf(left, body, right) }
  }
  return null
}

export const freeText = (lines) => {
  let block = null
  return lines.map((line) => {
    if (block) {
      if (block.close.test(line)) block = null
      return true
    }
    block = BLOCKS.find((candidate) => candidate.open.test(line)) ?? null
    return Boolean(block) || ONE_LINE_TEXT.test(line)
  })
}
