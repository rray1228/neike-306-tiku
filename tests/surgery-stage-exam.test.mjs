import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const exam = read('surgery-stage-exam-data')
const base = read('surgery-data')
const homework = read('surgery-teacher-supplement')
const q = n => exam.groups.find(g => g.stems[0].number === n)

test('37 source questions keep all choices and the supplied answer sequence', () => {
  assert.deepEqual(exam.groups.map(g=>g.stems[0].number), Array.from({length:37},(_,i)=>i+1))
  assert.equal(exam.groups.map(g=>g.stems[0].answerRaw).join(''),
    'BBDBB'+'DCDCC'+'DDACC'+'CBBBC'+'ADDCB'+'BCACC'+'CBADA'+'AD')
  const all = [...base.groups, ...homework.groups, ...exam.groups]
  assert.equal(new Set(all.map(g=>g.id)).size,all.length)
  for (const g of exam.groups) {
    assert.deepEqual(g.options.map(o=>o.key),['A','B','C','D'])
    assert.ok(g.options.every(o=>o.label.trim().length))
    assert.equal(g.stems.length,1)
    assert.deepEqual(g.stems[0].answer,[g.stems[0].answerRaw])
    assert.doesNotMatch([g.stems[0].text,...g.options.map(o=>o.label)].join(' '),/ttsx|每日计划|天天师兄|阶段考试/)
  }
})

test('questions are reachable in their tested chapters with existing lecture metadata', () => {
  const lectures = [...base.lectures,...homework.lectures,...exam.lectures]
  assert.equal(new Set(lectures.map(l=>l.id)).size,lectures.length)
  for (const g of exam.groups) {
    assert.ok([...base.topics,'外科总论','骨科'].includes(g.topic))
    assert.equal(g.lectureIds.length,1)
    const lecture=lectures.find(l=>l.id===g.lectureIds[0])
    assert.ok(lecture,g.id)
    assert.ok(lecture.file.endsWith('.pdf') && lecture.pageCount > 0)
    assert.equal(g.stems[0].lectureId,lecture.id)
  }
  const med = read('med-data')
  assert.equal(exam.lectures[0].file,med.lectures.find(l=>l.id==='lecture-16').file)
  for (const [n,lid] of [[1,'lecture-31'],[5,'lecture-32'],[9,'lecture-03'],
    [10,'med-lecture-16'],[11,'lecture-05'],[12,'lecture-07'],[21,'lecture-13'],
    [23,'med-lecture-23'],[24,'lecture-15'],[29,'lecture-29'],[33,'lecture-27'],[37,'lecture-25']])
    assert.deepEqual(q(n).lectureIds,[lid])
})

test('cross-page stems, options, scientific notation and original images survive', () => {
  for (const [n,pages] of [[6,[1,2]],[12,[2,3]],[19,[3,4]],[26,[4,5]],[33,[5,6]]])
    assert.deepEqual(q(n).sourcePages,pages)
  assert.match(q(6).stems[0].text,/淋巴结。核素扫描/)
  assert.equal(q(12).options[3].label,'肠外置，3-4 周后处理')
  assert.equal(q(19).options[3].label,'Whipple 术')
  assert.equal(q(26).options[0].label,'药物排石')
  assert.equal(q(33).options[3].label,'足背内侧感觉异常')
  assert.match(q(18).stems[0].text,/16×10⁹\/L/)
  assert.equal(q(37).options[3].label,'对放疗敏感')
  assert.equal(exam.pages.length,6)
  for (const p of exam.pages) assert.ok(existsSync(resolve('public',p.image)),p.image)
  for (const g of exam.groups) for (const page of g.sourcePages)
    assert.ok(exam.pages.some(p=>p.sourceKey===g.sourceKey && p.page===page))
})
