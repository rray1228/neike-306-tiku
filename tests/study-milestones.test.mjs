import test from 'node:test'
import assert from 'node:assert/strict'
import { advancePractice, completePracticeGroup, groupHasResponses, HALF_HOUR, IDLE_LIMIT, newPractice, NOTICE_COOLDOWN, restorePractice, takePracticeNotice } from '../src/study-milestones.js'

const groupIds = n => Array.from({ length: n }, (_, i) => `med:${i}`)
const minutes = n => n * 60_000

test('twenty distinct completed groups trigger a notice; redo does not inflate progress', () => {
  let state = newPractice(1000)
  for (const id of groupIds(19)) state = completePracticeGroup(state, id, 2000)
  state = completePracticeGroup(state, 'med:0', 3000)
  assert.equal(takePracticeNotice(state, 3000), null)
  state = completePracticeGroup(state, 'surgery:0', 4000)
  const result = takePracticeNotice(state, 4000)
  assert.equal(result.notice.kind, 'groups')
  assert.equal(result.notice.groups, 20)
  assert.equal(takePracticeNotice({ ...result.state, groups: groupIds(39) }, 4000 + NOTICE_COOLDOWN), null)
  assert.equal(takePracticeNotice({ ...result.state, groups: groupIds(40) }, 4000 + NOTICE_COOLDOWN).notice.groups, 40)
})

test('forty-five minutes is active time, with background, rest and inactivity excluded', () => {
  const initial = newPractice(1000)
  assert.equal(advancePractice(initial, 1000, minutes(45) + 1000, true).activeMs, IDLE_LIMIT)
  assert.equal(advancePractice(initial, 1000, 10000, false).activeMs, 0)
  assert.equal(advancePractice({ ...initial, paused: true }, 1000, 10000, true).activeMs, 0)
  let state = initial
  for (let minute = 0; minute < 44; minute++) {
    const from = 1000 + minutes(minute)
    state = advancePractice({ ...state, lastInteractionAt: from }, from, from + minutes(1), true)
  }
  assert.equal(takePracticeNotice(state, minutes(44) + 1000), null)
  const timed = takePracticeNotice({ ...state, activeMs: minutes(45) }, minutes(45) + 1000)
  assert.equal(timed.notice.kind, 'time')
  assert.equal(timed.notice.minutes, 45)
  assert.equal(takePracticeNotice({ ...timed.state, activeMs: minutes(90) - 1 }, minutes(90) + 1000), null)
  assert.equal(takePracticeNotice({ ...timed.state, activeMs: minutes(90) }, minutes(90) + 1000).notice.kind, 'time')
})

test('simultaneous thresholds merge and cooldown avoids back-to-back notices', () => {
  const state = { ...newPractice(1000), groups: groupIds(20), activeMs: minutes(45) }
  const both = takePracticeNotice(state, minutes(45) + 1000)
  assert.equal(both.notice.kind, 'both')
  const later = { ...both.state, groups: groupIds(40) }
  assert.equal(takePracticeNotice(later, minutes(45) + 2000), null)
  assert.equal(takePracticeNotice(later, minutes(45) + 1000 + NOTICE_COOLDOWN).notice.kind, 'groups')
})

test('reload preserves the schedule; a long break starts a new practice session', () => {
  const state = { ...newPractice(1000), groups: ['med:1'], activeMs: 5000 }
  assert.deepEqual(restorePractice(JSON.stringify(state), 2000), state)
  assert.deepEqual(restorePractice(JSON.stringify(state), HALF_HOUR + 1000), newPractice(HALF_HOUR + 1000))
  assert.deepEqual(restorePractice('invalid', 2000), newPractice(2000))
  assert.deepEqual(completePracticeGroup(state, 'med:2', HALF_HOUR + 1000).groups, ['med:2'])
})

test('an earlier time notice does not advance the group threshold', () => {
  const timed = takePracticeNotice({ ...newPractice(1000), groups: groupIds(19), activeMs: minutes(45) }, minutes(45) + 1000)
  const grouped = takePracticeNotice({ ...timed.state, groups: groupIds(20) }, minutes(45) + 1000 + NOTICE_COOLDOWN)
  assert.equal(grouped.notice.kind, 'groups')
  assert.equal(grouped.state.nextActiveMs, timed.state.nextActiveMs)
})

test('the previous random schedule migrates without losing practice or popping early', () => {
  const old = { ...newPractice(1000), version: 1, groups: groupIds(12), activeMs: minutes(35), nextGroups: 12, nextActiveMs: minutes(35) }
  const restored = restorePractice(JSON.stringify(old), 2000)
  assert.deepEqual(restored.groups, old.groups)
  assert.equal(restored.activeMs, old.activeMs)
  assert.equal(takePracticeNotice(restored, 2000), null)
  assert.equal(takePracticeNotice({ ...restored, groups: groupIds(20) }, 2000).notice.kind, 'groups')
  assert.equal(takePracticeNotice({ ...restored, activeMs: minutes(45) }, 2000).notice.kind, 'time')
})

test('empty submissions do not count; fill blanks, sorting, and drafts must be completed', () => {
  assert.equal(groupHasResponses({ stems: [{ answerMode: '多选', answer: ['A'] }] }, {}), false)
  assert.equal(groupHasResponses({ stems: [{ answerMode: '多选', answer: ['A'] }] }, { 0: ['B'] }), true)
  assert.equal(groupHasResponses({ stems: [{ answerMode: '填空', answer: ['1', '45'] }] }, { 0: ['1', ''] }), false)
  assert.equal(groupHasResponses({ stems: [{ answerMode: '填空', answer: ['1', '45'] }] }, { 0: ['0', '45'] }), true)
  assert.equal(groupHasResponses({ stems: [{ answerMode: '排序', answer: ['A', 'B'] }] }, { 0: ['A'] }), false)
  assert.equal(groupHasResponses({ stems: [{ answerMode: '自评' }] }, { 0: ['  '] }), false)
})
