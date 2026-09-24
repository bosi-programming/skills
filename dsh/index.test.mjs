/**
 * Hold the DeepSeek Harness plugin to the repository it actually ships.
 *
 * The provider reads `SKILL.md` frontmatter with a reader for the subset these
 * skills use, not a YAML parser, so the guard that matters is this one: run the
 * real provider over the real `skills/` directory and assert what the catalog
 * has to contain. Run with `node --test dsh/`.
 */

import assert from 'node:assert/strict'
import { test } from 'node:test'

import { apply, inject, name, parseSkill } from './index.js'

/** Every skill this package must publish, in catalog order; add a skill, add it here. */
const SKILLS = [
  'better-code-review',
  'code-standards',
  'code-visualizer',
  'docs-visualizer',
  'epistemic-action',
  'feature-recipe',
  'maestri-workflow',
  'recipe-relay',
  'setup',
  'summarize-llm-response',
  'week-summary',
  'work-summary',
]

/** Mount the plugin against a stand-in registry and return the provider it registers. */
function mount() {
  let provider
  apply({
    skills: {
      registerProvider: (create) => {
        provider = create({ invalidate() {} })
      },
    },
  })
  return provider
}

test('registers one provider that needs the skill registry', () => {
  assert.equal(name, 'bosi-programming-skills')
  assert.deepEqual(inject, ['skills'])
  assert.equal(mount().name, 'bosi-programming-skills')
})

test('catalogs every skill in the repository', async () => {
  const candidates = await mount().list({})

  assert.deepEqual(
    candidates.map((candidate) => candidate.name),
    SKILLS,
  )
  for (const candidate of candidates) {
    assert.equal(candidate.provider, 'bosi-programming-skills')
    assert.equal(candidate.source, 'bundled')
    assert.equal(candidate.rank, 600)
    assert.match(candidate.path, /\/skills\/[^/]+\/SKILL\.md$/u)
    assert.deepEqual(candidate.resourceBase, {
      kind: 'directory',
      path: candidate.path.replace(/\/SKILL\.md$/u, ''),
    })
    assert.ok(candidate.description.length > 20, `${candidate.name} has no description`)
  }
})

test('reads a folded description as one line', async () => {
  const candidates = await mount().list({})
  const summarize = candidates.find((candidate) => candidate.name === 'summarize-llm-response')

  assert.equal(
    summarize.description,
    'Output gate for anything a human will read. Run it before you summarize findings '
      + 'or an investigation, before you create or update a Linear issue or comment, a '
      + 'Todoist task, a Notion page, a Slack message, or any technical markdown doc '
      + '(README, ADR, runbook, changelog, investigation notes). It fixes the shape — '
      + 'bullets over prose, evidence inline, action items as a checklist, no filler — '
      + 'and adds the attribution tag the destination requires. Skip it for yes/no '
      + 'answers, single-line factual replies, code-only output, clarifying questions, '
      + 'git commit messages and PR descriptions.',
  )
})

test('leaves every skill reachable from the model and from a person', async () => {
  const candidates = await mount().list({})

  for (const candidate of candidates) {
    assert.deepEqual(
      candidate.invocation,
      { modelInvocable: true, userInvocable: true },
      candidate.name,
    )
  }
})

test('reads the invocation keys the harness grammar allows', () => {
  const skill = (frontmatter) =>
    parseSkill(`---\nname: sample\ndescription: A sample skill.\n${frontmatter}---\n\nBody.\n`)

  assert.deepEqual(skill('disable-model-invocation: true\n').invocation, {
    modelInvocable: false,
    userInvocable: true,
  })
  assert.deepEqual(skill('disable_model_invocation: yes\n').invocation, {
    modelInvocable: false,
    userInvocable: true,
  })
  assert.deepEqual(skill('user-invocable: off\n').invocation, {
    modelInvocable: true,
    userInvocable: false,
  })
  assert.deepEqual(skill('disable-model-invocation: false\n').invocation, {
    modelInvocable: true,
    userInvocable: true,
  })
  assert.equal(skill('disable-model-invocation: maybe\n'), undefined)
})

test('refuses frontmatter the catalog cannot use', () => {
  assert.equal(parseSkill('No frontmatter here.\n'), undefined)
  assert.equal(parseSkill('---\ndescription: No name.\n---\n\nBody.\n'), undefined)
  assert.equal(parseSkill('---\nname: Not Kebab\ndescription: A name.\n---\n\nBody.\n'), undefined)
  assert.equal(parseSkill('---\nname: sample\n---\n\nBody.\n'), undefined)
})

test('loads a body without its frontmatter', async () => {
  const candidates = await mount().list({})
  const candidate = candidates.find((entry) => entry.name === 'better-code-review')
  const definition = await mount().get(candidate, {})

  assert.equal(definition.name, 'better-code-review')
  assert.equal(definition.description, candidate.description)
  assert.equal(definition.provider, 'bosi-programming-skills')
  assert.equal(definition.content.includes('adapted-by'), false)
  assert.ok(definition.content.startsWith('Three-axis review of the diff between `HEAD`'))
})

test('refuses a candidate whose file no longer matches it', async () => {
  const candidates = await mount().list({})
  const relay = candidates.find((entry) => entry.name === 'recipe-relay')
  const candidate = { ...relay, name: 'renamed' }

  assert.equal(await mount().get(candidate, {}), undefined)
})
