import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const base = read('med-data')
const homework = read('med-teacher-supplement')
const exam = read('med-stage-exam-data')
const group = id => [...base.groups, ...homework.groups, ...exam.groups].find(g => g.id === id)
const answers = id => group(id).stems.map(s => s.answer.join(''))

test('hemolysis source pools retain their case-sensitive option letters and separate meanings', () => {
  assert.equal(group('p45-g1').options.map(o => o.key).join(''), 'ABCDEFGHIJK')
  assert.equal(group('p45-g2').options.map(o => o.key).join(''), 'abcdefg')
  assert.deepEqual(answers('p45-g1'), ['ABEFHJ', 'CDEGHIK'])
  assert.deepEqual(answers('p45-g2'), ['aceg', 'bcdef'])
  assert.deepEqual(answers('p45-g4'), ['BDFGIJK', 'ACEHJ'])
  assert.equal(group('p45-g3').options.map(o => o.key).join(''), 'ABCDEFGHIJ')
  assert.equal(group('p45-g3').options.find(o => o.key === 'J').label, '溶血性黄疸')
  assert.deepEqual(answers('p45-g3').slice(1), ['BDF', 'ACEGHIJ'])
})

test('a source row without matching options is retained but not graded using an invented K', () => {
  const s = group('p45-g3').stems[0]
  assert.equal(s.text, '红细胞自身缺陷和外部异常')
  assert.deepEqual(s.answer, [])
  assert.equal(s.answerMode, '待核对')
  assert.equal(s.answerState, '待原题页核对')
})

test('summary includes lecture-backed splenectomy for warm AIHA and glucocorticoids for PNH', () => {
  assert.deepEqual(answers('p46-g1'), ['ACOQU', 'FHKP', 'ADJL', 'AIMNOU', 'EGNR', 'BGILST'])
  assert.equal(group('p46-g1').options.map(o => o.key).join(''), 'ABCDEFGHIJKLMNOPQRSTU')
  assert.equal(group('p46-g1').stems[3].sourceAnswerRaw, 'AIMNO')
  assert.equal(group('p46-g1').stems[5].sourceAnswerRaw, 'BGSTL')
})

test('PNH homework diagnosis is corrected without treating uncertain complication wording as verified', () => {
  const [diagnosis, complication] = group('med-teacher-06-07-08').stems
  assert.deepEqual(diagnosis.answer, ['q7-C'])
  assert.equal(diagnosis.answerRaw, 'C')
  assert.equal(diagnosis.sourceAnswerRaw, 'B')
  assert.equal(diagnosis.answerState, '讲义核对答案')
  assert.equal(complication.sourceAnswerRaw, 'C')
  assert.deepEqual(complication.answer, [])
  assert.equal(complication.answerMode, '待核对')
  assert.equal(complication.answerState, '待原题页核对')
  assert.equal(group('med-stage-exam-2026-09-q086').stems[0].answerRaw, 'C')
})

test('hemolysis evidence covers the actual pages and corrected attempts have a fresh revision', () => {
  for (const [id, pages] of [['p45-g3', [2, 3]], ['p46-g1', [4, 5]]]) {
    const g = group(id)
    assert.deepEqual(g.lectureEvidence.pages, pages)
    assert.ok(existsSync(resolve('public', g.lectureEvidence.image)), id)
    assert.equal(g.answerRevision, 'hemolysis-20261011')
  }
  assert.equal(group('med-teacher-06-07-08').answerRevision, 'hemolysis-20261011')
  for (const g of [...base.groups, ...homework.groups, ...exam.groups].filter(g => g.lectureIds.includes('lecture-30'))) {
    assert.equal(g.topic, '血液', g.id)
    assert.deepEqual(g.lectureIds, ['lecture-30'], g.id)
    for (const s of g.stems) {
      const choices = g.options.filter(o => !s.optionCategory || o.category === s.optionCategory)
      assert.ok(s.answer.every(key => choices.some(o => o.key === key)), g.id)
      if (s.answer.length) assert.equal(s.answerMode, s.answer.length > 1 ? '多选' : '单选', g.id)
    }
  }
})
