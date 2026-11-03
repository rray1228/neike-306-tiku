import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { combineSharedClinicalCases, migrateSharedClinicalCases } from '../src/shared-clinical-cases.js'
const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const files = ['med', 'surgery'].flatMap(subject => ['foundation-mock-exam', 'sprint-exam'].map(source => [subject, read(`${subject}-${source}-data`)]))

test('all 30 split clinical cases combine without dropping or mixing questions, choices or references', () => {
  let count = 0
  for (const [, original] of files) {
    const before = JSON.stringify(original), combined = combineSharedClinicalCases(original)
    assert.equal(combined.groups.reduce((n, group) => n + group.stems.length, 0), original.groups.length)
    assert.equal(JSON.stringify(original), before)
    assert.deepEqual(combineSharedClinicalCases(combined), combined)
    for (const group of combined.groups.filter(group => group.joinedSourceGroups)) {
      count++
      assert.ok(group.sharedStem)
      assert.equal(group.joinedSourceGroups.length, group.stems.length)
      assert.equal(new Set(group.options.map(option => option.key)).size, group.options.length)
      group.stems.forEach((stem, index) => {
        const old = original.groups.find(g => g.id === group.joinedSourceGroups[index].id)
        const choices = group.options.filter(option => option.category === stem.optionCategory)
        assert.deepEqual(choices.map(o => o.label), old.options.map(o => o.label))
        assert.deepEqual(stem.answer.map(key => choices.find(o => o.key === key).displayKey), old.stems[0].answer)
        assert.equal(stem.text, old.stems[0].text)
        assert.equal(stem.explanation, old.stems[0].explanation)
        assert.equal(`${group.sharedStem}${stem.sharedText || ''}`.replace(/\s+/g,''), `${old.sharedStem || old.stems[0].sharedText}`.replace(/\s+/g,''))
        assert.ok(stem.lectureEvidencePages.length)
      })
    }
  }
  assert.equal(count, 30)
})

test('screenshot renal case 82-84 is one group with three independently scoped answer banks', () => {
  const data = read('med-foundation-mock-exam-data')
  const group = combineSharedClinicalCases(data).groups.find(g => g.id.endsWith('q082'))
  assert.equal(group.stems.length, 3)
  assert.match(group.title, /第82—84题/)
  assert.match(group.sharedStem, /19.*岁/)
  assert.deepEqual(group.stems.map(s => s.sourceQuestion), [82, 83, 84])
  assert.ok(group.stems.every(stem => group.options.filter(o => o.category === stem.optionCategory).length === 4))
})

test('evolving UC case keeps the new examination and potassium result in question 81', () => {
  const group = combineSharedClinicalCases(read('med-sprint-exam-data')).groups.find(g=>g.sourceQuestion === '79—81')
  assert.equal(group.stems.length,3)
  assert.match(group.stems[2].sharedText,/39.1/)
  assert.match(group.stems[2].sharedText,/2.9mmol/)
  assert.ok(!group.stems[2].sharedText.includes('女性，28'))
})

test('answer migration preserves full and partial histories, favorites, notes and newer merged records', () => {
  for (const [subject, original] of files) {
    const groups = combineSharedClinicalCases(original).groups
    const group = groups.find(g => g.joinedSourceGroups)
    const base = id => subject === 'med' ? id : `${subject}:${id}`
    const old = group.joinedSourceGroups.map(source => base(source.id))
    const selections = Object.fromEntries(old.map(key => [key, { 0: ['B'] }]))
    const submitted = Object.fromEntries(old.map(key => [key, true]))
    const state = migrateSharedClinicalCases(subject, selections, submitted, [old[1]], {[old[0]]:'首题笔记',[old[1]]:'次题笔记'}, groups)
    const key = `${old[0]}:shared-case-v1`
    assert.equal(state.submitted[key], true)
    assert.equal(Object.keys(state.selections[key]).length, old.length)
    assert.deepEqual(state.selections[old[1]], selections[old[1]])
    assert.deepEqual(state.favorites, [old[0]])
    assert.match(state.notes[old[0]], /首题笔记\n\n次题笔记/)
    const again = migrateSharedClinicalCases(subject, state.selections, state.submitted, state.favorites, state.notes, groups)
    assert.equal(again.selections, state.selections)
    assert.equal(again.notes, state.notes)
    const partial = migrateSharedClinicalCases(subject, {[old[1]]:{0:['C']}}, {[old[1]]:true}, [], {}, groups)
    assert.equal(partial.submitted[key], false)
    assert.deepEqual(partial.selections[key][1], [group.joinedSourceGroups[1].optionKeyMap.C])
  }
})

test('identical descriptions in separate papers or nonconsecutive questions remain separate', () => {
  const data = read('med-foundation-mock-exam-data')
  const g = data.groups.find(g => g.stems[0].sharedText)
  const otherPaper = { ...g, id:'other', sourceKey:'other-paper' }
  const distant = { ...g, id:'distant', stems:[{...g.stems[0],sourceQuestion:999}] }
  assert.equal(combineSharedClinicalCases({...data, groups:[g,otherPaper,distant]}).groups.length,3)
})
