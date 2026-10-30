import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { questionBankUrl, scopeTestContent, studyViewUrl, testCollectionForSubject } from '../src/supplement-tests.js'

const directory = new URL('../src/data/', import.meta.url)
const read = name => JSON.parse(readFileSync(new URL(name, directory)))
const catalog = read('supplement-tests-catalog.json')
const original = readdirSync(directory).filter(name => name.endsWith('.json') && name !== 'supplement-tests-catalog.json').flatMap(name => {
  const content = read(name)
  return Array.isArray(content.groups) ? content.groups.map(group => ({ ...group, sourceSubject: name.split('-')[0] })) : []
})

test('test navigation preserves both root hosting and GitHub Pages subdirectories', () => {
  for (const href of ['https://study.example/?subject=physiology', 'https://owner.github.io/neike-306-tiku/?subject=physiology']) {
    const before = new URL(href)
    const tests = new URL(studyViewUrl(href, 'tests'))
    assert.equal(tests.origin, before.origin)
    assert.equal(tests.pathname, before.pathname)
    assert.equal(tests.searchParams.get('subject'), 'physiology')
    assert.equal(tests.searchParams.get('view'), 'tests')
    const bank = new URL(questionBankUrl(`${tests.href}&paper=med-stage-exam`))
    assert.equal(bank.href, href)
  }
  assert.equal(questionBankUrl('https://study.example/tests?paper=med-stage-exam'), 'https://study.example/')
  assert.equal(questionBankUrl('https://owner.github.io/neike-306-tiku/tests?paper=med-stage-exam'), 'https://owner.github.io/neike-306-tiku/')
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

test('the supplementary entrance combines sources within each subject and preserves their system and chapter assignments', () => {
  for (const subject of new Set(catalog.map(paper => paper.subject))) {
    const papers = catalog.filter(paper => paper.subject === subject)
    const collection = testCollectionForSubject(catalog, subject)
    const sourceGroups = original.filter(group => group.sourceSubject === subject)
    const scoped = scopeTestContent({ groups: sourceGroups, meta: {} }, collection)
    assert.equal(scoped.groups.length, papers.reduce((sum, paper) => sum + paper.groupCount, 0))
    for (const group of scoped.groups) {
      assert.ok(group.topic)
      assert.equal(group, sourceGroups.find(source => source.id === group.id))
      assert.deepEqual(group.lectureIds, sourceGroups.find(source => source.id === group.id).lectureIds)
    }
    assert.deepEqual(scoped.topics, ['全部', ...new Set(scoped.groups.map(group => group.topic))])
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

test('every imported homework, practitioner, exam and other supplemental source is included', () => {
  for (const name of readdirSync(directory).filter(name => name.endsWith('.json') && name !== 'supplement-tests-catalog.json')) {
    const data = read(name)
    if (!Array.isArray(data.groups)) continue
    const subject = name.split('-')[0]
    const collection = testCollectionForSubject(catalog, subject)
    const expected = data.groups.filter(group => group.supplement || subject === 'politics' || name === 'physiology-endocrine-summary-data.json')
    const registered = new Set(catalog.filter(source => source.subject === subject).flatMap(source => source.groupIds))
    for (const group of expected) assert.ok(registered.has(group.id), `${name}: missing ${group.id}`)
    assert.deepEqual(scopeTestContent({ groups: data.groups, meta: {} }, collection).groups, expected, name)
  }
})

test('new explicitly supplemental questions appear without requiring a manual ID list', () => {
  const group = { id: 'future-homework', supplement: true, topic: '呼吸', stems: [] }
  const collection = testCollectionForSubject(catalog, 'med')
  assert.deepEqual(scopeTestContent({ groups: [group], meta: {} }, collection).groups, [group])
})
