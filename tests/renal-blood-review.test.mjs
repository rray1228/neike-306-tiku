import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'
import test from 'node:test'

const data = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const groups = data.groups.filter(g => ['肾脏', '血液'].includes(g.topic))
const group = id => data.groups.find(g => g.id === id)
const answers = id => group(id).stems.map(s => s.answer.join(''))
const option = (id, key) => group(id).options.find(o => o.key === key)?.label

test('renal and blood source blocks have answerable stems and correct chapter evidence', () => {
  for (const g of groups) {
    assert.equal(new Set(g.options.map(o => o.key)).size, g.options.length, g.id)
    const range = g.topic === '肾脏' ? [24, 27] : [28, 35]
    assert.ok(g.lectureIds.every(id => {const n = Number(id.slice(-2)); return n >= range[0] && n <= range[1]}), g.id)
    assert.ok(g.lectureIds.includes(g.lectureEvidence.lectureId), g.id)
    assert.ok(existsSync(resolve('public', g.lectureEvidence.image)), g.id)
    for (const s of g.stems) {
      assert.ok(s.answer.length, `${g.id}: ${s.text}`)
      assert.equal(new Set(s.answer).size, s.answer.length, g.id)
      assert.ok(s.answer.every(key => g.options.some(o => o.key === key)), g.id)
      assert.ok(['单选','多选','排序'].includes(s.answerMode), g.id)
      if (s.answerMode !== '排序') assert.equal(s.answerMode, s.answer.length > 1 ? '多选' : '单选', g.id)
    }
  }
})

test('CKD and RPGN inherit shared source bracket answers', () => {
  assert.deepEqual(answers('p38-g2'), ['D','BEF','HJM','JLM','GKN','ACI'])
  assert.deepEqual(answers('p40-g1').slice(1, 4), ['BJKMPdgik','BJKNOdgikm','BJKMQdgik'])
  assert.match(option('p40-g1','e'), /各种病理类型.*系膜增生性/)
})

test('hemolysis lowercase answers and omitted source questions are restored', () => {
  assert.deepEqual(answers('p45-g2'), ['aceg','bcdef'])
  assert.equal(group('p45-g3').stems[0].text, '红细胞自身缺陷和外部异常')
  assert.equal(answers('p45-g3').at(-1), 'ACEGHIJ')
  assert.equal(group('p46-g3').stems.at(-1).text, '起效慢、不单独用')
  assert.equal(answers('p46-g3').at(-1), 'G')
  assert.deepEqual(answers('p47-table1'), ['ACE','BCE'])
})

test('myeloma and MDS regimen pools preserve original letters and components', () => {
  assert.equal(group('p49-g3').options.map(o => o.key).join(''), 'ABCDEFGH')
  assert.deepEqual(answers('p49-g3'), ['AD','ABD','CH','FH','CEG'])
  assert.equal(option('p51-g1','D'), '蒽环类')
  assert.equal(option('p51-g1','C'), '地西他滨')
  assert.deepEqual(answers('p51-g1'), ['DI','A','CEG','FH'])
})

test('AML FAB and immunophenotypes retain case-sensitive option identities', () => {
  assert.equal(group('p52-g3').options.map(o => o.key).join(''), 'ABCDEFHI')
  assert.match(option('p52-g3','H'), /原和幼单核.*≥80%/)
  assert.match(option('p52-g3','B'), /各阶段粒细胞≥20%.*各阶段单核细胞≥20%/)
  assert.equal(answers('p52-g3')[5], 'H')
  assert.equal(answers('p60-g1')[6], 'CTc')
  assert.equal(answers('p60-g1').at(-1), 'Xb')
  assert.equal(answers('p57-g1')[1], 'ACFHJKLN')
})

test('lymphoma source wording and ranking survive review', () => {
  assert.match(option('p56-g1','C'), /ⅢE.*ⅢS.*ⅢE\+S/)
  assert.match(option('p56-g1','A'), /≥2组/)
  assert.equal(option('p58-g2','B'), '霍奇金细胞（单核）')
  assert.deepEqual(answers('p58-g3'), ['BACD','ABCD','CABD'])
  assert.ok(group('p58-g3').stems.every(s => s.answerMode === '排序'))
  assert.deepEqual(answers('p58-g4'), ['AB','CDE'])
})

test('lecture 56 supplemental cardiac groups are not mistaken for workbook page 56', () => {
  for (const id of ['ecg56-g1','lecture56-av-dissociation','lecture56-cardiac-enlargement']) {
    assert.equal(group(id).topic, '循环')
    assert.deepEqual(group(id).lectureIds, ['lecture-56'])
  }
})
