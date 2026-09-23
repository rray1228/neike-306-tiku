import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import assert from 'node:assert/strict'

const data = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const group = id => data.groups.find(item => item.id === id)
const reviewedIds = ['p80-g3', 'p81-g2', 'p82-g3', 'p82-g4', 'p83-g2', 'p83-g3', 'p83-g4', 'p86-g1', 'p86-g2', 'p86-g3', 'p86-table1', 'p91-g4', 'p92-g1', 'p89-table1', 'p89-table2', 'p92-table1']

test('reviewed cardiac groups have valid answer keys and unique options', () => {
  for (const id of reviewedIds) {
    const g = group(id)
    assert.ok(g, id)
    assert.equal(data.groups.filter(item => item.id === id).length, 1)
    assert.equal(new Set(g.options.map(o => o.key)).size, g.options.length, id)
    assert.equal(new Set(g.options.map(o => o.label)).size, g.options.length, id)
    for (const s of g.stems) {
      assert.ok(s.answer.length, `${id}: ${s.text}`)
      assert.ok(s.answer.every(key => g.options.some(o => o.key === key)), `${id}: ${s.text}`)
      assert.equal(new Set(s.answer).size, s.answer.length)
      assert.equal(s.answerMode, s.answer.length > 1 ? '多选' : '单选')
    }
    if (g.lectureEvidence) assert.ok(existsSync(resolve('public', g.lectureEvidence.image)), id)
  }
})

test('page 92 restores omitted/misread letters and separate SGLT2 limits', () => {
  const g = group('p92-g1')
  const label = key => g.options.find(o => o.key === key)?.label
  assert.match(label('K'), /二度Ⅱ型/)
  assert.equal(label('e'), '收缩压＜90 mmHg')
  assert.equal(label('f'), '房颤')
  assert.match(label('c'), /LVEF≤35%.*HR≥70/)
  assert.equal(label('d'), undefined)
  assert.deepEqual(g.stems.find(s => s.text === '伊伐布雷定适应证').answer, ['c'])
  assert.deepEqual(g.stems.find(s => s.text === '伊伐布雷定不用于').answer, ['E', 'f'])
  assert.deepEqual(g.stems.find(s => /达格列净/.test(s.text)).answer, ['Y'])
  assert.deepEqual(g.stems.find(s => /恩格列净/.test(s.text)).answer, ['a'])
  assert.deepEqual(g.stems.find(s => s.text === '血管扩张剂禁忌／不宜使用的情况').answer, ['X', 'e', 'h'])
})

test('chapter attribution separates hypertension cross-topic drugs from heart failure', () => {
  assert.deepEqual(group('p80-g3').lectureIds, ['lecture-52'])
  assert.ok(!group('p80-g3').options.some(o => o.key === 'X'))
  assert.deepEqual(group('p92-g1').lectureIds, ['lecture-55'])
  for (const id of ['p86-g1','p86-g2','p86-g3','p89-table1','p89-table2']) {
    assert.deepEqual(group(id).lectureIds, ['lecture-54'])
  }
  const drugGroups = ['p80-g3','p91-g4','p92-g1'].map(group)
  const signatures = drugGroups.map(g => JSON.stringify(g.stems.map(s => [s.text, s.answer.map(k => g.options.find(o => o.key === k).label).sort()]).sort()))
  assert.equal(new Set(signatures).size, drugGroups.length, 'delete only truly identical groups')
})

test('S1 weakening includes cardiomyopathy after restoring the misprinted J option', () => {
  const g = group('p81-g2')
  assert.equal(g.options.find(o => o.key === 'J')?.label, '心肌病')
  assert.deepEqual(g.stems.find(s => s.text === 'S1减弱').answer, ['B', 'D', 'E', 'G', 'H', 'J', 'L', 'N'])
})

test('page 82 auscultation locations use their own option bank', () => {
  const g = group('p82-g3')
  assert.deepEqual(g.options.map(o => [o.key, o.label]), [
    ['A', '肺动脉瓣'],
    ['B', '主动脉瓣第二听诊区'],
    ['C', '三尖瓣'],
    ['D', '二尖瓣'],
    ['E', '室间隔'],
    ['F', '主动脉瓣第一听诊区'],
    ['G', '心脏裸区'],
  ])
  assert.deepEqual(g.stems.map(s => s.answer.join('')), ['D', 'A', 'F', 'BEG', 'C', 'F', 'B'])
})

