import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/med-stage-exam-data.json', import.meta.url)))
const base = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const stems = data.groups.flatMap(g => g.stems)
const group = n => data.groups.find(g => g.stems.some(s => s.number === n))
const stem = n => stems.find(s => s.number === n)

test('stage exam retains every question exactly once and all screenshot answer rows', () => {
  assert.equal(data.groups.length, 108)
  assert.equal(stems.length, 116)
  assert.deepEqual(stems.map(s=>s.number), Array.from({length:116},(_,i)=>i+1))
  const expectedRows = [
    'CCDCDCBBACDBACC', 'CDCADCDCCBBDDAA', 'CCBCBDABCCCCBAB',
    'CBCDDCAABAABCCD', 'CCBAABBBAABCABB', 'CCBDBCDCCCCDCCD',
    'DBBDBBDCDCACBCD', 'ABACACCABAA',
  ]
  assert.deepEqual(Array.from({length:8},(_,i)=>stems.slice(i*15,i*15+15).map(s=>s.answerRaw).join('')), expectedRows)
  assert.equal(new Set([...base.groups,...data.groups].map(g=>g.id)).size, base.groups.length+data.groups.length)
})

test('each case subquestion has only its own four options and original single-choice answer', () => {
  const shared = data.groups.filter(g=>g.sharedStem)
  assert.deepEqual(shared.map(g=>g.stems.map(s=>s.number)), [[42,43],[71,72],[74,75,76],[89,90,91],[94,95],[96,97]])
  for (const g of data.groups) {
    assert.equal(new Set(g.options.map(o=>o.key)).size,g.options.length,g.id)
    for(const s of g.stems) {
      const choices = g.options.filter(o=>!s.optionCategory||o.category===s.optionCategory)
      assert.deepEqual(choices.map(o=>o.displayKey),['A','B','C','D'],g.id)
      assert.ok(choices.every(o=>o.label.length),g.id)
      assert.equal(s.answerMode,'单选')
      assert.equal(s.answer.length,1)
      assert.equal(choices.find(o=>o.key===s.answer[0])?.displayKey,s.answerRaw)
      assert.doesNotMatch(s.text,/ttsx|每日计划|不要焦虑正确率|ACA/)
    }
    if(g.sharedStem) assert.equal(g.sharedQuestionCount,g.stems.length)
  }
})

test('stage questions resolve to actual lecture chapters rather than distractor topics', () => {
  const ranges = {呼吸:[1,13],消化:[14,23],肾脏:[24,27],血液:[28,35],内分泌:[36,42],风湿:[43,47],中毒:[48,48],循环:[49,57]}
  for(const g of data.groups) {
    assert.equal(g.lectureIds.length,1)
    assert.ok(base.lectures.some(l=>l.id===g.lectureIds[0]))
    const n=Number(g.lectureIds[0].slice(-2)), [lo,hi]=ranges[g.topic]
    assert.ok(n>=lo&&n<=hi,g.id)
    assert.ok(g.stems.every(s=>s.lectureId===g.lectureIds[0]))
  }
  for(const [n,lid] of [[16,13],[19,2],[23,11],[45,50],[63,22],[65,20],[66,21],[71,27],[82,28],[88,33],[96,32],[99,36],[101,37],[104,40],[115,48]])
    assert.deepEqual(group(n).lectureIds,[`lecture-${String(lid).padStart(2,'0')}`])
})

test('cross-page case text and option continuations are not dropped or leaked', () => {
  assert.deepEqual(group(5).sourcePages,[1,2])
  assert.deepEqual(group(31).sourcePages,[6,7])
  assert.deepEqual(group(42).sourcePages,[8,9])
  assert.deepEqual(group(71).sourcePages,[13,14])
  assert.deepEqual(group(94).sourcePages,[17,18])
  assert.match(group(42).sharedStem,/收缩期喷射样杂音/)
  assert.doesNotMatch(group(41).options.at(-1).label,/男|32/)
  assert.match(group(54).stems[0].text,/组织病理学检查.*壁细胞增生/)
  assert.equal(group(59).options.at(-1).label,'急性肠穿孔')
  assert.equal(group(106).options.at(-1).label,'肢端袜套样感觉异常')
  assert.equal(group(116).options.at(-1).label,'有机磷中毒')
})

test('original page images and the unredrawn question30 ECG exist under the Pages base path', () => {
  assert.equal(data.pages.length,21)
  assert.equal(data.groups.filter(g=>g.stems.some(s=>s.image)).length,1)
  assert.ok(existsSync(resolve('public',stem(30).image)))
  for(const p of data.pages)assert.ok(existsSync(resolve('public',p.image)),p.image)
  for(const g of data.groups)for(const n of g.sourcePages)
    assert.ok(data.pages.some(p=>p.sourceKey===g.sourceKey&&p.page===n))
})
