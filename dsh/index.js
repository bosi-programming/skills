/**
 * DeepSeek Harness plugin: serve this repository's skills from their own
 * directory instead of from a scanned root.
 *
 * `cordis.patch.yml` mounts this module as one row. `apply` registers a single
 * skill provider on `ctx.skills`, so the skills in `../skills/` reach the session
 * catalog without being copied into `~/.dsh/skills`, `~/.agents/skills`, or a
 * project's `.dsh/skills`.
 *
 * Implements the `SkillProvider` contract from `@deepseek-ai/dsh-skill`.
 */

import { readdir, readFile, stat } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'bosi-programming-skills'
export const inject = ['skills']

/** The `skills/` directory beside this module, wherever the package is installed. */
const SKILLS_DIR = fileURLToPath(new URL('../skills/', import.meta.url))
const PROVIDER = 'bosi-programming-skills'
const SOURCE = 'bundled'
/**
 * `BUNDLED_SKILL_RANK` from `@deepseek-ai/dsh-skill`, inlined to keep this
 * package dependency-free. Lower ranks win a duplicate skill name.
 */
const RANK = 600
const SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u
const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u
/** The boolean spellings the harness accepts; any other spelling drops the skill. */
const BOOLEANS = new Map([
  ['true', true],
  ['yes', true],
  ['on', true],
  ['1', true],
  ['false', false],
  ['no', false],
  ['off', false],
  ['0', false],
])
/** Both keys are negative: set, they take the skill *out* of a surface. */
const MODEL_DISABLE_KEYS = ['disable-model-invocation', 'disable_model_invocation']
const USER_INVOCATION_KEYS = ['user-invocable', 'user_invocable']

/**
 * Read the top-level scalars of a frontmatter block.
 *
 * A reader for the subset these skills use — plain scalars, `>`/`|` blocks, and
 * nested maps — rather than a YAML parser. A nested key is dropped with its
 * parent, so an indented `name:` cannot shadow the top-level one. `dsh/index.test.mjs`
 * holds this reader to every `SKILL.md` in the repository.
 *
 * @param raw - the text between the opening and closing `---` markers.
 * @returns each top-level key mapped to its scalar, or to `undefined` for a bare key.
 */
function readFields(raw) {
  const entries = []
  let current

  for (const line of raw.split(/\r?\n/u)) {
    const key = /^([A-Za-z][A-Za-z0-9_-]*):(.*)$/u.exec(line)
    if (key !== null) {
      current = { key: key[1], head: key[2].trim(), lines: [] }
      entries.push(current)
      continue
    }
    if (current === undefined) continue
    if (/^[ \t]/u.test(line)) current.lines.push(line.trim())
    else if (line.trim() !== '') current = undefined
  }

  const fields = new Map()
  for (const { key, head, lines } of entries) {
    if (head === '>' || head === '>-' || head === '|' || head === '|-') {
      fields.set(key, head.startsWith('>') ? lines.join(' ').trim() : lines.join('\n').trim())
    } else if (head === '') {
      fields.set(key, undefined)
    } else {
      fields.set(key, head.replace(/^(['"])([\s\S]*)\1$/u, '$2'))
    }
  }
  return fields
}

/**
 * Resolve one invocation control from the frontmatter.
 *
 * @param fields - the parsed frontmatter.
 * @param keys - the accepted spellings of the key.
 * @param fallback - the value the harness assumes when the key is absent.
 * @returns the parsed boolean, the fallback when the key is absent, or
 *   `undefined` when the key is present with a spelling the harness rejects.
 */
function readFlag(fields, keys, fallback) {
  const raw = keys.map((key) => fields.get(key)).find((value) => value !== undefined)
  if (raw === undefined) return fallback
  return typeof raw === 'string' ? BOOLEANS.get(raw.toLowerCase()) : undefined
}

/**
 * Parse one `SKILL.md` into the fields the catalog and the loader need.
 *
 * Exported so the test can hold this reader to frontmatter the repository's own
 * skills do not contain — the invocation keys in particular, whose polarity is
 * easy to invert and would otherwise fail silently, as a skill going quiet.
 *
 * @param contents - the whole file.
 * @returns the skill, or `undefined` when the file has no frontmatter block, no
 *   kebab-case `name`, no `description`, or a rejected boolean spelling.
 */
export function parseSkill(contents) {
  const block = FRONTMATTER.exec(contents)
  if (block === null) return undefined

  const fields = readFields(block[1])
  const skillName = fields.get('name')
  if (typeof skillName !== 'string' || !SKILL_NAME.test(skillName)) return undefined
  const description = fields.get('description')
  if (typeof description !== 'string' || description === '') return undefined
  const modelDisabled = readFlag(fields, MODEL_DISABLE_KEYS, false)
  const userInvocable = readFlag(fields, USER_INVOCATION_KEYS, true)
  if (modelDisabled === undefined || userInvocable === undefined) return undefined

  return {
    name: skillName,
    description,
    invocation: { modelInvocable: !modelDisabled, userInvocable },
    content: contents.slice(block[0].length).trim(),
  }
}

/**
 * Read every skill directory beside this module.
 *
 * A skill the harness would reject is skipped with a warning rather than
 * failing the catalog, which is what the first-party filesystem provider does.
 *
 * @returns the provider candidates, sorted by name.
 */
async function listSkills() {
  const entries = await readdir(SKILLS_DIR, { withFileTypes: true })
  const directories = entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()

  const candidates = []
  for (const skillName of directories) {
    const directory = join(SKILLS_DIR, skillName)
    const path = join(directory, 'SKILL.md')
    const info = await stat(path).catch(() => undefined)
    if (info?.isFile() !== true) continue

    const parsed = parseSkill(await readFile(path, 'utf8'))
    if (parsed === undefined) {
      console.warn(`${PROVIDER}: ${skillName}/SKILL.md is not a skill the harness can catalog`)
      continue
    }

    candidates.push({
      name: parsed.name,
      description: parsed.description,
      path,
      invocation: parsed.invocation,
      source: SOURCE,
      provider: PROVIDER,
      rank: RANK,
      locator: path,
      resourceBase: { kind: 'directory', path: directory },
    })
  }

  return candidates
}

/**
 * Register the bundled provider with the skill registry.
 *
 * Discovery is cached per scope and this plugin registers no watcher, so an edit
 * to a `SKILL.md` frontmatter reaches the catalog on the next session. An edit to
 * a skill *body* reaches it immediately: the registry calls `get` on every load.
 *
 * @param ctx - the Cordis context carrying `ctx.skills`.
 */
export function apply(ctx) {
  ctx.skills.registerProvider(() => ({
    name: PROVIDER,
    list: () => listSkills(),
    async get(candidate, options) {
      const parsed = parseSkill(
        await readFile(candidate.locator, { encoding: 'utf8', signal: options.signal }),
      )
      if (parsed === undefined || parsed.name !== candidate.name) return undefined
      return {
        name: parsed.name,
        description: parsed.description,
        path: candidate.locator,
        invocation: parsed.invocation,
        source: SOURCE,
        provider: PROVIDER,
        resourceBase: candidate.resourceBase,
        content: parsed.content,
      }
    },
  }))
}
