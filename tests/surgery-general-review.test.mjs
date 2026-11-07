import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import core from '../src/data/surgery-general-core-data.js'
import { surgeryGeneralInfectionGroups, surgeryGeneralLaterGroups } from '../src/data/surgery-general-late-data.js'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'

const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const peri = read('surgery-general-data')
const groups = [...core.groups, ...surgeryGeneralInfectionGroups, ...peri.groups, ...surgeryGeneralLaterGroups]
const get = id => groups.find(group => group.id === id)
const sourceAnswer = (group, stem) => stem.answer.map(key => group.options.find(option => option.key === key).sourceKey).sort().join('')

test('all general-surgery pools have valid answers and no repeated or self-answering correct options', () => {
  assert.equal(groups.length, 93)
  assert.equal(groups.reduce((count, group) => count + group.stems.length, 0), 399)
  for (const group of groups) {
    const labels = group.options.map(option => option.label)
    assert.equal(new Set(labels).size, labels.length, group.id)
    for (const stem of group.stems) {
      if (stem.answerMode === '填空') {
        assert.equal((stem.text.match(/____/g) || []).length, stem.answer.length, group.id)
        assert.equal(stem.blankLabels.length, stem.answer.length, group.id)
      } else {
        assert.equal(new Set(stem.answer).size, stem.answer.length, group.id)
        assert.ok(stem.answer.every(key => group.options.some(option => option.key === key)), group.id)
        if (stem.answerMode !== '排序') {
          assert.ok(stem.answer.length < group.options.length, `${group.id}: selecting the whole pool is not a question`)
          assert.ok(stem.answer.every(key => group.options.find(option => option.key === key).label !== stem.text), `${group.id}: self-answering option`)
        }
      }
      for (const accepted of stem.acceptedAnswers || []) assert.equal(accepted.length, stem.answer.length, group.id)
    }
  }
})

test('frozen plasma and cryoprecipitate share one question but retain distinct indications', () => {
  const group = get('surgery-general-core-t04')
  assert.equal(group.stems.length, 5)
  const stem = group.stems[4]
  assert.equal(stem.text, '冰冻血浆或冷沉淀的适用情形')
  assert.equal(stem.answerMode, '多选')
  assert.deepEqual([...stem.answer].sort(), ['C', 'E', 'J'])
  assert.deepEqual(stem.answer.map(key => group.options.find(option => option.key === key).label), [
    '纤维蛋白原缺乏症', '甲型血友病', '肝疾病伴凝血障碍',
  ])
  assert.match(stem.explanation, /肝疾病伴凝血障碍对应冰冻血浆；纤维蛋白原缺乏症、甲型血友病列在冷沉淀下/)
  assert.equal(group.answerRevision, 'transfusion-plasma-cryo-combined-20261107')
})

test('decimals remain decimals, while genuine ranges retain separate endpoints', () => {
  const fever = get('surgery-general-p06').stems[0]
  assert.deepEqual(fever.answer, ['1.4', '2.7'])
  assert.equal((fever.text.match(/____/g) || []).length, 2)
  assert.equal(fever.answerDisplay, '1.4天；2.7天')
  assert.deepEqual(get('surgery-general-p05').stems[0].answer, ['4', '5'])
  assert.deepEqual(get('surgery-general-p03b').stems[5].answer, ['5.6', '11.2'])
  assert.deepEqual(get('surgery-general-core-f05').stems[2].answer, ['5.5', '3.5'])
})

test('adult burn areas total 100%, exclude the separately listed perineum, and formulas are parenthesized', () => {
  const group = get('surgery-general-core-b06')
  assert.deepEqual(group.stems[1].answer, ['9', '18', '26', '46', '1'])
  assert.equal(group.stems[1].answer.reduce((sum, value) => sum + Number(value), 0), 100)
  assert.match(group.stems[1].text, /前后躯干（不含会阴）/)
  assert.match(group.stems[0].text, /（____＋12－年龄）%/)
  assert.match(group.stems[4].text, /补液总量的一半/)
  assert.equal(group.answerRevision, 'burn-area-no-double-count-20261027')
})

