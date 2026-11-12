import { readFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import test from 'node:test'

const read = path => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url)))
const audit = read('reports/biochemistry-answer-audit-2026-10-29.json')
const banks = audit.scope.map(({ file }) => read(file))
const groups = banks.flatMap(b => b.groups)
const get = id => { const g = groups.find(g => g.id === id); assert.ok(g, id); return g }
const stem = (id, n) => { const s = get(id).stems.find(s => s.number === n); assert.ok(s); return s }
const label = (id, key) => get(id).options.find(o => o.key === key).label
const answers = (id, n) => stem(id, n).answer

test('content review covers all 20 chapters and both supplements without dropping questions', () => {
  assert.equal(banks.length, 22)
  assert.equal(groups.length, 336)
  assert.equal(groups.flatMap(g => g.stems).length, 1005)
  for (let i = 0; i < banks.length; i++) {
    assert.equal(banks[i].groups.length, audit.scope[i].groups)
    assert.equal(banks[i].groups.flatMap(g => g.stems).length, audit.scope[i].stems)
  }
  assert.equal(audit.changes.length, 32)
  assert.equal(new Set(audit.changes.map(c => c.id)).size, 32)
  for (const { id, note, supersededBy } of audit.changes) {
    assert.equal(get(id).answerRevision, supersededBy?.revision || audit.revision, id)
    assert.equal(get(id).reviewedAt, supersededBy?.date || audit.date, id)
    assert.ok(get(id).reviewNotes.includes(supersededBy?.note || note), id)
  }
})

test('known omitted valid choices are restored and answer modes follow the new keys', () => {
  assert.deepEqual(answers('bio-02-04-focus-2', 2), ['F', 'A', 'B'])
  assert.match(stem('bio-02-04-focus-2', 2).text, /辅基/)
  assert.deepEqual(answers('bio-02-08', 2), ['I', 'L', 'G'])
  assert.deepEqual(answers('bio-16-01', 1), ['A', 'B', 'C', 'D'])
  assert.deepEqual(answers('bio-13-03', 8), ['A', 'D', 'I', 'J', 'K'])
})

test('amino acid classification follows the supplied lecture without adding tryptophan to its nonpolar list', () => {
  const s = stem('bio-07-02', 7)
  assert.equal(label('bio-07-02', 'A'), '色氨酸')
  assert.match(s.text, /本讲义列出/)
  assert.deepEqual(s.answer, ['I', 'L', 'B', 'E', 'N', 'M', 'K', 'J'])
  assert.equal(s.answerRaw, 'I、L、B、E、N、M、K、J')
  assert.equal(s.answerMode, '多选')
  assert.deepEqual(s.acceptedAnswers || [], [])
  assert.doesNotMatch(s.explanation, /色氨酸/)
  assert.ok(answers('bio-07-02', 6).includes('A'), '芳香族分类保留色氨酸')
  assert.equal(get('bio-07-02').answerRevision, 'bio-amino-classification-20261103-v2')
})

test('the phospholipid pathway question follows the collection diagram', () => {
  assert.match(stem('bio-05-03', 2).text, /第42页/)
  assert.deepEqual(answers('bio-05-03', 2), ['B', 'G', 'M'])
  assert.match(stem('bio-05-03', 2).explanation, /磷脂酰丝氨酸/)
  assert.deepEqual(answers('bio-05-04', 1), ['B'])
  assert.equal(stem('bio-05-04', 1).answerMode, '单选')
  assert.match(stem('bio-05-04', 1).text, /直接/)
})

test('overlapping cofactor, interferon and polymerase distractors no longer create false wrong answers', () => {
  assert.match(label('bio-13-04', 'I'), /氢负离子/)
  assert.match(label('bio-13-04', 'D'), /单电子与双电子/)
  assert.match(label('bio-18-08-focus-3', 'D'), /去磷酸化.*增强病毒/)
  assert.deepEqual(answers('bio-18-08-focus-3', 1), ['B', 'C'])
  assert.equal(label('bio-20-06-focus-4', 'B'), 'DNA聚合酶Ⅰ')
})

test('molecular mechanisms distinguish bases, nucleosides, protein factors and origin elements', () => {
  assert.equal(label('bio-20-04-focus-2', 'B'), '腺嘌呤→次黄嘌呤')
  assert.match(label('bio-18-03', 'H'), /核苷酸交换因子/)
  assert.equal(label('bio-18-08', 'F'), '结合真核60S亚基而抑制成肽')
  assert.match(label('bio-19-07-focus-2', 'A'), /降解减少.*稳定积累/)
  assert.match(label('bio-17-02', 'D'), /决定转录特异性/)
  assert.match(label('bio-17-02', 'B'), /募集σ/)
  assert.match(label('bio-17-01-focus-4', 'B'), /初级转录本/)
  assert.match(stem('bio-16-05', 1).text, /DnaA盒/)
})

test('fill corrections preserve all blanks and do not turn conditional claims into absolutes', () => {
  assert.deepEqual(answers('bio-16-fill-04', 13), ['多', '慢', '短'])
  assert.equal(answers('bio-16-fill-04', 14)[0], 'DNApol α-引物酶复合物')
  assert.doesNotMatch(stem('bio-15-fill-02', 13).text, /不能复性/)
  assert.doesNotMatch(label('bio-06-01', 'B'), /只能/)
  assert.doesNotMatch(label('bio-08-08', 'A'), /均为/)
  assert.equal(groups.flatMap(g => g.stems).filter(s => s.answerMode === '填空').length, 60)
})

test('lecture/user conventions remain explicitly distinguished from general structural claims', () => {
  assert.equal(stem('bio-13-03', 8).text, '讲义列出的含腺嘌呤辅因子')
  assert.match(stem('bio-13-03', 8).explanation, /并不含腺嘌呤/)
  const cps = get('biochemistry-stage-exam-2026-10-q010')
  assert.equal(cps.options[2].label, '主要受到 UMP 负反馈机制的调节')
  assert.deepEqual(cps.stems[0].answer, ['A', 'C'])
  assert.match(cps.stems[0].explanation, /通常受UTP负反馈调节/)
})
