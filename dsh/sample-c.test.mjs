import assert from 'node:assert/strict'
import { test } from 'node:test'

import { apply, skillCount } from './index.js'

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

test('skillCount matches the catalog length', async () => {
  const candidates = await mount().list({})

  assert.equal(await skillCount(), candidates.length)
})

test('skillCount is a whole number above twenty', async () => {
  const count = await skillCount()

  assert.equal(Number.isInteger(count), true)
  assert.equal(count > 20, true)
})
