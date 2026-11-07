#!/usr/bin/env node

import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import content from '../src/data/surgery-general-core-data.js'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const groups = content.groups
const byId = new Map(groups.map((group) => [group.id, group]))

assert.deepEqual(content.topics, ['外科总论'])
assert.equal(groups.length, 29)
assert.equal(byId.size, 29)
assert.equal(groups.reduce((sum, group) => sum + group.stems.length, 0), 122)
assert.equal(groups.reduce((sum, group) => sum + group.options.length, 0), 245)
assert.equal(groups.filter((group) => group.kind === 'B').length, 25)
assert.equal(groups.filter((group) => group.kind === 'FILL').length, 4)

const expectedChoiceAnswers = {
  'surgery-general-core-t01': ['GJ', 'DFHI', 'BC', 'A', 'E', 'K'],
  'surgery-general-core-t02': ['DH', 'G', 'ABFI', 'E'],
  'surgery-general-core-t03': ['D', 'A', 'C', 'B'],
  'surgery-general-core-t04': ['G', 'BHJK', 'ABDFJ', 'AI', 'CEL'],
  'surgery-general-core-f01': ['BEFJN', 'DHMOS', 'AEGIKLQ', 'CPR'],
  'surgery-general-core-f02': ['ABCFKLNPQV', 'DEGHIJMORSTUW'],
  'surgery-general-core-f03a': ['AEFHJ', 'BCDGI'],
  'surgery-general-core-f03b': ['B', 'B', 'C', 'A'],
  'surgery-general-core-f04a': ['MNQ', 'ABCDEFGHIJKLOP'],
  'surgery-general-core-f04b': ['B', 'A', 'C', 'D'],
  'surgery-general-core-n01a': ['D', 'AE', 'F', 'G', 'B', 'C'],
  'surgery-general-core-n01b': ['D', 'C', 'C', 'C', 'B', 'A'],
  'surgery-general-core-n02a': ['A', 'A', 'A', 'B', 'B'],
  'surgery-general-core-n03a': ['A', 'BCDE', 'F', 'GH'],
  'surgery-general-core-n02b': ['ABCDEFGHI', 'JKL', 'M', 'N', 'O', 'P'],
  'surgery-general-core-n03b': ['A', 'B', 'C'],
  'surgery-general-core-n04a': ['C', 'B', 'A'],
  'surgery-general-core-n04b': ['ABCD', 'EFG', 'HIJ', 'KLMNOP', 'QRSTUVWXYZ', '①②③④⑤⑥'],
  'surgery-general-core-b01': ['BKOP', 'FHMN', 'ACGI', 'DEJL'],
  'surgery-general-core-b02': ['E', 'AJ', 'BCDFH', 'CDGHI', 'K'],
  'surgery-general-core-b03': ['BDEG', 'ACF'],
  'surgery-general-core-b04a': ['A', 'BCD'],
  'surgery-general-core-b04b': ['B', 'D', 'ACG', 'E', 'F'],
  'surgery-general-core-b04c': ['BC', 'DEFGIJ', 'A', 'H'],
  'surgery-general-core-b05a': ['AB', 'BC'],
}

const expectedFillAnswers = {
  'surgery-general-core-t05': [['100', '70', '70', '100'], ['500', '1000', '1500', '1500'], ['30', '10', '3']],
  'surgery-general-core-f05': [['135', '150', '142'], ['280', '310'], ['5.5', '3.5'], ['130', '135', '120', '130', '120'], ['2.75', '2.25'], ['1', '1']],
  'surgery-general-core-n05': [['16'], ['2', '2'], ['2', '2'], ['3', '3.5', '2', '3', '50', '60'], ['0.7', '1.3', '30', '40'], ['1.2', '1.5', '1', '1', '1', '2', '150', '200']],
  'surgery-general-core-b06': [['9', '46'], ['9', '18', '26', '46', '1'], ['1.5', '2000'], ['2', '1', '1', '1'], ['8', '16'], ['2000'], ['3', '5']],
}

