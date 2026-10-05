import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const group = data.groups.find(g => g.id === 'p30-g1')

test('IBS question 14 includes both short-term drugs from lecture 19 page 1', () => {
  assert.equal(group.stems.length, 14)
  assert.equal(group.stems[13].text, '短期用')
  assert.deepEqual(group.stems[13].answer, ['A', 'I'])
  assert.equal(group.stems[13].answerMode, '多选')
  assert.equal(group.options.find(o => o.key === 'A').label, '利福昔明')
  assert.equal(group.options.find(o => o.key === 'I').label, '抗胆碱药')
  assert.equal(group.lectureEvidence.lectureId, 'lecture-19')
  assert.equal(group.lectureEvidence.page, 1)
})

test('IBS has only its original A-Q drug options, with no spurious short-term option', () => {
  assert.deepEqual(group.options.map(o => o.key), Array.from('ABCDEFGHIJKLMNOPQ'))
  for (const s of group.stems) {
    assert.ok(s.answer.every(key => group.options.some(o => o.key === key)))
  }
  assert.deepEqual(group.stems.slice(0, 13).map(s => s.answer.join('')), [
    'BDFHI', 'CEKL', 'GNO', 'GJP', 'AMQ', 'A', 'BDFH', 'CK', 'EL', 'N', 'GO', 'JP', 'MQ',
  ])
  const repair = readFileSync(new URL('../scripts/repair_med_answers.py', import.meta.url), 'utf8')
  assert.doesNotMatch(repair, /"p30-g1": \[option\("T"/)
})
