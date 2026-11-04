import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'

const data = JSON.parse(readFileSync(new URL('../src/data/med-foundation-mock-exam-data.json', import.meta.url)))
const group = data.groups.find(group => group.id === 'med-foundation-mock-exam-20260907-q041')

test('hereditary jaundice retains its original B answer and explains all four lecture options', () => {
  assert.equal(group.stems.length, 1)
  assert.deepEqual(group.options.map(option => option.key), ['A', 'B', 'C', 'D'])
  assert.deepEqual(group.stems[0].answer, ['B'])
  assert.equal(group.stems[0].answerMode, '单选')
  assert.equal(group.answerRevision, undefined)
  const explanation = group.stems[0].explanation
  for (const disease of ['Gilbert', 'Crigler-Najjar', 'Rotor', 'Dubin-Johnson']) assert.ok(explanation.includes(disease))
  assert.match(explanation, /UCB甚高、核黄疸、预后极差/)
  assert.match(explanation, /Rotor综合征：.*摄取、排泄障碍，血UCB和CB均可升高/)
  assert.match(explanation, /Dubin-Johnson综合征：.*排泄障碍，血CB升高/)
  assert.ok(group.stems[0].knowledgeConnections.every(point => !/必会项|易混对照|ALA|磷酸吡哆醛|睾酮/.test(point)))
})

test('the lecture opens the actual four-disease table and provides full per-question reference pages', () => {
  assert.equal(group.lectureEvidence.page, 2)
  assert.equal(group.lectureEvidence.sourceFile, '10 27考研：生化 胆色素代谢 核心-真题-串联-导图 天天师兄.pdf')
  assert.match(group.lectureEvidence.image, /reviewed-mocks-20261104\/biochemistry-[a-f0-9]+-p002\.webp/)
  assert.deepEqual(group.lectureEvidence.optionKeys, ['A', 'B', 'C', 'D'])
  assert.equal(group.lectureEvidencePages.length, 2)
  assert.deepEqual(group.stems[0].lectureEvidencePages, group.lectureEvidencePages)
  for (const page of group.lectureEvidencePages) {
    assert.ok(existsSync(new URL(`../public/${page.image}`, import.meta.url)), page.image)
    assert.deepEqual(page.questionNumbers, [41])
    assert.equal(page.sourceSubject, 'biochemistry')
    assert.ok(page.knowledgePoints.length >= 2)
  }
})
