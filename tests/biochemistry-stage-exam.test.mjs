import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const data = read('biochemistry-stage-exam-data')
const banks = [read('biochemistry-data'), ...Array.from({ length: 19 }, (_, i) => read(`biochemistry-lecture${i + 2}-data`)), read('biochemistry-teacher-supplement')]
const q = n => data.groups.find(g => g.stems[0].number === n)
const multiple = [3, 4, 6, 10, 11, 13, 18, 21, 22]

test('all 25 biochemistry exam questions retain original numbering, four choices and source type', () => {
  assert.equal(data.meta.groupCount, 25)
  assert.equal(data.meta.stemCount, 25)
  assert.deepEqual(data.groups.map(g => g.stems[0].number), Array.from({ length: 25 }, (_, i) => i + 1))
  assert.deepEqual(data.groups.filter(g => g.kind === 'X').map(g => g.stems[0].number), multiple)
  const all = [...banks.flatMap(b => b.groups), ...data.groups]
  assert.equal(new Set(all.map(g => g.id)).size, 336)
  assert.equal(all.flatMap(g => g.stems).length, 1005)
  for (const g of data.groups) {
    const s = g.stems[0]
    assert.equal(g.stems.length, 1)
    assert.deepEqual(g.options.map(o => o.key), ['A', 'B', 'C', 'D'])
    assert.ok(g.options.every(o => o.label && o.key === o.displayKey))
    assert.equal(s.answerMode, multiple.includes(s.number) ? '多选' : '单选')
    assert.doesNotMatch([s.text, ...g.options.map(o => o.label)].join(' '), /uusx|每日计划|微信|再相逢|（X）/)
  }
})

test('all user-authorized draft answers are attributed, explained and never labelled official', () => {
  assert.deepEqual(data.meta.missingAnswerQuestions, [])
  assert.equal(data.meta.hasOfficialAnswerKey, false)
  assert.deepEqual(data.meta.missingOfficialAnswerQuestions, Array.from({ length: 25 }, (_, i) => i + 1))
  assert.deepEqual(data.meta.draftAnswerQuestions, data.meta.missingOfficialAnswerQuestions)
  assert.equal(data.meta.answerRows, undefined)
  assert.deepEqual(data.groups.map(g => g.stems[0].answerRaw), [
    'B', 'D', 'BC', 'ABC', 'D', 'ABD', 'C', 'B', 'A', 'AC',
    'ABCD', 'D', 'ABD', 'B', 'B', 'B', 'B', 'AC', 'D', 'B',
    'ABD', 'ACD', 'C', 'B', 'D',
  ])
  for (const g of data.groups) {
    const s = g.stems[0]
    assert.equal(g.supplementNotice, '')
    assert.equal(g.studyNotice, '生物化学')
    assert.equal(g.answerSourceLabel, '答案')
    const corrected = [10, 21].includes(s.number)
    assert.match(g.answerSourceName, corrected ? /用户.*校正/ : /用户授权拟答/)
    assert.equal(g.answerRevision, s.number === 21 ? 'bio-stage-p53-20261102-v2' : s.number === 10 ? 'bio-answer-audit-20261029-v1' : 'bio-stage-draft-20261017-v1')
    assert.deepEqual(s.answer, s.answerRaw.split(''))
    assert.ok(s.answer.length && s.answer.every(k => g.options.some(o => o.key === k)))
    assert.equal(s.sourceAnswerMode, s.answerMode)
    assert.equal(s.answerState, corrected ? '用户校正' : '讲义核对拟答（非官方）')
    assert.equal(s.answerProvenance, corrected ? 'user-correction' : 'assistant-draft')
    assert.ok(s.explanation.length > 30)
    assert.doesNotMatch([g.supplementNotice, g.studyNotice, g.answerSourceLabel, s.explanation].join(' '), /拟答|暂拟|非官方|后续校正|待你校正|保留原卷多选操作|本题口径待复核/)
    for (const a of s.acceptedAnswers || []) assert.ok(a.length && a.every(k => g.options.some(o => o.key === k)))
  }
})

