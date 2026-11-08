import { readFileSync, existsSync } from 'node:fs'
import assert from 'node:assert/strict'
import test from 'node:test'

const bank = JSON.parse(readFileSync(new URL('../src/data/biochemistry-lecture9-data.json', import.meta.url)))
const analogues = bank.groups.find(g => g.id === 'bio-09-07')
const group = bank.groups.find(g => g.id === 'bio-09-08')
const processes = bank.groups.find(g => g.id === 'bio-09-08-focus-2')
const activation = bank.groups.find(g => g.id === 'bio-09-08-focus-3')
const labels = (g, n) => g.stems[n - 1].answer.map(k => g.options.find(o => o.key === k).label)

test('the 5-FU analogue answer follows the lecture table without changing the other matches', () => {
  assert.deepEqual(analogues.stems.map((_, i) => labels(analogues, i + 1)), [
    ['次黄嘌呤'], ['次黄嘌呤'], ['胞苷'], ['胸腺嘧啶（T）'], ['叶酸'], ['谷氨酰胺'],
  ])
  const s = analogues.stems[3]
  assert.match(s.text, /按讲义抗代谢物表/)
  assert.equal(s.answerRaw, 'A')
  assert.equal(s.answerMode, '单选')
  assert.match(s.explanation, /T（胸腺嘧啶）/)
  assert.equal(analogues.lectureEvidence.sourceBookPage, 65)
  assert.equal(analogues.lectureEvidence.sourcePdfPage, 80)
  assert.equal(analogues.answerRevision, 'bio-5fu-analogue-20261108-v2')
})

test('six antimetabolites have separate target and process questions', () => {
  assert.equal(bank.groups.length, 15)
  assert.equal(bank.groups.flatMap(g => g.stems).length, 54)
  assert.equal(group.stems.length, 6)
  assert.equal(processes.stems.length, 6)
  assert.equal(activation.stems.length, 1)
  for (const g of [group, processes, activation]) {
    assert.equal(g.sourceGroupId, 'bio-09-08')
    assert.equal(g.answerRevision, 'bio-focused-20261017-v1')
    assert.ok(g.options.length <= 7)
    for (const s of g.stems) {
      assert.equal(s.answerRaw, s.answer.join('、'))
      assert.equal(s.answerMode, s.answer.length > 1 ? '多选' : '单选')
    }
  }
  assert.doesNotMatch(group.options.map(o => o.label).join(' '), /次黄嘌呤|嘌呤核苷酸从头合成|结构类似物/)
})

test('activation, targets and overlapping processes remain correct after relettering', () => {
  assert.deepEqual(labels(group, 1), ['PRPP酰胺转移酶'])
  assert.deepEqual(labels(group, 2), ['黄嘌呤氧化酶'])
  assert.deepEqual(labels(group, 3), ['DNA聚合酶'])
  assert.deepEqual(labels(group, 4), ['胸苷酸合酶'])
  assert.deepEqual(labels(group, 5), ['二氢叶酸还原酶（DHFR）'])
  assert.deepEqual(labels(group, 6), ['CPS-Ⅱ', 'PRPP酰胺转移酶'])
  assert.deepEqual(labels(activation, 1), ['HGPRT'])
  assert.deepEqual(labels(processes, 5), ['嘌呤核苷酸从头合成', 'dTMP合成（dUMP → dTMP）'])
  assert.deepEqual(labels(processes, 6), ['嘌呤核苷酸从头合成', '嘧啶核苷酸从头合成'])
})

test('all split groups retain the corrected antimetabolite table reference', () => {
  for (const g of [group, processes, activation]) {
    const evidence = g.lectureEvidence
    assert.equal(evidence.sourcePdfPage, 80)
    assert.equal(evidence.sourceBookPage, 65)
    assert.equal(evidence.page, 6)
    assert.match(evidence.pageLabel, /65.*80/)
    assert.match(evidence.image, /lecture-09-page-06.webp$/)
    assert.ok(existsSync(new URL(`../public/${evidence.image}`, import.meta.url)))
  }
})
