import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/med-teacher-supplement.json', import.meta.url)))
const cardiac = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const expected = {
  1: ['D','D','B','C','B','D','C','C','B','B','D','B','BC','B','C','B'],
  2: ['D','D','B','A','ACD','C','C','ABD','A','D','B','B','ABC','ACD','BC','D','B','C','B'],
  3: ['D','D','D','D','ABC','A','ABC','D','C','C','A','C','A','A','C','ABD','C','CD'],
  4: ['D','BC','D','AB','D','B','D','BC','C','ACD','A','C'],
  5: ['D','D','B','A','D','ABCD','C','AB','C','B','D','A'],
  6: ['D','B','B','C','A','A','C','','A','A','ABD','AD','D','D','B'],
  7: ['ACD','AC','C','A','D','C','B','A','C','C','A','A','D','A','ABC'],
  8: ['D','C','','CD','ACD','B','C','B','C','B','A','D','D','B','B','A','D','A','D'],
}

test('all 126 source questions retain scoped answers including reviewed PNH exceptions', () => {
  const seen = new Set()
  let answered = 0
  for (const g of data.groups) {
    const section = Number(g.id.split('-')[2])
    for (const s of g.stems) {
      const identity = `${section}:${s.number}`
      assert.ok(!seen.has(identity), identity)
      seen.add(identity)
      const choices = g.options.filter(o => !s.optionCategory || o.category === s.optionCategory)
      assert.equal(choices.length, identity === '8:3' ? 3 : 4, identity)
      assert.ok(s.answer.every(k => choices.some(o => o.key === k)), identity)
      const letters = s.answer.map(k => {
        const o = choices.find(o => o.key === k)
        return o.displayKey || o.key
      }).join('')
      assert.equal(letters, expected[section][s.number - 1], identity)
      if (s.answer.length) answered++
      if (s.answer.length > 1) assert.equal(s.answerMode, '多选', identity)
      assert.ok(s.answerSourcePage >= 1 && s.answerSourcePage <= 13)
    }
  }
  assert.equal(seen.size, 126)
  assert.equal(answered, 124)
  assert.equal(data.meta.answeredStemCount, answered)
})

test('missing source answer is explicit and not fabricated', () => {
  const g = data.groups.find(g => g.id === 'med-teacher-08-01-03')
  assert.ok(g.sharedStem)
  assert.deepEqual(g.stems[2].answer, [])
  assert.match(g.supplementNotice, /缺A选项.*未标红答案/)
})

test('cardiac table stems contain no verbose instructions or answer-revealing hints', () => {
  for (const g of cardiac.groups.filter(g => g.id.includes('table'))) {
    for (const s of g.stems) assert.doesNotMatch(s.text, /选择讲义|选择原表|原表可选|病理Q波多无|不常规抗凝/)
  }
})
