import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/physiology-stage-exam-data.json', import.meta.url)))
const base = JSON.parse(readFileSync(new URL('../src/data/physiology-data.json', import.meta.url)))
const homework = JSON.parse(readFileSync(new URL('../src/data/physiology-teacher-supplement.json', import.meta.url)))
const q = n => data.groups.find(g => g.stems[0].number === n)

test('every original number and every screenshot answer is retained exactly once', () => {
  assert.equal(data.groups.length, 62)
  assert.deepEqual(data.groups.map(g => g.stems[0].number), Array.from({length:62}, (_,i)=>i+1))
  const answers = data.groups.map(g => g.stems[0].answerRaw).join('')
  assert.deepEqual(Array.from({length:13}, (_,i)=>answers.slice(i*5,i*5+5)), [
    'BCCCC', 'BBDDC', 'BDDCA', 'DCCDA', 'CADDC', 'AACDA',
    'CBDCC', 'DCDCD', 'CDABA', 'CDBCC', 'ADACC', 'BAACA', 'CB',
  ])
  const all = [...base.groups, ...homework.groups, ...data.groups]
  assert.equal(new Set(all.map(g=>g.id)).size, all.length)
  for (const g of data.groups) {
    assert.deepEqual(g.options.map(o=>o.key), ['A','B','C','D'])
    assert.ok(g.options.every(o=>o.label.length))
    assert.equal(g.stems.length, 1)
    assert.equal(g.stems[0].answerMode, '单选')
    assert.deepEqual(g.stems[0].answer, [g.stems[0].answerRaw])
    assert.ok(g.options.some(o=>o.key===g.stems[0].answerRaw))
    assert.doesNotMatch([g.stems[0].text,...g.options.map(o=>o.label)].join(' '), /ttsx|每日计划|ACA|不要焦虑/)
  }
})

test('questions join the existing physiology lecture directory by tested knowledge', () => {
  for (const g of data.groups) {
    assert.ok(base.topics.includes(g.topic), g.id)
    assert.equal(g.lectureIds.length, 1)
    assert.ok(base.lectures.some(l=>l.id===g.lectureIds[0]), g.id)
    assert.equal(g.stems[0].lectureId, g.lectureIds[0])
  }
  // Cross-topic distractors must not move these questions to unrelated chapters.
  for (const [n,lecture] of [[2,2],[9,5],[13,7],[14,8],[15,6],[17,10],[19,11],
    [21,14],[29,20],[31,21],[32,22],[34,23],[35,23],[41,24],[46,29],
    [47,31],[48,31],[49,32],[50,33],[53,35],[56,38],[59,40],[62,41]]) {
    assert.deepEqual(q(n).lectureIds,[`lecture-${String(lecture).padStart(2,'0')}`])
  }
})

test('cross-page choices, numerical values and source images remain complete', () => {
  for (const [n,pages] of [[24,[4,5]],[30,[5,6]],[55,[9,10]],[61,[10,11]]])
    assert.deepEqual(q(n).sourcePages, pages)
  assert.equal(q(24).options.at(-1).label, '血红蛋白具有变构效应')
  assert.equal(q(30).options.at(-1).label, '蛋白质分解产物')
  assert.equal(q(55).options.at(-1).label, 'IGF-1')
  assert.equal(q(61).options.at(-1).label, '抑制母体免疫排斥')
  assert.equal(q(10).options[0].label, 'STAT')
  assert.match(q(34).stems[0].text, /1\.5 m².*16\.3 L.*146\.3 kJ\/\(m²·h\)/)
  assert.match(q(41).stems[0].text, /0\.02 mg\/ml.*12\.6 mg\/ml.*60 ml.*45%/)
  assert.equal(data.pages.length, 11)
  for (const p of data.pages) assert.ok(existsSync(resolve('public',p.image)), p.image)
  for (const g of data.groups) for (const n of g.sourcePages)
    assert.ok(data.pages.some(p=>p.sourceKey===g.sourceKey && p.page===n))
})
