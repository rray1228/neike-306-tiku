import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'

const root = new URL('../', import.meta.url)
const subjects = ['physiology', 'biochemistry', 'pathology', 'med', 'surgery']
const groups = subjects.flatMap(subject => JSON.parse(readFileSync(new URL(`src/data/${subject}-foundation-mock-exam-data.json`, root))).groups)

test('foundation mock contains exactly 165 complete, unique questions', () => {
  assert.equal(groups.length, 165)
  assert.deepEqual(groups.map(group => Number(group.sourceQuestion)).sort((a, b) => a - b), Array.from({ length: 165 }, (_, index) => index + 1))
  for (const group of groups) {
    assert.equal(group.options.length, 4, group.sourceQuestion)
    assert.ok(group.options.every(option => option.label.trim()), group.sourceQuestion)
    assert.ok(group.stems[0].text.trim(), group.sourceQuestion)
    assert.ok(group.stems[0].explanation.startsWith('正确答案：') || group.lectureEvidenceNotice, group.sourceQuestion)
  }
})

test('shared clinical vignettes are separated from subquestions without parser debris', () => {
  assert.equal(groups.filter(group => group.stems[0].sharedText).length, 40)
  const debris = /\[共用题干\]|\[\d+题\]|题共用题干|ttsx|\d{4}N\d+|真题解析[·・]/
  for (const group of groups) assert.doesNotMatch(JSON.stringify(group), debris, group.sourceQuestion)
  const question81 = groups.find(group => group.sourceQuestion === '81').stems[0]
  assert.match(question81.sharedText, /间歇性乏力、腹胀/)
  assert.match(question81.text, /意识模糊/)
  assert.doesNotMatch(question81.text, /间歇性乏力、腹胀/)
})

test('rewritten explanations and lecture evidence remain tied to the tested point', () => {
  const question51 = groups.find(group => group.sourceQuestion === '51')
  assert.match(question51.stems[0].explanation, /机械性肠梗阻/)
  assert.match(question51.stems[0].explanation, /气液平/)
  assert.ok(question51.lectureSummary.some(point => /立位腹部X线片/.test(point)))
  for (const group of groups) {
    for (const evidence of group.lectureEvidencePages || []) {
      assert.ok(existsSync(new URL(`public/${evidence.image}`, root)), `${group.sourceQuestion}: ${evidence.image}`)
    }
  }
})