test('ambiguous source wording is explicit and CPSII is not confused with CPSI', () => {
  assert.deepEqual(data.meta.reviewQuestionNumbers, [4, 10, 11, 18, 24])
  const cps = q(10).stems[0]
  assert.equal(q(10).kind, 'X')
  assert.equal(cps.answerMode, '多选')
  assert.deepEqual(cps.answer, ['A', 'C'])
  assert.equal(q(10).options[2].label, '主要受到 UMP 负反馈机制的调节')
  assert.match(cps.explanation, /通常受UTP负反馈调节/)
  assert.match(cps.explanation, /特定实验中UMP也可产生抑制/)
  assert.doesNotMatch(cps.explanation, /仅A符合/)
  assert.match(cps.explanation, /增殖程度.*分化程度/)
  assert.match(cps.explanation, /选A、C/)
  assert.deepEqual(q(4).stems[0].acceptedAnswers, [['A', 'B']])
  assert.deepEqual(q(11).stems[0].acceptedAnswers, [['A', 'B', 'C']])
  assert.match(q(11).stems[0].explanation, /不能泛化/)
  assert.match(q(18).stems[0].explanation, /最终多肽/)
  assert.match(q(24).stems[0].explanation, /GST.*谷胱甘肽/)
})

test('p53 question 21 grades only ABD within the book scope and removes the added C rationale', () => {
  const g = q(21), s = g.stems[0]
  assert.deepEqual(s.answer, ['A', 'B', 'D'])
  assert.equal(s.answerRaw, 'ABD')
  assert.equal(s.answerMode, '多选')
  assert.deepEqual(s.acceptedAnswers || [], [])
  assert.doesNotMatch([s.explanation, ...(s.knowledgeConnections || [])].join(' '), /PTEN|漏选C|选C/)
  assert.equal(s.answerReferences, undefined)
  assert.match(s.explanation, /书上列举范围/)
  const grade = selected => [...selected].sort().join('') === [...s.answer].sort().join('')
  assert.equal(grade(['A', 'B', 'D']), true)
  assert.equal(grade(['A', 'B', 'C', 'D']), false)
})

test('cross-page choices, source page images and notation survive extraction', () => {
  assert.deepEqual(q(5).sourcePages, [1, 2])
  assert.deepEqual(q(16).sourcePages, [3, 4])
  assert.equal(q(5).options[3].label, 'ACP')
  assert.match(q(16).options[1].label, /5-端添加端粒/)
  assert.match(q(16).options[3].label, /线性染色体的合成/)
  assert.match(q(12).options[0].label, /Fe²⁺/)
  assert.match(q(12).options[2].label, /B₆/)
  assert.deepEqual(q(23).options.map(o => o.label), ['ATAATA', 'CCCTGG', 'GATATC', 'GAGTCT'])
  assert.match(q(24).options[0].label, /6× His-Tag/)
  assert.match(q(25).options[3].label, /ddNTP.*终止 DNA 合成/)
  assert.equal(data.pages.length, 5)
  for (const p of data.pages) assert.ok(existsSync(resolve('public', p.image)), p.image)
  for (const g of data.groups) {
    assert.equal(g.page, g.sourcePages[0])
    for (const n of g.sourcePages) assert.ok(data.pages.some(p => p.page === n && p.sourceKey === g.sourceKey))
  }
})

test('stage questions load into real tested chapters, alongside existing lecture and homework data', () => {
  const lectureIds = new Set(banks.flatMap(b => b.lectures || []).map(l => l.id))
  const topics = ['糖代谢', '生物氧化', '脂代谢', '氨基酸与蛋白质', '核苷酸代谢', '胆色素代谢与生物转化', '小基因', '核酸']
  for (const g of data.groups) {
    assert.equal(g.lectureIds.length, 1)
    assert.ok(lectureIds.has(g.lectureIds[0]), g.id)
    assert.equal(g.stems[0].lectureId, g.lectureIds[0])
    assert.ok(topics.includes(g.topic))
  }
  for (const [n, lecture] of [[1, 8], [3, 3], [7, 2], [10, 9], [11, 10], [14, 20], [16, 16], [17, 17], [18, 18], [19, 19], [21, 14], [25, 14]]) {
    assert.deepEqual(q(n).lectureIds, [`lecture-${String(lecture).padStart(2, '0')}`])
  }
  const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8')
  assert.match(app, /loadJson\(\(\) => import\('\.\/data\/biochemistry-stage-exam-data\.json'\)\)/)
  assert.match(app, /groups: \[\.\.\.biochemistryTeacherContent\.groups, \.\.\.biochemistryExamContent\.groups(?:,|\])/)
  assert.match(app, /pages: \[\.\.\.biochemistryTeacherContent\.pages, \.\.\.biochemistryExamContent\.pages(?:,|\])/)
})
