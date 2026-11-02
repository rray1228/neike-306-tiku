import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { chapterLectureIds, organizeChapterPractice, originalQuestionsFirst } from '../src/chapter-practice.js'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const subjects = ['med', 'pathology', 'physiology', 'surgery', 'biochemistry']
function bank(subject) {
  const base = read(`${subject}-data`)
  const sources = ['teacher-supplement', 'stage-exam-data', 'foundation-mock-exam-data', 'sprint-exam-data'].map(suffix => read(`${subject}-${suffix}`))
  if (subject === 'biochemistry') for (let number = 2; number <= 20; number++) sources.unshift(read(`biochemistry-lecture${number}-data`))
  return {
    ...base,
    groups: [...base.groups, ...sources.flatMap(source => source.groups)],
    topics: [...new Set([...base.topics, ...sources.flatMap(source => source.topics || [])])],
    lectures: [...base.lectures, ...sources.flatMap(source => source.lectures || [])],
  }
}

test('five subjects place same-subject mock questions in existing chapters instead of paper-specific copies', () => {
  for (const subject of subjects) {
    const content = bank(subject)
    const organized = organizeChapterPractice(content, subject)
    for (const group of organized.groups) {
      const sameSubject = group.lectureIds?.[0]?.match(new RegExp(`^foundation-${subject}-(\\d+)$`))
      if (!sameSubject) continue
      const chapter = `lecture-${sameSubject[1].padStart(2, '0')}`
      assert.deepEqual(chapterLectureIds(group), [chapter], group.id)
      assert.ok(organized.lectures.some(lecture => lecture.id === chapter), group.id)
    }
    assert.equal(organized.groups.length, content.groups.length)
    assert.deepEqual(new Set(organized.groups.map(group => group.id)), new Set(content.groups.map(group => group.id)))
  }
})

test('screenshot ulcer question follows all 学成 questions in the existing ulcer chapter', () => {
  const content = organizeChapterPractice(bank('med'), 'med')
  const groups = originalQuestionsFirst(content.groups.filter(group => chapterLectureIds(group).includes('lecture-16')))
  const mock = groups.findIndex(group => group.id === 'med-foundation-mock-exam-20260907-q050')
  assert.ok(mock > 0)
  assert.equal(groups[mock].topic, '消化')
  assert.ok(groups.slice(mock + 1).every(group => group.supplement))
  assert.ok(groups.slice(0, mock).some(group => !group.supplement))
})

test('supplemental topics match the existing chapter systems rather than creating broad duplicate systems', () => {
  const checks = [
    ['physiology', 'lecture-27', '感觉系统'], ['physiology', 'lecture-33', '中枢神经系统'],
    ['pathology', 'lecture-23', '损伤与修复'], ['pathology', 'lecture-20', '传染病'],
    ['surgery', 'lecture-01', '颈部疾病'], ['surgery', 'lecture-11', '结直肠与肛管疾病'],
    ['biochemistry', 'lecture-01', '糖代谢'], ['biochemistry', 'lecture-02', '生物氧化'],
    ['biochemistry', 'lecture-16', '核酸'], ['biochemistry', 'lecture-12', '酶'],
  ]
  for (const [subject, id, topic] of checks) {
    const groups = organizeChapterPractice(bank(subject), subject).groups.filter(group => group.supplement && chapterLectureIds(group).includes(id))
    assert.ok(groups.length, `${subject} ${id}`)
    assert.ok(groups.every(group => group.topic === topic), `${subject} ${id}`)
  }
})

test('reordering preserves answers, revisions, evidence, IDs and saved-record addresses', () => {
  for (const subject of subjects) {
    const source = bank(subject)
    const snapshot = JSON.stringify(source)
    const original = new Map(source.groups.map(group => [group.id, group]))
    const organized = organizeChapterPractice(source, subject)
    for (const { topic, chapterLectureIds: navigation, ...group } of organized.groups) {
      const { topic: oldTopic, ...before } = original.get(group.id)
      assert.deepEqual(group, before, group.id)
    }
    assert.equal(JSON.stringify(source), snapshot)
    assert.deepEqual(organizeChapterPractice(organized, subject), organized)
    for (const id of new Set(organized.groups.flatMap(chapterLectureIds))) {
      const chapter = originalQuestionsFirst(organized.groups.filter(group => chapterLectureIds(group).includes(id)))
      const firstSupplement = chapter.findIndex(group => group.supplement)
      if (firstSupplement >= 0) assert.ok(chapter.slice(firstSupplement).every(group => group.supplement), `${subject} ${id}`)
    }
  }
})

test('foreign references retain their actual discipline and ethics papers share one chapter', () => {
  const content = organizeChapterPractice(bank('med'), 'med')
  const bilirubin = content.groups.find(group => group.id === 'med-foundation-mock-exam-20260907-q041')
  assert.deepEqual(chapterLectureIds(bilirubin), ['foundation-biochemistry-10'])
  assert.equal(bilirubin.lectureEvidence.sourceSubject, 'biochemistry')
  assert.ok(content.groups.filter(group => group.topic === '医学人文').every(group => chapterLectureIds(group).includes('lecture-99')))
})
