import assert from 'node:assert/strict'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

import { DIAGRAM_TYPES } from './args.mjs'

const SKILL_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const REPO = resolve(SKILL_DIR, '..', '..')
const SKILL_MD = join(SKILL_DIR, 'SKILL.md')
const CONFIG_MD = resolve(REPO, 'skills', 'setup', 'references', 'config.md')

const TITLES = ['Class', 'Sequence', 'State', 'Profile', 'Composite structure', 'Component', 'Deployment', 'Object', 'Package']
const SETTINGS = [['uml.outputDir', 'docs/uml'], ['uml.plantumlJar', "''"], ['uml.plantumlServer', 'local'], ['uml.idleMinutes', '30']]
const IGNORED = ['node_modules', '__pycache__', 'runs']

const read = (path) => (existsSync(path) ? readFileSync(path, 'utf8') : '')

const walk = (folder) =>
  existsSync(folder)
    ? readdirSync(folder)
        .filter((name) => !IGNORED.includes(name))
        .flatMap((name) => (statSync(join(folder, name)).isDirectory() ? walk(join(folder, name)) : [join(folder, name)]))
    : []

const files = (extensions) => walk(SKILL_DIR).filter((path) => extensions.some((extension) => path.endsWith(extension)))

const relativeRefs = (text) => [...text.matchAll(/(?:`|\]\()(\.\.?\/[^`)\s]+)/g)].map((match) => match[1])

const section = (text, heading) => {
  const start = text.indexOf(`\n## ${heading}\n`)
  if (start === -1) return ''
  const end = text.indexOf('\n## ', start + 1)
  return text.slice(start, end === -1 ? undefined : end)
}

const shellBlocks = (text) => [...text.matchAll(/```(?:bash|sh)\n([\s\S]*?)```/g)].map((match) => match[1])

const skill = read(SKILL_MD)

test('structure: SKILL.md declares name uml', () => {
  assert.match(skill, /^---\nname: uml\n/)
})

test('structure: SKILL.md links config and names four keys with defaults', () => {
  const linked = relativeRefs(skill).map((ref) => resolve(SKILL_DIR, ref))
  const missing = SETTINGS.filter(([key, value]) => !skill.includes(`\`${key}\``) || !skill.includes(`\`${value}\``))
  assert.deepEqual([linked.includes(CONFIG_MD), missing], [true, []])
})

test('structure: selection guide covers nine types', () => {
  const guide = section(skill, 'Diagram selection guide')
  const missing = TITLES.filter((title) => !guide.includes(`\n### ${title}\n`))
  assert.deepEqual([missing, /^#+ .*(activity|use case)/im.test(skill)], [[], false])
})

test('structure: SKILL.md states the LLM never writes HTML', () => {
  assert.match(skill, /never writes HTML/)
})

test('structure: SKILL.md asks before download-jar', () => {
  const consent = skill.indexOf('Download only after the person says yes.')
  const command = skill.indexOf('uml.mjs" download-jar')
  assert.deepEqual([consent > -1, command > -1, consent < command], [true, true, true])
})

test('structure: SKILL.md stops on no Java naming uml.plantumlServer', () => {
  assert.match(section(skill, 'Run it'), /`java` is `false`[\s\S]*`uml\.plantumlServer`/)
})

test('structure: SKILL.md branches render-only, regenerate, missing manifest', () => {
  const flow = section(skill, 'Run it')
  const branches = ['`ok`', '`--regenerate`', '`missing`', '`unreadable`']
  assert.deepEqual(branches.filter((branch) => !flow.includes(branch)), [])
})

test('structure: every reference file exists and SKILL.md links it', () => {
  const expected = ['manifest', ...DIAGRAM_TYPES].map((name) => `./references/${name}.md`)
  const problems = expected.filter((ref) => !skill.includes(`\`${ref}\``) || !existsSync(resolve(SKILL_DIR, ref)))
  assert.deepEqual(problems, [])
})

test('structure: each type reference has notation and anti-patterns sections', () => {
  const lacking = DIAGRAM_TYPES.filter((type) => {
    const text = read(join(SKILL_DIR, 'references', `${type}.md`))
    return !text.includes('\n## Notation\n') || !text.includes('\n## Anti-patterns\n')
  })
  assert.deepEqual(lacking, [])
})

test('evals: evals.json parses, has code and description cases', () => {
  const evals = JSON.parse(read(join(SKILL_DIR, 'evals', 'evals.json')) || '{}')
  const modes = new Set((evals.evals ?? []).map((entry) => entry.mode))
  assert.deepEqual([evals.skill_name, modes.has('code'), modes.has('description')], ['uml', true, true])
})

test('structure: every relative path in skills/uml resolves', () => {
  const broken = files(['.md']).flatMap((path) =>
    relativeRefs(read(path))
      .filter((ref) => !existsSync(resolve(dirname(path), ref)))
      .map((ref) => `${relative(SKILL_DIR, path)} -> ${ref}`)
  )
  assert.deepEqual(broken, [])
})

test('structure: shell blocks use $SKILL_DIR, no CLAUDE_SKILL_DIR', () => {
  const texts = files(['.md', '.json', '.mjs', '.js']).filter((path) => path !== fileURLToPath(import.meta.url)).map(read)
  const blocks = shellBlocks(skill).filter((block) => block.includes('uml.mjs'))
  const bare = blocks.filter((block) => !block.includes('"$SKILL_DIR/scripts/uml.mjs"'))
  assert.deepEqual([blocks.length > 0, bare, texts.some((text) => text.includes('CLAUDE_SKILL_DIR'))], [true, [], false])
})

test('structure: no comments in .mjs files', () => {
  const commented = files(['.mjs', '.js']).filter((path) =>
    read(path).split('\n').some((line) => /^\s*(\/\/|\/\*)/.test(line))
  )
  assert.deepEqual(commented.map((path) => relative(SKILL_DIR, path)), [])
})

test('structure: prose never says AI', () => {
  const offending = files(['.md', '.json']).filter((path) => /\bAI\b/.test(read(path)))
  assert.deepEqual(offending.map((path) => relative(SKILL_DIR, path)), [])
})

test('listing: README, both plugin.json list uml', () => {
  const readme = read(join(REPO, 'README.md'))
  const claude = JSON.parse(read(join(REPO, '.claude-plugin', 'plugin.json')))
  const codex = JSON.parse(read(join(REPO, '.codex-plugin', 'plugin.json')))
  assert.deepEqual(
    [readme.includes('\n### uml\n'), readme.includes("node --test 'skills/uml/scripts/*.test.mjs'"), /UML/.test(claude.description), /UML/.test(codex.description), /uml/.test(codex.interface.longDescription)],
    [true, true, true, true, true]
  )
})
