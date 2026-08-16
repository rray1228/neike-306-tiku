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
assert.equal(groups.length, 21)
assert.equal(byId.size, 21)
assert.equal(groups.reduce((sum, group) => sum + group.stems.length, 0), 111)
assert.equal(groups.reduce((sum, group) => sum + group.options.length, 0), 235)
assert.equal(groups.filter((group) => group.kind === 'B').length, 17)
assert.equal(groups.filter((group) => group.kind === 'FILL').length, 4)

const expectedChoiceAnswers = {
  'surgery-general-core-t01': ['GJ', 'DFHI', 'BC', 'A', 'E', 'K'],
  'surgery-general-core-t02': ['DH', 'G', 'ABFI', 'E'],
  'surgery-general-core-t03': ['D', 'A', 'C', 'B'],
  'surgery-general-core-t04': ['G', 'BHJK', 'ABDFJ', 'AI', 'L', 'CE'],
  'surgery-general-core-f01': ['BEFJN', 'DHMOS', 'AEGIKLQ', 'CPR'],
  'surgery-general-core-f02': ['ABCFKLNPQV', 'DEGHIJMORSTUW'],
  'surgery-general-core-f03': ['AGHJM', 'CDEIK', 'F', 'F', 'L', 'B'],
  'surgery-general-core-f04': ['ORU', 'ABCDEFGHIJKNST', 'M', 'L', 'P', 'Q'],
  'surgery-general-core-n01': ['E', 'AF', 'G', 'H', 'B', 'C', 'K', 'J', 'J', 'J', 'I', 'D'],
  'surgery-general-core-n02': ['FG', 'ACEIKLMNOPQ', 'BR', 'DHJ'],
  'surgery-general-core-n03': ['J', 'FGHK', 'B', 'CD', 'A', 'E', 'I'],
  'surgery-general-core-n04': ['DHW', 'GLSU', 'ANV', 'BCFOQ', 'EIKMPR', 'JTX'],
  'surgery-general-core-b01': ['BKOP', 'FHMN', 'ACGI', 'DEJL'],
  'surgery-general-core-b02': ['E', 'AJ', 'BCDFH', 'CDGHI'],
  'surgery-general-core-b03': ['BDEG', 'ACF', 'H'],
  'surgery-general-core-b04': ['O', 'HIJ', 'G', 'M', 'ALS', 'P', 'Q', 'BCDEFKNRTU'],
  'surgery-general-core-b05': ['AC', 'CD', 'B'],
}

const expectedFillAnswers = {
  'surgery-general-core-t05': [['100', '70', '70', '100'], ['500', '1000', '1500', '1500'], ['30', '10', '3']],
  'surgery-general-core-f05': [['135', '150', '142'], ['280', '310'], ['5.5', '3.5'], ['130', '135', '120', '130', '120'], ['2.75', '2.25'], ['1', '1']],
  'surgery-general-core-n05': [['16'], ['2', '2'], ['2', '2'], ['3', '3.5', '2', '3', '50', '60'], ['0.7', '1.3', '30', '40'], ['1.2', '1.5', '1', '1', '1', '2', '150', '200']],
  'surgery-general-core-b06': [['9', '46'], ['9', '18', '27', '46', '1'], ['1.5', '2000'], ['2', '1', '1', '1'], ['8', '16'], ['2000'], ['3', '5']],
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

console.log({ groups: 21, stems: 111, options: 235, choice: 17, fill: 4, lecturePages: 12, status: 'ok' })
