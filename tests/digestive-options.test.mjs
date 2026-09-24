import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'

const payload = JSON.parse(readFileSync(new URL('../src/data/med-data.json', import.meta.url)))
const groups = payload.groups.filter((group) => group.topic === '消化')
const byId = new Map(groups.map((group) => [group.id, group]))

const group = (id) => {
  const item = byId.get(id)
  assert.ok(item, `missing group ${id}`)
  return item
}

const label = (groupId, key) => {
  const option = group(groupId).options.find((item) => item.key === key)
  assert.ok(option, `${groupId} missing option ${key}`)
  return option.label
}

test('all digestive groups have complete option banks and valid answers', () => {
  assert.equal(groups.length, 43)
  for (const item of groups) {
    const keys = item.options.map((option) => option.key)
    assert.equal(new Set(keys).size, keys.length, `${item.id} has duplicate option keys`)
    for (const [index, stem] of item.stems.entries()) {
      assert.ok(stem.answer.length, `${item.id} stem ${index + 1} has no answer`)
      for (const answer of stem.answer) {
        assert.ok(keys.includes(answer), `${item.id} stem ${index + 1} references missing ${answer}`)
      }
    }
  }
})

test('truncated digestive options match the source pages and lectures', () => {
  const expected = {
    'p20-g1': { G: 'ACh' },
    'p20-g2': { J: '癔球症（患者感到咽部不适，有异物感、堵塞感，但又没有真正的吞咽困难）' },
    'p21-g3': {
      B: '与K+竞争结合H+-K+-ATP酶',
      G: '酸环境稳定、不需酸激活、起效快、持续时间长、夜间作用确切、用药个体差异小和不良反应少',
    },
    'p24-g1': {
      S: '胃溃疡病史患者腹痛开始不规律',
      T: '若发热、右上腹痛、呃逆→膈下脓肿',
      V: '可有移动性浊音（腹水>1000ml）',
      W: '不缓解→瘢痕性为主→内镜或胃大部切除术（术前用抗生素）',
    },
    'p29-g2': { A: '杵状指' },
    'p32-g3': {
      A: '海蛇头样（脐周血回流：脐以上向上+脐以下向下，上上下下）',
      E: '静脉连续性潺潺音/嗡嗡音',
    },
    'p33-g1': {
      Q: '总胆固醇TC↓、胆固醇酯/总胆固醇↓',
      U: '黄疸（主要为肝细胞性黄疸）',
    },
    'p33-g2': {
      C: '腹水为渗出液：SAAG<11、细胞>500×10^6/L且以多个核细胞（中性粒细胞）为主',
      D: '腹水为渗出液：SAAG<11、细胞>500×10^6/L且以单个核细胞（淋巴细胞）为主',
    },
    'p33-g3': {
      F: '渗出液（SAAG<11、细胞>500×10^6/L且以多个核细胞/中性粒细胞为主）',
    },
  }

  for (const [groupId, options] of Object.entries(expected)) {
    for (const [key, text] of Object.entries(options)) assert.equal(label(groupId, key), text)
  }
})

test('source-page tables and page 33 option pools are separate answerable groups', () => {
  assert.deepEqual(group('p25-g4').stems.map((stem) => stem.answer.join('')), ['A', 'B', 'C', 'A'])
  assert.deepEqual(
    payload.groups.filter((item) => item.page === 33).map((item) => item.id),
    ['p33-g1', 'p33-g1b', 'p33-g1c', 'p33-g2', 'p33-g3'],
  )
  assert.deepEqual(group('p33-g1').stems.map((stem) => stem.answer.join('')), ['ABCEFGHLNPQRSTU', 'DEFHIJKMOP'])
  assert.deepEqual(group('p33-g1b').stems.map((stem) => stem.answer.join('')), ['ACF', 'BDE'])
  assert.deepEqual(group('p33-g1c').stems.map((stem) => stem.answer.join('')), ['BEFGHIJ', 'ACE', 'CDEJ'])
  for (const id of ['p25-g4', 'p33-g1', 'p33-g1b', 'p33-g1c', 'p33-g2', 'p33-g3']) {
    const evidence = group(id).lectureEvidence
    assert.ok(evidence, `${id} missing lecture evidence`)
    assert.ok(existsSync(resolve('public', evidence.image)), `${id} missing ${evidence.image}`)
  }
})

test('known digestive OCR fragments and unfinished punctuation are gone', () => {
  const labels = groups.flatMap((item) => item.options.map((option) => option.label))
  const joined = labels.join('\n')
  for (const fragment of ['球症(', '夜间作用确\n', '穿孔性大出血', '瘘痿性', 'A.状指', '潺潺音/音', '黄疽', '黄痘', '500x10%']) {
    assert.ok(!joined.includes(fragment), `stale OCR fragment remains: ${fragment}`)
  }
  for (const text of labels) {
    const openings = (text.match(/[（(]/g) ?? []).length
    const closings = (text.match(/[）)]/g) ?? []).length
    assert.equal(openings, closings, `unbalanced parentheses: ${text}`)
  }
})
