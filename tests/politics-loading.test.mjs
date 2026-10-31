import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { migratePoliticsAnswers, sourceStemNumber } from '../src/politics-answers.js'
import { organizePoliticsContent } from '../src/politics-navigation.js'

const root = new URL('../', import.meta.url)
const files = readdirSync(new URL('src/data/', root)).filter(name => /^politics.*\.json$/.test(name))
const read = name => JSON.parse(readFileSync(new URL(`src/data/${name}`, root)))
const daily = read('politics-daily-selftest-data.json')
const hash = bytes => createHash('sha256').update(bytes).digest('hex')

test('politics entry contains only small text data and every external original image is intact', () => {
  assert.ok(files.reduce((sum, name) => sum + statSync(new URL(`src/data/${name}`, root)).size, 0) < 900_000)
  const visit = value => {
    if (typeof value === 'string') {
      assert.ok(!value.startsWith('data:image'), 'images must never block the entry bundle')
      if (value.startsWith('/politics/reference-pages/')) {
        const bytes = readFileSync(new URL(`public${value}`, root))
        assert.equal(bytes.subarray(0, 4).toString(), 'RIFF')
        assert.equal(bytes.subarray(8, 12).toString(), 'WEBP')
        assert.ok(value.endsWith(`${hash(bytes).slice(0, 24)}.webp`))
      }
    } else if (Array.isArray(value)) value.forEach(visit)
    else if (value && typeof value === 'object') Object.values(value).forEach(visit)
  }
  files.forEach(name => visit(read(name)))
})

test('all existing non-daily questions, answers, IDs and exact image bytes survive extraction', () => {
  const expected = {
    'politics-data.json': '4a2446cb5066cc1a73cb4939ef1091d15ae0e5c52f1b88ac2a2bba1367cdffd7',
    'politics-selftest-completion.json': 'd2a1a6cc5d7fd494c86867dd1a0416b32649fdb437dab1b97c56fae10fbc37a6',
    'politics-selftest-data.json': '702879bf7ba8d11e3054dae978c1ca3e23f76e4ff6cf4f9a93f37e5566b37a92',
    'politics-technique-completion.json': '5b4e9e6e7c0c514d883855952095be067f60286dc484c6595028e1b65adc90b6',
    'politics-technique-data.json': '514d83896cc73958529b8833f53c7c54a87071410da36ad07db179a0ddbae025',
  }
  const normalize = value => typeof value === 'string' && value.startsWith('/politics/reference-pages/')
    ? `image-sha256:${hash(readFileSync(new URL(`public${value}`, root)))}`
    : Array.isArray(value) ? value.map(normalize)
      : value && typeof value === 'object' ? Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalize(item)])) : value
  for (const [name, digest] of Object.entries(expected)) assert.equal(hash(JSON.stringify(normalize(read(name)))), digest, name)
})

test('all legacy daily fill positions migrate once while original records and submissions remain intact', () => {
  let selections = { medical: { 0: ['untouched'] } }, submitted = { medical: true }
  let originals = 0
  for (const group of daily.groups) {
    selections[`politics:${group.id}`] = Object.fromEntries(group.stems.map((stem, index) => [index, Array.from({ length: stem.legacyBlankCount }, (_, blank) => `value-${stem.id}-${blank}`)]))
    submitted[`politics:${group.id}`] = true
    const sources = group.stems.flatMap(stem => stem.legacyBlankSources.flat()).map(([id, blank]) => `${id}:${blank}`)
    originals += sources.length
    assert.equal(new Set(sources).size, sources.length)
    for (const stem of group.stems) for (let blank = 0; blank < stem.legacyBlankCount; blank++) assert.ok(sources.includes(`${stem.id}:${blank}`))
  }
  assert.equal(originals, 488)
  const migrated = migratePoliticsAnswers(selections, submitted, daily.groups)
  for (const group of daily.groups) {
    const oldKey = `politics:${group.id}`, newKey = `${oldKey}:daily-text-v1`
    assert.equal(migrated.selections[oldKey], selections[oldKey])
    assert.equal(migrated.submitted[newKey], true)
    for (const [index, stem] of group.stems.entries()) {
      assert.equal(migrated.selections[newKey][index].length, stem.blankCount)
      for (const [id, blank] of stem.legacyBlankSources.flat()) assert.ok(migrated.selections[newKey][index].join('').includes(`value-${id}-${blank}`))
    }
  }
  const again = migratePoliticsAnswers(migrated.selections, migrated.submitted, daily.groups)
  assert.equal(again.selections, migrated.selections)
  assert.equal(again.submitted, migrated.submitted)
  assert.equal(migrated.selections.medical, selections.medical)
})

test('adjacent crop remnants belong to their original text questions and no answers are invented', () => {
  const stems = daily.groups.flatMap(group => group.stems)
  assert.equal(stems.length, 149)
  const stem = id => stems.find(item => item.id === id)
  assert.match(stem('politics-daily-day29-思法-s02').text, /培养社会主义【空4】和【空5】/)
  assert.ok(stem('politics-daily-day29-思法-s03').text.startsWith('有序的公共生活'))
  assert.match(stem('politics-daily-day30-思法-s02').text, /关系党【空3】/)
  assert.ok(stem('politics-daily-day30-思法-s03').text.startsWith('法律权利与法律义务'))
  const split = daily.groups.find(group => group.day === 10 && group.topic.endsWith('毛中特'))
  assert.equal(sourceStemNumber(split, split.stems[0], 0), 5)
  assert.equal(sourceStemNumber({}, { number: 5 }, 0), 1)
  for (const item of stems) {
    assert.ok(!/^Day\d+/.test(item.text))
    assert.ok(!item.image)
    assert.ok(item.answer.every(value => value === ''))
    assert.equal(item.answerState, '待补答案')
  }
})

test('political entry and record migration work without newer Array.at or Object.hasOwn built-ins', () => {
  const at = Array.prototype.at, hasOwn = Object.hasOwn
  try {
    Array.prototype.at = undefined
    Object.hasOwn = undefined
    const content = organizePoliticsContent(...['politics-data', 'politics-selftest-data', 'politics-technique-data', 'politics-selftest-completion', 'politics-technique-completion', 'politics-daily-selftest-data'].map(name => read(`${name}.json`)))
    assert.equal(content.groups.length, 111)
    assert.equal(content.meta.stemCount, 671)
    const group = daily.groups[0], key = `politics:${group.id}`
    const result = migratePoliticsAnswers({ [key]: { 0: ['saved'] } }, {}, [group])
    assert.equal(result.selections[`${key}:daily-text-v1`][0][0], 'saved')
  } finally { Array.prototype.at = at; Object.hasOwn = hasOwn }
})
