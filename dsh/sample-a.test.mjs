import assert from 'node:assert/strict'
import { test } from 'node:test'

import { hasSkill } from './index.js'

test('hasSkill finds a skill the repository ships', async () => {
  assert.equal(await hasSkill('code'), true)
})

test('hasSkill refuses a name the repository does not ship', async () => {
  assert.equal(await hasSkill('no-such-skill'), false)
})

test('hasSkill refuses part of a name the repository ships', async () => {
  assert.equal(await hasSkill('cod'), false)
})
