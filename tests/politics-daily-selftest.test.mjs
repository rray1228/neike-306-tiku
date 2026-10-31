import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { organizePoliticsContent } from '../src/politics-navigation.js'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const daily = read('politics-daily-selftest-data')
const previous = ['politics-data', 'politics-selftest-data', 'politics-technique-data', 'politics-selftest-completion', 'politics-technique-completion'].map(read)
const original = organizePoliticsContent(...previous)
const combined = organizePoliticsContent(...previous, daily)

test('the complete thirty-day workbook retains all 149 original question numbers, continuations and fill slots', () => {
  const counts = [5,6,5,4,5,8,9,6,4,6,6,7,5,4,5,3,4,3,5,5,4,5,5,4,4,3,5,5,4,5]
  assert.equal(daily.meta.stemCount, 149)
  assert.equal(daily.meta.blankCount, 468)
  assert.equal(daily.meta.legacyBlankCount, 488)
  for (let day = 1; day <= 30; day++) {
    const groups = daily.groups.filter(g => g.day === day)
    const stems = groups.flatMap(g => g.stems).sort((a,b) => a.number - b.number)
    assert.deepEqual(stems.map(s => s.number), Array.from({length:counts[day-1]}, (_,i) => i+1), `Day${day}`)
    for (const group of groups) {
      assert.ok(group.dailySelftest && group.pendingAnswers && group.bookSelftest)
      assert.ok(daily.referenceImages[group.lectureEvidence.image].match(/^\/politics\/reference-pages\/[a-f0-9]{24}\.webp$/))
      for (const stem of group.stems) {
        assert.ok(!stem.image)
        assert.ok(stem.originalImage.match(/^\/politics\/reference-pages\/[a-f0-9]{24}\.webp$/))
        assert.deepEqual([...stem.text.matchAll(/【空(\d+)】/g)].map(match => Number(match[1])), Array.from({ length: stem.blankCount }, (_, index) => index + 1))
        assert.equal(stem.answerState, '待补答案')
        assert.equal(stem.answerMode, '填空')
        assert.equal(stem.answer.length, stem.blankCount)
        assert.ok(stem.answer.length > 0 && stem.answer.every(value => value === ''))
        assert.ok(stem.sourcePdfPages.every(page => page === 2*day+1 || page === 2*day+2))
      }
    }
  }
  const continued = daily.groups.find(g => g.day === 1).stems.find(s => s.number === 4)
  assert.deepEqual(continued.sourcePdfPages, [3,4])
  assert.equal(daily.groups.find(g => g.day === 30).stems.at(-1).number, 5)
})

test('daily exercises extend each subject directory while preserving every existing chapter and answer ID', () => {
  assert.equal(combined.groups.length, original.groups.length + 34)
  assert.equal(combined.meta.stemCount, original.meta.stemCount + 149)
  assert.equal(new Set(combined.groups.map(g => g.id)).size, combined.groups.length)
  for (const chapter of original.lectures) assert.deepEqual(combined.lectures.find(l => l.id === chapter.id), chapter)
  for (const group of original.groups) assert.deepEqual(combined.groups.find(g => g.id === group.id), group)
  for (const group of combined.groups.filter(g => g.dailySelftest)) {
    const chapter = combined.lectures.find(l => l.id === group.lectureIds[0])
    assert.equal(chapter.topic, group.topic)
    assert.match(chapter.title, new RegExp(`^自测\\d+ · Day${group.day}｜`))
  }
  assert.equal(combined.groups.find(g => g.day === 10 && g.stems.some(s => s.number === 5)).topic, '毛中特')
  assert.equal(combined.groups.find(g => g.day === 10 && g.stems.some(s => s.number === 6)).topic, '习思想')
})
