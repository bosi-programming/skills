import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { createIdleTimer } from './idle.mjs'

const MINUTE = 60_000

beforeEach(() => mock.timers.enable({ apis: ['setTimeout'] }))
afterEach(() => mock.timers.reset())

test('idle: fires after N minutes with no touch', () => {
  const onIdle = mock.fn()
  createIdleTimer({ minutes: 30, onIdle })
  mock.timers.tick(30 * MINUTE)
  assert.equal(onIdle.mock.callCount(), 1)
})

test('idle: does not fire before N minutes', () => {
  const onIdle = mock.fn()
  createIdleTimer({ minutes: 30, onIdle })
  mock.timers.tick(30 * MINUTE - 1)
  assert.equal(onIdle.mock.callCount(), 0)
})

test('idle: touch resets the timer', () => {
  const onIdle = mock.fn()
  const timer = createIdleTimer({ minutes: 30, onIdle })
  mock.timers.tick(20 * MINUTE)
  timer.touch()
  mock.timers.tick(20 * MINUTE)
  assert.equal(onIdle.mock.callCount(), 0)
})

test('idle: stop cancels the timer', () => {
  const onIdle = mock.fn()
  const timer = createIdleTimer({ minutes: 1, onIdle })
  timer.stop()
  mock.timers.tick(MINUTE)
  assert.equal(onIdle.mock.callCount(), 0)
})
