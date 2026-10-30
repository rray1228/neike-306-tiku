import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { scopeTestContent } from '../src/supplement-tests.js'

const directory = new URL('../src/data/', import.meta.url)
const read = name => JSON.parse(readFileSync(new URL(name, directory)))
const catalog = read('supplement-tests-catalog.json')
const original = readdirSync(directory).filter(name => name.endsWith('.json') && name !== 'supplement-tests-catalog.json').flatMap(name => {
  const content = read(name)
  return Array.isArray(content.groups) ? content.groups.map(group => ({ ...group, sourceSubject: name.split('-')[0] })) : []
})

test('every catalog paper references existing questions with exact displayed counts and no duplicated IDs', () => {
  assert.equal(new Set(catalog.map(paper => paper.id)).size, catalog.length)
  for (const paper of catalog) {
    assert.equal(new Set(paper.groupIds).size, paper.groupIds.length)
    const groups = paper.groupIds.map(id => original.find(group => group.id === id && group.sourceSubject === paper.subject))
    assert.ok(groups.every(Boolean), paper.id)
    assert.equal(groups.length, paper.groupCount, paper.id)
    assert.equal(groups.reduce((sum, group) => sum + group.stems.length, 0), paper.stemCount, paper.id)
  }
})

test('the original entrance is unchanged and test scope retains object identity, answer revisions and evidence', () => {
  const group = { id: 'shared', topic: '循环', answerRevision: 'corrected', stems: [{ answer: ['B'] }], lectureEvidence: { page: 10 } }
  const content = { groups: [group, { id: 'other', topic: '消化', stems: [] }], pages: [{ page: 10 }], meta: {}, topics: ['循环', '消化'] }
  assert.equal(scopeTestContent(content, null), content)
  const scoped = scopeTestContent(content, { groupIds: ['shared'], title: '测试卷' })
  assert.deepEqual(scoped.groups, [group])
  assert.equal(scoped.groups[0], group)
  assert.equal(scoped.pages, content.pages)
  assert.equal(scoped.groups[0].answerRevision, 'corrected')
  assert.deepEqual(scoped.topics, ['全部', '循环'])
  assert.equal(content.groups.length, 2)
})
