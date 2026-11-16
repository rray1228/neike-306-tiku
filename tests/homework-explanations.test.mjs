import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const totals = { med: [126, 116], surgery: [103, 37], pathology: [90, 51], physiology: [172, 62], biochemistry: [23, 25] }
const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))

test('all 805 homework and stage questions have individual explanations and concrete connections', () => {
  let total = 0
  for (const [subject, counts] of Object.entries(totals)) {
    for (const [index, suffix] of ['teacher-supplement', 'stage-exam-data'].entries()) {
      const bank = read(`${subject}-${suffix}`)
      const stems = bank.groups.flatMap(g => g.stems)
      assert.equal(stems.length, counts[index], `${subject}-${suffix}`)
      assert.equal(new Set(stems.map(s => s.explanation)).size, stems.length, 'no repeated filler explanation')
      for (const stem of stems) {
        assert.ok(stem.explanation?.length > 30, stem.text)
        assert.ok(stem.knowledgeConnections?.length >= 1, stem.text)
        assert.ok(stem.knowledgeConnections.every(c => c.trim().length > 5), stem.text)
        assert.doesNotMatch(stem.explanation, /作为AI|存在争议|有表述争议|需进一步复核|现代指南/)
      }
      total += stems.length
    }
  }
  assert.equal(total, 805)
})

test('answer revisions retain source keys and invalidate previous grading storage', () => {
  for (const [file, id, original, corrected, revision] of [
    ['surgery-teacher-supplement', 'surgery-teacher-06-03', 'C', 'B', 'lecture-analysis-20261017-v1'],
    ['physiology-teacher-supplement', 'phys-teacher-14-06', 'ABD', 'ABD', 'rem-teacher-key-20261116'],
  ]) {
    const group = read(file).groups.find(g => g.id === id)
    assert.equal(group.stems[0].sourceAnswerRaw, original)
    assert.equal(group.stems[0].answerRaw, corrected)
    assert.deepEqual(group.stems[0].answer, corrected.split(''))
    assert.equal(group.answerRevision, revision)
  }
})