const malformed = /[|°•“”‘’]|\s{2,}/
for (const group of groups) {
  assert.equal(group.page, 0)
  assert.equal(group.topic, '外科总论')
  assert.equal(group.hideSource, true)
  assert.equal(group.reviewState, '已完成结构校对')
  assert.deepEqual(group.reviewIssues, [])
  assert.equal(group.lectureIds.length, 1)
  assert.equal(group.lectureIds[0], group.lectureEvidence.lectureId)
  assert.ok(existsSync(join(root, 'public', group.lectureEvidence.image)), `${group.id}: missing lecture image`)

  const keys = group.options.map((option) => option.key)
  assert.equal(keys.length, new Set(keys).size)
  for (const value of [group.title, ...group.options.map((option) => option.label), ...group.stems.map((stem) => stem.text)]) {
    assert.equal(value.trim(), value)
    assert.ok(!malformed.test(value), `${group.id}: malformed text: ${value}`)
  }

  if (group.kind === 'B') {
    assert.equal(group.kindLabel, 'B型题')
    assert.equal(group.optionShuffleVersion, 1)
    const sourceOrder = group.options.map((option) => option.sourceKey)
    assert.notDeepEqual(sourceOrder, group.optionOriginalOrder, `${group.id}: options were not shuffled`)
    assert.deepEqual([...sourceOrder].sort(), [...group.optionOriginalOrder].sort())
    const currentToSource = Object.fromEntries(group.options.map((option) => [option.key, option.sourceKey]))
    const semanticAnswers = group.stems.map((stem) => stem.answer.map((key) => currentToSource[key]).sort().join(''))
    const expected = expectedChoiceAnswers[group.id].map((answer) => [...answer].sort().join(''))
    assert.deepEqual(semanticAnswers, expected, `${group.id}: answer remap mismatch`)
  } else {
    assert.equal(group.kindLabel, '填空题')
    assert.deepEqual(group.options, [])
    assert.deepEqual(group.stems.map((stem) => stem.answer), expectedFillAnswers[group.id])
    assert.ok(group.stems.every((stem) => stem.answerMode === '填空'))
    assert.ok(group.stems.every((stem) => stem.blankLabels.length === stem.answer.length))
  }
}

const allIds = []
for (const filename of [
  'surgery-data.json', 'surgery-fracture-data.json', 'surgery-deformity-data.json',
  'surgery-ortho-mixed-data.json', 'surgery-ortho-infection-data.json',
  'surgery-nonpurulent-arthritis-data.json', 'surgery-bone-tumor-data.json',
  'surgery-trunk-spine-data.json', 'surgery-degenerative-spine-data.json',
  'surgery-limb-fracture-data.json', 'surgery-general-data.json',
]) {
  const payload = JSON.parse(readFileSync(join(root, 'src', 'data', filename), 'utf8'))
  allIds.push(...payload.groups.map((group) => group.id))
}
allIds.push(...groups.map((group) => group.id))
assert.equal(allIds.length, new Set(allIds).size, 'duplicate surgery group ids')

assert.deepEqual(groups.slice(7, 11).map((group) => [group.id, group.stems.map((stem) => stem.text)]), [
  ['surgery-general-core-f03a', ['高钾血症', '静脉补KCl']],
  ['surgery-general-core-f03b', ['DKA：K⁺＜3.5 mmol/L', 'DKA：K⁺正常且尿量＞40 ml/h', 'DKA：K⁺正常且尿量＜30 ml/h', 'DKA：K⁺＞5.5 mmol/L']],
  ['surgery-general-core-f04a', ['高钙血症', '低钙血症']],
  ['surgery-general-core-f04b', ['体液缓冲系统', '肺', '肾', '组织细胞']],
])

for (const retiredMixedId of [
  'surgery-general-core-n01', 'surgery-general-core-n02', 'surgery-general-core-n03',
  'surgery-general-core-n03c', 'surgery-general-core-n04',
  'surgery-general-core-b04', 'surgery-general-core-b05',
]) assert.equal(byId.has(retiredMixedId), false, `${retiredMixedId}: mixed option pool returned`)

assert.deepEqual(groups.filter((group) => group.id.startsWith('surgery-general-core-n')).map((group) => group.id), [
  'surgery-general-core-n01a', 'surgery-general-core-n01b',
  'surgery-general-core-n02a', 'surgery-general-core-n03a',
  'surgery-general-core-n02b', 'surgery-general-core-n03b',
  'surgery-general-core-n04a', 'surgery-general-core-n04b',
  'surgery-general-core-n05',
])

assert.deepEqual(groups.filter((group) => group.id.startsWith('surgery-general-core-b04')).map((group) => group.id), [
  'surgery-general-core-b04a', 'surgery-general-core-b04b', 'surgery-general-core-b04c',
])

console.log({ groups: 29, stems: 122, options: 245, choice: 25, fill: 4, lecturePages: 12, status: 'ok' })