test('local-anesthetic categorical ties accept both orders but not inversions across tiers', () => {
  const group = get('surgery-general-a09')
  const source = Object.fromEntries(group.options.map(option => [option.key, option.sourceKey]))
  const expected = { 1: ['BDCA', 'DBCA'], 3: ['BDCA', 'DBCA'], 4: ['CDAB', 'CDBA'], 5: ['CDAB', 'CDBA'] }
  for (const [index, orders] of Object.entries(expected)) {
    const stem = group.stems[Number(index)]
    const actual = new Set([stem.answer, ...stem.acceptedAnswers].map(answer => answer.map(key => source[key]).join('')))
    assert.deepEqual([...actual].sort(), orders)
    assert.match(stem.text, /同档者先后不限/)
    assert.match(stem.answerDisplay, /=/)
  }
  assert.equal(group.answerRevision, 'local-anesthetic-ties-20261027')
})

test('matching questions preserve every substantive lecture feature without all-select or identity-only stems', () => {
  const en = get('surgery-general-core-n04a')
  assert.deepEqual(en.stems.map(stem => sourceAnswer(en, stem)), ['C', 'B', 'A'])
  assert.ok(en.options.every(option => !/最常见|最严重/.test(option.label)))
  const inhalation = get('surgery-general-core-b04c')
  assert.deepEqual(inhalation.stems.map(stem => sourceAnswer(inhalation, stem)), ['BC', 'DEFGIJ', 'A', 'H'])
  assert.equal(new Set(inhalation.stems.flatMap(stem => stem.answer)).size, inhalation.options.length)
  assert.equal(get('surgery-general-core-b03').stems.length, 2)
  assert.equal(get('surgery-general-p04').stems.length, 7)
  assert.ok(get('surgery-general-p04').stems.slice(2).every(stem => stem.text.startsWith('全麻清醒后或腰麻6小时后：')))
})

test('text blanks accept equivalent symbols and DIC values carry their units', () => {
  const laparoscopy = get('surgery-general-other-05b').stems[0]
  assert.deepEqual(laparoscopy.acceptedAnswers, [['CO2'], ['二氧化碳']])
  const preAnesthesia = get('surgery-general-a11a').stems[0]
  assert.ok(preAnesthesia.acceptedAnswers.some(answer => answer.join(',') === '8.3,+,-'))
  assert.match(get('surgery-general-shock-07').stems[0].text, /血小板＜____×10⁹\/L/)
  assert.match(get('surgery-general-shock-07').stems[0].text, /纤维蛋白原＜____ g\/L/)
})

test('PN complications remain one shared group with six focused stems, 32 shuffled options, and complete lecture facts', () => {
  const group = get('surgery-general-core-n04b')
  assert.equal(group.stems.length, 6)
  assert.equal(group.options.length, 32)
  assert.equal(new Set(group.options.map(option => option.key)).size, 32)
  assert.equal(new Set(group.options.map(option => option.sourceKey)).size, 32)
  assert.ok(group.options.some(option => option.key === '⑥'))
  assert.notDeepEqual(group.options.map(option => option.sourceKey), group.optionOriginalOrder)
  assert.deepEqual(group.stems.map(stem => sourceAnswer(group, stem)), ['ABCD', 'EFG', 'HIJ', 'KLMNOP', 'QRSTUVWXYZ', '①②③④⑤⑥'])
  const answerLabels = index => group.stems[index].answer.map(key => group.options.find(option => option.key === key).label)
  assert.deepEqual(new Set(answerLabels(0)), new Set(['气胸', '空气栓塞', '血管损伤', '神经损伤']))
  assert.deepEqual(new Set(answerLabels(1)), new Set(['立即拔管', '抗生素治疗', '导管尖端细菌培养']))
  assert.ok(answerLabels(3).includes('葡萄糖耐受下降'))
  assert.ok(answerLabels(4).includes('胆囊收缩素分泌减少'))
  assert.ok(answerLabels(4).includes('急性非结石性胆囊炎'))
  for (const label of ['血钙升高', '尿钙升高', '碱性磷酸酶（ALP）升高']) assert.ok(answerLabels(5).includes(label))
  assert.ok(group.options.every(option => !/最常见|最严重|为标志/.test(option.label)))
  assert.match(group.stems[0].explanation, /气胸最常见、空气栓塞最严重/)
  assert.match(group.stems[3].explanation, /低磷为标志/)
  assert.equal(group.answerRevision, 'pn-complications-complete-20261028')
  assert.equal(new Set(group.stems.flatMap(stem => stem.answer)).size, 32)
})

