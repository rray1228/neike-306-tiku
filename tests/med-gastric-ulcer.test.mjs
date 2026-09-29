import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))

test('gastric ulcer includes impaired mucosal defense per lecture 16 page 1', () => {
  const group = data.groups.find(g => g.id === 'p23-g1')
  assert.equal(group.lectureEvidence.lectureId, 'lecture-16')
  assert.equal(group.lectureEvidence.page, 1)
  assert.equal(group.options.find(o => o.key === 'I').label, '黏膜屏障功能减弱为主')
  assert.deepEqual(group.stems[0].answer, ['A', 'C', 'E', 'I'])
  assert.equal(group.stems[0].answerMode, '多选')
  assert.deepEqual(group.stems[1].answer, ['B', 'D', 'F', 'G', 'H'])
})

test('answer-repair override preserves gastric ulcer option I', () => {
  const repair = readFileSync(new URL('../scripts/repair_med_answers.py', import.meta.url), 'utf8')
  assert.match(repair, /"p23-g1:0": list\("ACEI"\)/)
})
