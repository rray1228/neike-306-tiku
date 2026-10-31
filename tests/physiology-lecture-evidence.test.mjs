import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const review = read('physiology-reviewed-lecture-evidence')
const sources = ['physiology-data', 'physiology-teacher-supplement', 'physiology-stage-exam-data', 'physiology-endocrine-summary-data']
const original = { groups: sources.flatMap(name => read(name).groups) }
const result = applyReviewedEvidence(original, review)
const group = id => result.groups.find(g => g.id === id)
const withoutEvidence = ({ lectureEvidence, lectureEvidencePages, lectureEvidenceNotice, ...item }) => ({
  ...item, ...(item.stems ? { stems: item.stems.map(withoutEvidence) } : {}),
})

test('physiology references cover every source and preserve all questions, answers and saved-progress IDs', () => {
  assert.equal(original.groups.length, 405)
  assert.equal(original.groups.reduce((n, g) => n + g.stems.length, 0), 809)
  assert.deepEqual(Object.keys(review.groups).sort(), original.groups.map(g => g.id).sort())
  assert.deepEqual(result.groups.map(withoutEvidence), original.groups.map(withoutEvidence))
  for (const g of result.groups) {
    const location = review.groups[g.id]
    assert.equal(location.stemPages.length, g.stems.length, g.id)
    assert.deepEqual(Object.keys(location.optionPages).sort(), g.options.map(o => o.key).sort(), g.id)
    g.stems.forEach((s, i) => {
      assert.deepEqual(s.lectureEvidencePages.map(p => p.page), location.stemPages[i].map(id => review.pages[id].page))
      assert.ok(s.lectureEvidencePages.every(p => g.lectureEvidencePages.includes(p)))
    })
    for (const [key, ids] of Object.entries(location.optionPages)) {
      for (const id of ids) {
        const p = g.lectureEvidencePages.find(p => p.image === review.pages[id].image)
        assert.ok(p?.optionKeys.includes(key), `${g.id}: option ${key}`)
      }
    }
  }
})

test('G-protein effectors open their direct source instead of the second-messenger summary', () => {
  const g = group('phys-007')
  assert.deepEqual(g.lectureEvidencePages.map(p => p.page), [64, 65, 66, 76])
  assert.equal(lectureForStem(g, 0).page, 64)
  assert.equal(lectureForStem(g, 1).page, 65)
  assert.equal(lectureForStem(g, 2).page, 65)
  const effectors = g.lectureEvidencePages.find(p => p.page === 64)
  assert.deepEqual(effectors.questionNumbers, [1])
  assert.deepEqual(effectors.optionKeys, ['A', 'G', 'I'])
  assert.ok(g.lectureEvidencePages.find(p => p.page === 76).optionKeys.includes('E'))
})

test('the three second-messenger questions have explicit scope and retain their original keys', () => {
  const g = group('phys-010')
  assert.equal(g.title, '第二信使与 Ca²⁺ 的靶分子')
  for (const s of g.stems.slice(0, 3)) assert.match(s.text, /第二信使/)
  assert.match(g.stems[3].text, /Ca²⁺ 的靶分子有哪些/)
  assert.deepEqual(g.stems.map(s => s.answerRaw), ['ABG', 'B', 'F', 'CDEH'])
  assert.ok(g.stems[0].sourceText.includes('G 蛋白耦联受体'))
})

test('cross-lecture material is attached to the actual knowledge pages', () => {
  assert.deepEqual(group('phys-teacher-12-10').stems[0].lectureEvidencePages.map(p => p.page), [326])
  assert.deepEqual(group('physiology-stage-exam-2026-09-q046').stems[0].lectureEvidencePages.map(p => p.page), [342, 343])
  assert.ok(group('phys-003').lectureEvidencePages.length >= 7)
  assert.ok(group('phys-020').lectureEvidencePages.some(p => p.page === 148))
})

test('uncovered stems are explicit and cannot fall back to a distractor or another question', () => {
  for (const id of ['phys-teacher-17-09', 'phys-teacher-17-10']) {
    const g = group(id)
    assert.deepEqual(g.stems[0].lectureEvidencePages, [])
    assert.equal(lectureForStem(g, 0), undefined)
    assert.match(g.lectureEvidenceNotice, /合集未单独展开/)
  }
})

test('every attached collection page is bounded and has a genuine image', () => {
  assert.equal(Object.keys(review.pages).length, 262)
  for (const p of Object.values(review.pages)) {
    assert.equal(p.sourceFile, '27跟课生理合集【带导图】.pdf')
    assert.ok(p.page > 0 && p.page <= 437)
    assert.equal(p.collectionPage, p.page)
    assert.match(p.image, new RegExp(`page-${String(p.page).padStart(3, '0')}\\.webp$`))
    const file = new URL(`../public/${p.image}`, import.meta.url)
    assert.ok(existsSync(file), p.image)
    const bytes = readFileSync(file)
    assert.equal(bytes.toString('ascii', 0, 4), 'RIFF')
    assert.equal(bytes.toString('ascii', 8, 12), 'WEBP')
  }
})