test('nerve-block complications transpose the lecture table and separate the three nerve palsies', () => {
  const group = get('surgery-general-a07')
  assert.deepEqual(group.stems.map(stem => stem.text), [
    '颈丛阻滞', '臂丛阻滞：肌间沟径路', '臂丛阻滞：锁骨上径路', '肋间神经阻滞',
  ])
  assert.equal(group.options.length, 6)
  assert.deepEqual(new Set(group.options.map(option => option.label)), new Set([
    '高位硬膜外阻滞', '全脊髓麻醉', '膈神经麻痹', '喉返神经麻痹', '颈交感神经麻痹', '气胸',
  ]))
  assert.notDeepEqual(group.options.map(option => option.sourceKey), group.optionOriginalOrder)
  assert.deepEqual(group.stems.map(stem => sourceAnswer(group, stem)), ['ABCDE', 'ABCDE', 'CDEF', 'F'])
  assert.equal(group.stems.reduce((sum, stem) => sum + stem.answer.length, 0), 15)
  assert.deepEqual(group.stems.map(stem => stem.answerMode), ['多选', '多选', '多选', '单选'])
  assert.match(group.stems[0].explanation, /不能同时进行双侧深颈丛阻滞/)
  assert.equal(group.answerRevision, 'nerve-block-complications-transposed-20261028')
})

test('both lecture editions stay aligned after restructuring and retain exact burn and EN pages', () => {
  for (const name of ['surgery-remaining-reviewed-lecture-evidence', 'surgery-updated-lecture-evidence']) {
    const review = read(name)
    const reviewed = applyReviewedEvidence({ groups }, review).groups
    for (const group of reviewed) {
      assert.equal(review.groups[group.id].stemPages.length, group.stems.length, group.id)
      group.stems.forEach((_, index) => assert.ok(lectureForStem(group, index)?.image, `${group.id}:${index}`))
    }
    const burn = reviewed.find(group => group.id === 'surgery-general-core-b06')
    assert.equal(lectureForStem(burn, 1).lectureNumber, 33)
    assert.equal(lectureForStem(burn, 1).chapterPage, 1)
    const en = reviewed.find(group => group.id === 'surgery-general-core-n04a')
    assert.equal(lectureForStem(en, 0).lectureNumber, 32)
    assert.equal(lectureForStem(en, 0).chapterPage, 1)
    const pn = reviewed.find(group => group.id === 'surgery-general-core-n04b')
    assert.deepEqual(pn.stems.map((_, index) => lectureForStem(pn, index).chapterPage), [2, 2, 2, 2, 2, 3])
    const nerveBlocks = reviewed.find(group => group.id === 'surgery-general-a07')
    assert.deepEqual(nerveBlocks.stems.map((_, index) => [lectureForStem(nerveBlocks, index).lectureNumber, lectureForStem(nerveBlocks, index).chapterPage]), [[36, 3], [36, 3], [36, 3], [36, 3]])
  }
})
