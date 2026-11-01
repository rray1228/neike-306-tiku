import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { applyReviewedMedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const review = read('med-reviewed-lecture-evidence')
const groups = ['med-data', 'med-teacher-supplement', 'med-stage-exam-data', 'med-practitioner-upper-data'].flatMap(name => read(name).groups)
const content = { groups }
test('tuberculous pericarditis distinguishes the lecture table dry and wet presentations', () => {
  const g = groups.find(g => g.id === 'p76-g2')
  const dry = g.stems.find(s => s.text === '结核性心包炎（干性）')
  const wet = g.stems.find(s => s.text === '结核性心包炎（湿性）')
  assert.equal(g.stems.length, 6)
  assert.deepEqual(dry.answer, [...'AGIMPRTW'])
  assert.deepEqual(wet.answer, [...'AGINQSTW'])
  assert.ok(!wet.answer.some(key => ['M', 'P', 'R'].includes(key)))
  assert.ok(!dry.answer.some(key => ['N', 'Q', 'S'].includes(key)))
  assert.match(g.sharedStem, /“—”表示未列出/)
  assert.deepEqual(g.stems.find(s => s.text === '化脓性心包炎').answer, [...'BFKU'])
  assert.ok(g.answerRevision)
})
const updated = applyReviewedMedEvidence(content, review)
const withoutEvidence = ({ lectureEvidence, lectureEvidencePages, ...item }) => ({
  ...item,
  ...(item.stems ? { stems: item.stems.map(withoutEvidence) } : {}),
})

test('all three systems receive reviewed pages without changing questions, answers or navigation', () => {
  const target = groups.filter(group => review.scope.includes(group.topic))
  assert.equal(target.length, 366)
  assert.equal(target.reduce((total, group) => total + group.stems.length, 0), 943)
  assert.deepEqual(Object.keys(review.groups).sort(), target.map(group => group.id).sort())
  assert.deepEqual(updated.groups.map(withoutEvidence), groups.map(withoutEvidence))
  for (const group of updated.groups) {
    if (!review.groups[group.id]) {
      assert.equal(group, groups.find(original => original.id === group.id))
      continue
    }
    assert.ok(group.lectureEvidencePages.length)
    assert.equal(review.groups[group.id].stemPages.length, group.stems.length)
    for (let index = 0; index < group.stems.length; index++) {
      assert.ok(group.lectureEvidencePages.includes(lectureForStem(group, index)), `${group.id} row ${index}`)
    }
  }
})

test('assets are genuine AVIF pages with accurate, bounded source references', () => {
  assert.equal(Object.keys(review.pages).length, 167)
  for (const page of Object.values(review.pages)) {
    const file = new URL(`../public/${page.image}`, import.meta.url)
    assert.ok(existsSync(file), page.image)
    const bytes = readFileSync(file)
    assert.equal(bytes.toString('ascii', 4, 8), 'ftyp', page.image)
    assert.equal(bytes.toString('ascii', 8, 12), 'avif', page.image)
    if (page.sourceSubject === 'med') {
      assert.equal(page.sourceFile, '27跟课版内科合集【带导图】.pdf')
      assert.ok(page.page >= 1 && page.page <= 482)
      assert.ok(page.image.endsWith(`page-${String(page.page).padStart(3, '0')}.avif`))
    }
  }
})

test('cross-chapter and ECG rows open their corresponding knowledge pages', () => {
  const group = id => updated.groups.find(group => group.id === id)
  const peritonitis = group('p33-g2')
  assert.deepEqual(peritonitis.lectureEvidencePages.map(page => page.page), [155, 121, 122])
  assert.ok(!peritonitis.lectureEvidencePages.some(page => page.chapterPage === 3 && page.lectureNumber === 17))
  const ecg = group('ecg56-g1')
  assert.equal(lectureForStem(ecg, 0).page, 449)
  assert.equal(lectureForStem(ecg, 7).page, 457)
  assert.equal(lectureForStem(ecg, 23).page, 467)
  const shared = group('practitioner-upper-20261019-q030')
  assert.deepEqual(shared.stems.map((_, index) => lectureForStem(shared, index).lectureNumber), [55, 56, 55])
  assert.equal(lectureForStem(group('practitioner-upper-20261019-q068'), 0).sourceSubject, 'surgery')
})
