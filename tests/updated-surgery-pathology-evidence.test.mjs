import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'
import surgeryCore from '../src/data/surgery-general-core-data.js'
import { surgeryGeneralInfectionGroups, surgeryGeneralLaterGroups } from '../src/data/surgery-general-late-data.js'
const directory = new URL('../src/data/', import.meta.url)
const read = name => JSON.parse(readFileSync(new URL(`${name}.json`, directory)))
// Keep this review's original scope; paper-specific evidence has separate checks.
const collect = subject => readdirSync(directory).filter(name => name.startsWith(subject) && name.endsWith('.json') && !/(?:sprint-exam|foundation-mock-exam|easy-review-2027)-data\.json$/.test(name)).flatMap(name => {
  const data = JSON.parse(readFileSync(new URL(name, directory)))
  return Array.isArray(data.groups) ? data.groups : []
})
const surgery = [...collect('surgery'), ...surgeryCore.groups, ...surgeryGeneralInfectionGroups, ...surgeryGeneralLaterGroups]
const pathology = collect('pathology')
const surgeryReview = read('surgery-updated-lecture-evidence')
const pathologyReview = read('pathology-reviewed-lecture-evidence')
const strip = ({ lectureEvidence, lectureEvidencePages, lectureEvidenceNotice, ...rest }) => ({ ...rest, ...(rest.stems ? { stems: rest.stems.map(strip) } : {}) })
for (const [subject, groups, review, count, stems] of [
  ['surgery', surgery, surgeryReview, 485, 1483],
  ['pathology', pathology, pathologyReview, 218, 456],
]) {
  test(`${subject}: every loaded group and stem has reviewed evidence without changing questions or saved-answer keys`, () => {
    assert.equal(groups.length, count)
    assert.equal(groups.reduce((sum, group) => sum + group.stems.length, 0), stems)
    assert.deepEqual(Object.keys(review.groups).sort(), groups.map(group => group.id).sort())
    const updated = applyReviewedEvidence({ groups }, review)
    assert.deepEqual(updated.groups.map(strip), groups.map(strip))
    for (const group of updated.groups) {
      assert.equal(review.groups[group.id].stemPages.length, group.stems.length)
      group.stems.forEach((stem, index) => {
        assert.ok(lectureForStem(group, index), `${group.id}:${index}`)
        assert.ok(stem.lectureEvidencePages.length, group.id)
        for (const page of stem.lectureEvidencePages) assert.ok(group.lectureEvidencePages.includes(page), group.id)
      })
    }
  })
  test(`${subject}: source bounds, page metadata and bundled AVIF files are valid`, () => {
    const bounds = { '27 外科跟课合集改.pdf': 232, '27病理精编版合集【带导图】.pdf': 233, '27跟课版内科合集【带导图】.pdf': 482 }
    for (const page of Object.values(review.pages)) {
      assert.ok(bounds[page.sourceFile], page.sourceFile)
      assert.ok(Number.isInteger(page.page) && page.page >= 1 && page.page <= bounds[page.sourceFile], page.title)
      assert.ok(page.title && page.pageLabel && page.sourceSubject, page.image)
      const bytes = readFileSync(new URL(`../public/${page.image}`, import.meta.url))
      assert.ok(bytes.length > 1000, page.image)
      assert.equal(bytes.toString('ascii', 4, 8), 'ftyp', page.image)
      assert.equal(bytes.toString('ascii', 8, 12), 'avif', page.image)
    }
  })
}
test('surgery edition migration retains every prior cross-source page and coverage notice', () => {
  const old = [read('surgery-ortho-reviewed-lecture-evidence'), read('surgery-remaining-reviewed-lecture-evidence')]
  const oldGroups = Object.assign({}, ...old.map(review => review.groups))
  for (const [id, location] of Object.entries(oldGroups)) {
    if (location.notice) assert.equal(surgeryReview.groups[id].notice, location.notice)
  }
  const pages = Object.values(surgeryReview.pages)
  assert.equal(pages.filter(page => page.sourceFile === surgeryReview.sourceFile).length, 153)
  assert.equal(pages.filter(page => page.sourceSubject === 'med').length, 14)
  assert.ok(pages.some(page => page.previousPage === 75 && page.page === 60))
  assert.ok(pages.some(page => page.previousPage === 180 && page.page === 147))
  assert.ok(pages.some(page => page.previousPage === 284 && page.page === 231))
})
test('pathology fixes misplaced pages and resolves the lecture-backed RAS answer', () => {
  const updated = applyReviewedEvidence({ groups: pathology }, pathologyReview).groups
  const get = id => updated.find(group => group.id === id)
  assert.equal(lectureForStem(get('p06-g1'), 0).page, 31)
  assert.equal(lectureForStem(get('p28-g3'), 4).page, 169)
  assert.ok(get('p35-g1').lectureEvidencePages.some(page => page.page === 220))
  assert.equal(get('p36-g1').lectureEvidenceNotice, undefined)
  assert.deepEqual(get('p36-g1').stems.find(stem => stem.text === 'RAS').answer, ['E', 'F', 'H', 'J', 'L', '①'])
  for (const number of [34, 35, 36]) {
    const group = get(`pathology-stage-exam-2026-09-q${String(number).padStart(3, '0')}`)
    assert.ok(group.lectureEvidencePages.some(page => page.sourceSubject === 'med'), group.id)
  }
})
