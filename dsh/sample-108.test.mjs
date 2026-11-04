import assert from 'node:assert/strict'
import { test } from 'node:test'

import { isStage } from './index.js'

test('isStage is true for a skill that ships a stage.json', async () => {
  assert.equal(await isStage('code-docs'), true)
})

test('isStage is false for a skill without a stage.json, or no skill at all', async () => {
  assert.equal(await isStage('feature-recipe'), false)
  assert.equal(await isStage('no-such-skill'), false)
})
