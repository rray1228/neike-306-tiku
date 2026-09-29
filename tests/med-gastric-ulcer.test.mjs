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

test('perforation questions have explicit non-overlapping scopes in one group', () => {
  const group = data.groups.find(g => g.id === 'p24-g1')
  assert.equal(group.answerRevision, 'perforation-v2')
  assert.equal(group.stems.length, 8)
  assert.deepEqual(group.stems.slice(1, 6).map(s => [s.text, s.answer.join('')]), [
    ['穿孔：相关用药背景', 'A'],
    ['急性穿孔：临床表现与体征', 'DGHJRTV'],
    ['慢性穿孔（穿透性溃疡）：临床表现', 'CMO'],
    ['急性穿孔：检查及阳性发现', '②⑤'],
    ['急性穿孔：初始处理及手术选择（注意选项中的适用条件）', 'Y⑧'],
  ])
  assert.equal(group.stems[1].answerMode, '单选')
  assert.ok(group.stems.slice(2, 6).every(s => s.answerMode === '多选'))
  assert.deepEqual([group.stems[0], ...group.stems.slice(6)].map(s => s.answer.join('')), ['BFX⑦', 'EINWY①③⑥', 'KLPQSU④'])
  assert.match(group.options.find(o => o.key === '⑧').label, /饱餐后或弥漫性腹膜炎/)
})
