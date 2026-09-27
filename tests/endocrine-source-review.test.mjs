import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'
import test from 'node:test'

const data = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const endocrine = data.groups.filter(group => group.topic === '内分泌')
const group = id => endocrine.find(item => item.id === id)

test('endocrine pages 61-68 retain every reviewed question block', () => {
  assert.equal(endocrine.length, 29)
  assert.equal(endocrine.reduce((n, g) => n + g.stems.length, 0), 127)
  assert.deepEqual(endocrine.filter(g => g.page === 64).map(g => g.id), ['p64-g1', 'p64-table1', 'p64-g2'])
  assert.deepEqual(endocrine.filter(g => g.page === 61).map(g => g.id), ['p61-g1', 'p61-g2', 'p61-g3', 'p61-g4'])
  assert.deepEqual(endocrine.filter(g => g.page === 66).map(g => g.id), ['p66-table1', 'p66-g1', 'p66-g2', 'p66-g3'])
  for (const g of endocrine) {
    assert.equal(new Set(g.options.map(option => option.key)).size, g.options.length, g.id)
    for (const stem of g.stems) {
      assert.ok(stem.answer.length, `${g.id}: ${stem.text}`)
      assert.ok(stem.answer.every(key => g.options.some(option => option.key === key)), `${g.id}: ${stem.text}`)
      assert.equal(stem.answerMode, stem.answer.length > 1 ? '多选' : '单选')
    }
    if (g.lectureEvidence) assert.ok(existsSync(resolve('public', g.lectureEvidence.image)), g.id)
  }
})

test('thyroid and pheochromocytoma wording matches source and lectures', () => {
  assert.equal(group('p61-g2').options.find(o => o.key === 'B')?.label, '皱额无能：眼球向上看时前额皮肤不出现皱纹')
  assert.deepEqual(group('p61-g4').stems.map(s => s.answer.join('')), ['BDFH', 'ACEG'])
  assert.equal(group('p62-g3').options.find(o => o.key === 'D')?.label, '诊断甲亢不用TT3、TT4')
  assert.equal(group('p62-g5').stems.at(-1)?.text, '神经肽Y')
})

test('Cushing option bank keeps the original A-I alignment', () => {
  const cushing = group('p63-g2')
  assert.deepEqual(cushing.options.map(o => o.label), [
    '若伴皮肤、乳房、心房黏液瘤、睾丸肿瘤、垂体生长激素瘤，为Carney综合征',
    '微腺瘤',
    '多为色素性（原发性色素沉着结节性肾上腺皮质病/Meador综合征）',
    '小细胞肺癌',
    '大腺瘤',
    '类癌',
    '增生',
    '胸腺癌',
    '食物依赖性库欣综合征：抑胃肽受体在肾上腺皮质异位表达，餐后皮质醇分泌增多，而清晨空腹时皮质醇正常或降低',
  ])
  assert.deepEqual(cushing.stems.map(s => s.answer.join('')), ['AC', 'BEG', 'I', 'DFH'])
})

test('diabetes groups restore truncated options and the omitted CKD table', () => {
  const emergencies = group('p65-g2')
  assert.equal(emergencies.options.find(o => o.key === 'D')?.label, '有酸中毒，出现Kussmaul深快呼吸')
  assert.match(emergencies.options.find(o => o.key === 'N')?.label, /pH≤6\.9.*低钾血症.*脑水肿/)

  const ckd = group('p66-table1')
  assert.deepEqual(ckd.stems.map(s => s.answer.join('')), ['AGM', 'BHM', 'CIN', 'DJO', 'EKP', 'FLP', 'Q', 'R', 'S'])
  assert.equal(ckd.lectureEvidence.lectureId, 'lecture-38')
  assert.equal(ckd.lectureEvidence.page, 4)
  assert.match(emergencies.options.find(o => o.key === 'P')?.label, /无休克.*且血钠/)
  assert.deepEqual(group('p64-table1').stems.map(s => s.answer.join('')), ['A', 'B', 'C', 'D', 'E', 'C'])
  assert.equal(group('p63-g1').options[0].label, '双侧肾上腺小结节性增生')

  assert.equal(group('p66-g2').options.find(o => o.key === 'B')?.label, '阿尔茨海默病')
  assert.equal(group('p67-g4').options.find(o => o.key === 'A')?.label, '晚上血糖高')
  assert.equal(group('p67-g6').options.find(o => o.key === 'B')?.label, '夜间胰岛素应用不足')
})
