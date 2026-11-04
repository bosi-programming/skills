import { test } from 'node:test'
import assert from 'node:assert/strict'
import { isStage } from './index.js'

test('isStage is true for a skill that ships a stage.json', async () => {
  assert.equal(await isStage('code-docs'), true)
  assert.equal(await isStage('review-fix'), true)
})

test('isStage is false for a skill without a stage.json', async () => {
  assert.equal(await isStage('feature-recipe'), false)
})

test('isStage is false for a skill that does not exist', async () => {
  assert.equal(await isStage('no-such-skill'), false)
})
