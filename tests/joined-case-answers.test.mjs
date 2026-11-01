import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { migrateJoinedCaseAnswers } from '../src/joined-case-answers.js'
const data = JSON.parse(readFileSync(new URL('../src/data/med-teacher-supplement.json', import.meta.url)))
const old = 'med-teacher-02-02-03', treatment = 'med-teacher-02-04', key = `${old}:pneumonia-case-v1`
test('one pneumonia case retains all three scoped questions and answers', () => {
  const group = data.groups.find(g => g.id === old)
  assert.ok(!data.groups.some(g => g.id === treatment))
  assert.equal(group.sharedQuestionCount, 3)
  assert.match(group.sharedStem, /青霉素耐药/)
  assert.deepEqual(group.stems.map(s => s.number), [2, 3, 4])
  assert.deepEqual(group.stems.map(s => s.answerRaw), ['D', 'B', 'A'])
  for (const stem of group.stems) {
    const choices = group.options.filter(o => o.category === stem.optionCategory)
    assert.deepEqual(choices.map(o => o.displayKey), ['A', 'B', 'C', 'D'])
    assert.ok(stem.answer.every(a => choices.some(o => o.key === a)))
    assert.ok(stem.explanation && stem.knowledgeConnections.length)
  }
})
test('saved results from both old groups migrate without losing source records or overwriting newer work', () => {
  const selections = { [old]: {0:['q2-D'],1:['q3-B']}, [treatment]: {0:['A']} }
  const submitted = { [old]:true, [treatment]:true }
  const result = migrateJoinedCaseAnswers(selections, submitted, data.groups)
  assert.deepEqual(result.selections[key], {0:['q2-D'],1:['q3-B'],2:['q4-A']})
  assert.equal(result.submitted[key], true)
  assert.deepEqual(result.selections[old], selections[old])
  assert.ok(!Object.hasOwn(selections,key))
  assert.equal(migrateJoinedCaseAnswers(result.selections,result.submitted,data.groups).selections,result.selections)
})
test('partially completed previous groups remain editable after joining', () => {
  const result=migrateJoinedCaseAnswers({[treatment]:{0:['A']}},{[treatment]:true},data.groups)
  assert.deepEqual(result.selections[key],{2:['q4-A']})
  assert.equal(result.submitted[key],false)
})
