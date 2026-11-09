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

test('the final question has no closing note in its options and keeps its original key', () => {
  const finalQuestion = groups.find(group => group.sourceQuestion === '165')
  assert.deepEqual(finalQuestion.options.map(({ key, label }) => [key, label]), [
    ['A', '髋臼发育不良'],
    ['B', '股骨颈前倾角增大'],
    ['C', '关节韧带松弛症'],
    ['D', '股骨头发育不良'],
  ])
  assert.deepEqual(finalQuestion.stems[0].answer, ['A', 'C'])
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

test('questions 103–105 keep the T₉ level intact in the shared stem and options', () => {
  const [q103, q104, q105] = [103, 104, 105].map(number =>
    groups.find(group => Number(group.sourceQuestion) === number))
  assert.deepEqual(q103.options.map(option => option.label), ['T₉肿瘤', 'T₉结核', 'T₉转移瘤', 'T₉骨髓炎'])
  const stems = [q103, q104, q105].map(group => group.stems[0])
  assert.equal(new Set(stems.map(stem => stem.sharedText)).size, 1)
  assert.match(stems[0].sharedText, /T₉压痛，叩痛明显/)
  assert.match(stems[0].sharedText, /T₉椎弓根及椎体后缘/)
  assert.deepEqual(stems.map(stem => stem.answer), [['C'], ['D'], ['C']])
})

test('questions 106–107 retain the shared case and display intact lumbar levels', () => {
  const [q106, q107] = ['106', '107'].map(number => groups.find(group => group.sourceQuestion === number))
  assert.deepEqual(q106.options.map(({ key, label }) => [key, label]), [
    ['A', 'L₂–L₃'],
    ['B', 'L₃–L₄'],
    ['C', 'L₄–L₅'],
    ['D', 'L₅–S₁'],
  ])
  assert.equal(q106.stems[0].sharedText, q107.stems[0].sharedText)
  assert.deepEqual([q106, q107].map(group => group.stems[0].answer), [['D'], ['D']])
  assert.equal(q107.options.find(option => option.key === 'D').label, '髓核摘除术')
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
