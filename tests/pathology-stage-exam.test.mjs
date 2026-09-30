import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const data = read('pathology-stage-exam-data')
const base = read('pathology-data')
const homework = read('pathology-teacher-supplement')
const q = n => data.groups.find(g => g.stems[0].number === n)

test('all 51 original questions and supplied answers survive without ID collisions', () => {
  assert.deepEqual(data.groups.map(g => g.stems[0].number), Array.from({length:51}, (_,i)=>i+1))
  const answers = data.groups.map(g=>g.stems[0].answerRaw).join('')
  assert.deepEqual([answers.slice(0,15),answers.slice(15,30),answers.slice(30,45),answers.slice(45)], [
    'DBAADDDAAAADCAA', 'BDDADBCACCBDCAD', 'DCDAAABABCBBCBD', 'DCAAAB',
  ])
  const all = [...base.groups,...homework.groups,...data.groups]
  assert.equal(new Set(all.map(g=>g.id)).size, all.length)
  for (const g of data.groups) {
    assert.deepEqual(g.options.map(o=>o.key), ['A','B','C','D'])
    assert.ok(g.options.every(o=>o.label.length))
    assert.equal(g.stems.length,1)
    assert.equal(g.stems[0].answerMode,'单选')
    assert.deepEqual(g.stems[0].answer,[g.stems[0].answerRaw])
    assert.ok(g.options.some(o=>o.key===g.stems[0].answerRaw))
    assert.doesNotMatch([g.stems[0].text,...g.options.map(o=>o.label)].join(' '), /ttsx|每日计划|微信|不要焦虑/)
  }
})

test('classification follows the tested chapter and never invents missing lectures', () => {
  for (const g of data.groups) {
    assert.ok([...base.topics,...data.topics].includes(g.topic),g.id)
    for (const lid of g.lectureIds) assert.ok(base.lectures.some(l=>l.id===lid),g.id)
  }
  // Organ names in distractors do not turn general pathology into an organ chapter.
  assert.equal(q(1).topic,'损伤与修复')
  assert.equal(q(7).topic,'局部血液循环障碍')
  assert.equal(q(11).topic,'炎症')
  assert.equal(q(18).topic,'免疫性疾病')
  assert.equal(q(25).topic,'呼吸系统')
  assert.equal(q(49).topic,'传染病')
  assert.deepEqual(q(18).lectureIds,['lecture-17'])
  for (const n of [32,33]) assert.equal(q(n).topic,'淋巴造血系统')
  for (const n of [34,35,36,37]) assert.equal(q(n).topic,'泌尿系统')
  for (const n of [32,33,34,35,36,37]) assert.deepEqual(q(n).lectureIds,[])
})

test('page-break continuations retain all choices and matching source pages', () => {
  for (const [n,pages] of [[6,[1,2]],[21,[3,4]],[28,[4,5]],[35,[5,6]],[50,[7,8]]])
    assert.deepEqual(q(n).sourcePages,pages)
  assert.equal(q(6).options.at(-1).label,'毛细血管')
  assert.equal(q(21).options[0].label,'Aschoff 小体具有诊断意义')
  assert.equal(q(28).options.at(-1).label,'假幽门腺化生')
  assert.equal(q(35).options.at(-1).label,'浆细胞构成')
  assert.equal(q(50).options[0].label,'虫卵')
  assert.equal(q(51).options.at(-1).label,'病变常累及主动脉，不累及骨骼')
  assert.equal(data.pages.length,8)
  for (const p of data.pages) assert.ok(existsSync(resolve('public',p.image)),p.image)
  for (const g of data.groups) for (const n of g.sourcePages)
    assert.ok(data.pages.some(p=>p.sourceKey===g.sourceKey && p.page===n))
})
