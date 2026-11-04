import test from 'node:test'
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync } from 'node:fs'

const files = readdirSync(new URL('../src/data/', import.meta.url))
  .filter(name => /-(foundation-mock-exam|sprint-exam)-data.json$/.test(name)).sort()
const groups = files.flatMap(name => JSON.parse(readFileSync(new URL(`../src/data/${name}`, import.meta.url))).groups)
const question = (paper, number) => groups.find(group => group.id.includes(paper) && Number(group.sourceQuestion) === number)

test('both papers retain every original question, option, answer and study-record address', () => {
  const rows = groups.map(g => ({
    id: g.id, sourceKey: g.sourceKey, kind: g.kind, options: g.options, sharedStem: g.sharedStem,
    stems: g.stems.map(s => ({ text: s.text, sharedText: s.sharedText, answer: s.answer,
      answerRaw: s.answerRaw, answerMode: s.answerMode, answerState: s.answerState, number: s.number })),
  }))
  assert.equal(rows.length, 330)
  assert.equal(createHash('sha256').update(JSON.stringify(rows)).digest('hex'),
    '4a845d9386a35bfde001264a174710575f9d889a843c8cbaea71addef38dc299')
})

test('every question has reviewed, specific notes instead of OCR paragraph templates', () => {
  const records = Object.assign({}, ...['med', 'phys_bio', 'path_surg'].map(name =>
    JSON.parse(readFileSync(new URL(`../scripts/reviewed_mock_${name}.json`, import.meta.url)))))
  assert.deepEqual(Object.keys(records).sort(), groups.map(group => group.id).sort())
  const debris = /关键线索是：|讲义依据：|先抓题干的决定性线索|不能因为某项表述熟悉|每日计划|精选答疑|讲义定位：|必会项：|易混对照：/
  for (const group of groups) {
    const record = records[group.id], stem = group.stems[0]
    assert.equal(stem.explanation, record.explanation, group.id)
    assert.deepEqual(stem.knowledgeConnections, record.knowledgeConnections, group.id)
    assert.deepEqual(group.lectureSummary, record.lectureSummary, group.id)
    assert.ok(stem.explanation.startsWith('正确答案：'), group.id)
    assert.ok(stem.knowledgeConnections.length >= 2, group.id)
    assert.ok(group.lectureSummary.length >= 2, group.id)
    assert.doesNotMatch([stem.explanation, ...stem.knowledgeConnections, ...group.lectureSummary].join('\n'), debris, group.id)
    if (group.topic !== '医学人文') {
      assert.ok(group.lectureEvidencePages.length, group.id)
      assert.deepEqual(stem.lectureEvidencePages, group.lectureEvidencePages, group.id)
      for (const page of group.lectureEvidencePages) {
        assert.ok(existsSync(new URL(`../public/${page.image}`, import.meta.url)), `${group.id}: ${page.image}`)
        assert.ok(page.knowledgePoints?.length || page.pageLabel === '解析流程图', group.id)
        assert.ok(page.questionNumbers?.includes(Number(group.sourceQuestion)) || page.pageLabel === '解析流程图', group.id)
      }
    }
  }
})

test('the serum-iron question uses the four-anemia iron table, not the cell-size classification', () => {
  const group = question('foundation-mock', 158)
  assert.deepEqual(group.stems[0].answer, ['B', 'D'])
  assert.match(group.stems[0].explanation, /铁利用障碍/)
  assert.match(group.stems[0].explanation, /铁调素/)
  assert.ok(group.lectureSummary.some(point => /总铁结合力/.test(point)))
  assert.ok(group.lectureEvidencePages.some(page => /^28 /.test(page.sourceFile) && page.page === 3))
  assert.ok(!group.lectureEvidencePages.some(page => /^28 /.test(page.sourceFile) && page.page === 4))
  assert.doesNotMatch(group.stems[0].explanation, /MCV|贫血的细胞学分类|造血干细胞异常/)
})
