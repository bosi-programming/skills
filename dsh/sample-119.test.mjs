import { test } from 'node:test'
import assert from 'node:assert/strict'
import { isStage } from './index.js'

test('isStage is true for a skill that ships a stage.json', async () => {
  assert.equal(await isStage('code-docs'), true)
  assert.equal(await isStage('review-fix'), true)
})