test('page 82 valve murmur patterns preserve the original option bank', () => {
  const g = group('p82-g4')
  assert.deepEqual(g.options.map(o => [o.key, o.label]), [
    ['A', '一贯型'],
    ['B', '收缩期'],
    ['C', '递减型'],
    ['D', '递增型'],
    ['E', '递增递减型'],
    ['F', '舒张期'],
  ])
  assert.deepEqual(g.stems.map(s => s.answer.join('')), ['DF', 'AB', 'BE', 'CF'])
})

test('page 83 left sternal border group preserves the source heading hierarchy', () => {
  const g = group('p83-g2')
  assert.equal(g.title, '胸骨左缘3～4肋间听诊')
  assert.equal(g.stems[0].text, '舒张期杂音')
  assert.deepEqual(g.stems.map(s => s.answer.join('')), ['F', 'AEG', 'CH', 'BD'])
})

test('page 83 ventricular enlargement directions match the source and lecture', () => {
  const g = group('p83-g3')
  assert.equal(g.options.find(o => o.key === 'G')?.label, '心前区/剑突下搏动弥散')
  assert.equal(g.options.find(o => o.key === 'H')?.label, '心尖搏动多向左下移位')
  assert.equal(g.options.find(o => o.key === 'J')?.label, '心尖搏动多向左移位')
  assert.deepEqual(g.stems.map(s => s.answer.join('')), ['ADFHIKMO', 'BCEGJLN'])
})

test('page 83 abnormal pulse options match the source and lecture', () => {
  const g = group('p83-g4')
  assert.deepEqual(g.options.map(o => [o.key, o.label]), [
    ['A', '吸气时脉搏显著减弱甚至消失'],
    ['B', 'P<心率'],
    ['C', '严重的右心衰'],
    ['D', '房颤'],
    ['E', '严重的心包积液/心脏压塞'],
    ['F', '脉搏骤起骤落'],
    ['G', '严重的缩窄性心包炎'],
    ['H', '甲亢'],
    ['I', '严重的支气管哮喘'],
    ['J', '脉搏强弱交替'],
    ['K', '严重的COPD'],
    ['L', '左心衰'],
    ['M', '超声心动图室间隔抖动征/吸气时室间隔左移'],
    ['N', '慢性主闭'],
    ['O', '严重的胸膜疾病（大量胸腔积液、张力性气胸）'],
  ])
  assert.deepEqual(g.stems.map(s => s.answer.join('')), ['BD', 'FHN', 'JL', 'ACEGIKMO'])
})

test('all four original tables become answerable B-type groups', () => {
  assert.deepEqual(group('p86-table1').stems.map(s => s.answer.join('')), ['ACDFH','BEGI'])
  assert.equal(group('p89-table1').stems.length, 5)
  assert.equal(group('p89-table2').stems.length, 6)
  assert.equal(group('p92-table1').stems.length, 2)
  assert.deepEqual(group('p89-table1').stems.map(s => s.answer.join('')), ['ABE','ABE','ABCE','ABCDFG','ABDF'])
  assert.deepEqual(group('p89-table2').stems.map(s => s.answer.join('')), ['ABCD','ABCDE','ACDE','ABDEF','BDEF','C'])
  assert.deepEqual(group('p92-table1').stems.map(s => s.answer.join('')), ['ACDEG','BCDEFH'])
})

test('coronary tables link to the exact lecture content rather than a generic treatment page', () => {
  const ecg = group('p89-table1')
  const drugs = group('p89-table2')
  assert.equal(ecg.lectureEvidence.lectureId, 'lecture-54')
  assert.equal(ecg.lectureEvidence.page, 8)
  assert.equal(ecg.lectureEvidence.image, 'med/lecture-pages/lecture-54-page-08.webp')
  assert.match(ecg.options.find(o => o.key === 'B').label, /缺血损伤.*不等同于心肌坏死/)
  assert.equal(drugs.lectureEvidence.lectureId, 'lecture-54')
  assert.equal(drugs.lectureEvidence.page, 18)
  assert.equal(drugs.lectureEvidence.image, 'med/lecture-pages/lecture-54-page-18.webp')
  assert.match(drugs.lectureEvidence.title, /第18页.*治疗小结/)
  assert.deepEqual(drugs.options.map(o => o.key), ['A','B','C','D','E','F'])
  assert.match(drugs.stems[2].text, /急性冠脉综合征/)
  assert.deepEqual(drugs.stems.find(s => s.text === '变异型心绞痛首选药物').answer, ['C'])
})
