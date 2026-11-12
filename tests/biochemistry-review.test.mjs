import { readFileSync, existsSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const load = n => JSON.parse(readFileSync(new URL(`../src/data/${n}.json`, import.meta.url)))
const banks = [load('biochemistry-data'), ...Array.from({ length: 19 }, (_, i) => load(`biochemistry-lecture${i + 2}-data`)), load('biochemistry-teacher-supplement')]
const groups = new Map(banks.flatMap(b => b.groups).map(g => [g.id, g]))
const group = id => { assert.ok(groups.has(id), id); return groups.get(id) }
const stem = (id, n) => { const s = group(id).stems.find(s => s.number === n); assert.ok(s, `${id}/${n}`); return s }
const labels = (id, n) => stem(id, n).answer.map(key => group(id).options.find(o => o.key === key).label)

test('all 20 lectures and homework keep valid IDs, counts, answer types and option scopes', () => {
  assert.equal(groups.size, 311)
  assert.equal(banks.flatMap(b => b.groups.flatMap(g => g.stems)).length, 980)
  for (const bank of banks) {
    assert.equal(bank.meta.groupCount, bank.groups.length)
    assert.equal(bank.meta.stemCount, bank.groups.reduce((n, g) => n + g.stems.length, 0))
    for (const g of bank.groups) {
      assert.equal(new Set(g.options.map(o => o.key)).size, g.options.length, g.id)
      assert.equal(new Set(g.stems.map(s => s.number)).size, g.stems.length, g.id)
      assert.equal(new Set(g.stems.map(s => `${s.optionCategory || ''}:${s.text.replace(/\s/g, '')}`)).size, g.stems.length, g.id)
      for (const s of g.stems) {
        assert.ok(s.answer.length, `${g.id}/${s.number}`)
        if (s.answerMode === '填空') {
          if (s.answerDisplay !== undefined) assert.equal(s.answerDisplay, s.answer.join('；'), `${g.id}/${s.number}: displayed answer`)
          assert.equal((s.text.match(/_{3,}/g) || []).length, s.answer.length)
          for (const a of s.acceptedAnswers || []) assert.equal(a.length, s.answer.length)
          continue
        }
        const options = g.options.filter(o => !s.optionCategory || o.category === s.optionCategory)
        for (const k of s.answer) assert.ok(options.some(o => o.key === k), `${g.id}/${s.number}: ${k}`)
        if (s.answerMode === '排序') continue
        assert.equal(s.answerMode, s.answer.length > 1 ? '多选' : '单选')
        let raw = s.answerRaw.match(/[A-Z]+/g) || []
        if (!options.some(o => o.key.length > 1)) raw = raw.join('').split('')
        assert.deepEqual(raw, s.answer.map(k => options.find(o => o.key === k).displayKey || k))
      }
      if (g.lectureEvidence?.image) assert.ok(existsSync(new URL(`../public/${g.lectureEvidence.image}`, import.meta.url)), g.id)
    }
  }
})

test('vitamins separate cofactors, enzymes and reactions while preserving ADEK answers', () => {
  const g = group('bio-13-03')
  assert.equal(g.options.length, 11)
  assert.match(group('bio-13-03-focus-2').title, /依赖酶/)
  assert.match(group('bio-13-03-focus-3').title, /参与的反应/)
  assert.deepEqual(labels(g.id, 2), ['FMN', 'FAD'])
  assert.deepEqual(labels(g.id, 3), ['NAD', 'NADP'])
  for (const s of g.stems) assert.equal(s.answerRaw, s.answer.join('、'))
  assert.equal(group('bio-13-01').stems[2].answer.length, 4)
  assert.deepEqual(stem('bio-13-01', 4).answer, ['H', 'O'])
})

test('vitamin group question eight preserves the supplied lecture list including ACP', () => {
  const g = group('bio-13-03')
  const q = stem(g.id, 8)
  assert.equal(q.text, '讲义列出的含腺嘌呤辅因子')
  assert.deepEqual(q.answer, ['A', 'D', 'I', 'J', 'K'])
  assert.equal(q.answerRaw, 'A、D、I、J、K')
  assert.equal(q.answerMode, '多选')
  assert.equal(g.options.find(o => o.key === 'I').label, '酰基载体蛋白（ACP）')
  assert.equal(g.answerRevision, 'bio-answer-audit-20261029-v1')
  assert.deepEqual(stem(g.id, 4).answer, ['D', 'I'])
})

test('question wording and grading follow the linked lecture tables', () => {
  assert.deepEqual(labels('bio-18-03-focus-3', 1), ['IF2', 'EF-Tu', 'RF3'])
  assert.ok(labels('bio-17-05-focus-2', 1).includes('参与翻译的起始过程'))
  assert.ok(labels('bio-17-05-focus-2', 2).includes('参与翻译的起始过程'))
  assert.deepEqual(labels('bio-08-02', 3), ['疏水键', '二硫键'])
  assert.deepEqual(labels('bio-08-02', 4), ['氢键', '离子键 / 盐键'])
  assert.deepEqual(labels('bio-07-10', 1), ['色氨酸'])
  assert.deepEqual(labels('bio-03-04-focus-2', 4), ['胞浆'])
  assert.deepEqual(labels('bio-03-05', 3), ['果糖-1,6-二磷酸', '果糖-2,6-二磷酸'])
  assert.ok(labels('bio-01-05', 2).includes('葡萄糖-1-磷酸'))
  assert.deepEqual(labels('bio-06-02', 3), ['柠檬酸', '异柠檬酸', '乙酰 CoA', '丙二酰 CoA'])
  assert.deepEqual(labels('bio-06-10', 2), ['亚油酸', '亚麻酸', '花生四烯酸'])
  assert.deepEqual(labels('bio-10-05', 3), ['胆红素摄取、排泄障碍'])
  assert.deepEqual(labels('bio-10-05-focus-2', 3), ['UCB↑、CB↑'])
  assert.deepEqual(labels('bio-20-07', 4), ['Fanconi贫血'])
})

test('drug targets and RNA recognition use the source labels', () => {
  assert.deepEqual(labels('bio-09-08', 3), ['CDP 还原酶'])
  assert.doesNotMatch(labels('bio-09-08', 2).join(' '), /合成嘌呤核苷酸/)
  assert.deepEqual(labels('bio-18-08', 3), ['使eEF2糖基化失活'])
  assert.match(labels('bio-18-08', 4).join(' '), /降解28S rRNA/)
  assert.deepEqual(labels('bio-17-08', 4), ['RNA 3′端的polyC'])
  assert.deepEqual(labels('bio-20-06-focus-2', 3), ['复制后新生链中的碱基错配'])
  assert.match(labels('bio-20-06-focus-2', 1).join(' '), /糖苷酶/)
})

test('translation inhibitors no longer repeat synonyms or combine mechanisms with system labels', () => {
  const g = group('bio-18-08')
  assert.equal(g.stems.length, 7)
  assert.equal(g.stems.filter(s => s.text.includes('白喉毒素')).length, 1)
  assert.equal(g.stems.filter(s => s.text.includes('伊短菌素')).length, 1)
  assert.equal(stem(g.id, 3).answer.length, 1)
  assert.match(labels('bio-18-08-focus-3', 1).join(' '), /eIF2/)
  assert.match(labels('bio-18-08-focus-3', 1).join(' '), /降解病毒mRNA/)
})

test('definitions, examples and measurements are not bundled into one answer', () => {
  assert.deepEqual(labels('bio-08-04', 1), ['破坏一级结构'])
  assert.deepEqual(labels('bio-08-04', 2), ['破坏空间结构'])
  assert.match(stem('bio-20-01', 1).text, /CDS/)
  assert.deepEqual(labels('bio-20-01', 2), ['被转录，不被翻译'])
  assert.match(stem('biochemistry-teacher-01-16', 16).text, /ρ依赖性/)
  assert.match(stem('biochemistry-teacher-01-27', 27).text, /特异性/)
  for (const id of ['biochemistry-teacher-01-16', 'biochemistry-teacher-01-27', 'biochemistry-teacher-01-28']) {
    assert.equal(group(id).title, group(id).stems[0].text)
  }
})

test('unordered fill-in lists accept all valid permutations and protect stored answers', () => {
  for (const [id, n, count] of [['bio-15-fill-03', 15, 5], ['bio-15-fill-04', 20, 5], ['bio-15-fill-04', 24, 1], ['bio-15-fill-04', 25, 5]]) {
    assert.equal(stem(id, n).acceptedAnswers.length, count)
    assert.equal(group(id).answerRevision, 'bio-review-20261017')
  }
  assert.deepEqual(stem('bio-16-fill-02', 11).answer, ['相同', '连续', '相反', '不连续', '冈崎片段'])
  assert.equal(group('bio-18-08').answerRevision, 'bio-answer-audit-20261029-v1')
})
