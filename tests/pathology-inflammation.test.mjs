import { readFileSync, existsSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import assert from 'node:assert/strict'
import test from 'node:test'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'

const root = new URL('../', import.meta.url)
const bank = JSON.parse(readFileSync(new URL('src/data/pathology-data.json', root)))
const review = JSON.parse(readFileSync(new URL('src/data/pathology-reviewed-lecture-evidence.json', root)))
const group = bank.groups.find(g => g.id === 'p32-g2')

test('chemotaxis contains IL-1 J, not histamine I, without dropping another choice', () => {
  const stem = group.stems.find(s => s.text === '趋化因子')
  assert.deepEqual(stem.answer, [...'ABCDFHJ'])
  assert.equal(stem.answerMode, '多选')
  assert.equal(stem.sourceText, '趋化因子（ABCDFHJ）')
  assert.deepEqual(stem.answer.map(k => group.options.find(o => o.key === k).label), [
    'C5a', 'TNF', 'C3a', 'LTB4', '细菌产物', 'IL-8', 'IL-1',
  ])
  assert.equal(group.options.find(o => o.key === 'I').label, '组胺')
  assert.equal(group.options.length, 17)
  assert.ok(group.sourceText.includes(stem.sourceText))
  assert.ok(!group.sourceText.includes('ABCDFHI'))
})

test('all five neighboring answers and stable group identity remain unchanged', () => {
  assert.deepEqual(group.stems.filter(s => s.text !== '趋化因子').map(s => [s.text,s.answer.join('')]), [
    ['血管扩张','ACEGIKM'], ['发热','BEJ'], ['疼痛','EGK'],
    ['组织损伤','LMP'], ['主动终止急性炎症反应','NOQ'],
  ])
  assert.equal(group.id, 'p32-g2')
  assert.equal(group.answerRevision, 'chemotaxis-il1-20261030-v1')
  assert.equal(bank.groups.find(g => g.id === 'p32-g1').answerRevision, undefined)
  assert.equal(bank.groups.length, 77)
  assert.equal(bank.groups.flatMap(g => g.stems).length, 315)
})

test('all six stems retain lecture PDF page 199 and its existing image', () => {
  const updated = applyReviewedEvidence({groups:[group]},review).groups[0]
  for (let i=0; i<6; i++) {
    const page = lectureForStem(updated,i)
    assert.equal(page.page,199)
    assert.equal(page.sourceFile,'27病理精编版合集【带导图】.pdf')
    assert.ok(existsSync(new URL(`public/${page.image}`,root)))
  }
  assert.equal(updated.lectureEvidenceNotice,undefined)
})

test('manual generation and finalization retain the repair idempotently', () => {
  const result = spawnSync('python3',['-c',`
import sys, json, copy
sys.path.insert(0, 'scripts')
from pathology_manual_pages import manual_groups_for_page, repair_inflammation_chemotaxis
from finalize_pathology_content import repair_and_restore
with open('src/data/pathology-data.json') as f:
    bank = json.load(f)
actual = next(g for g in bank['groups'] if g['id'] == 'p32-g2')
manual = manual_groups_for_page(32)[1]
assert manual['answerRevision'] == actual['answerRevision']
assert manual['options'] == actual['options']
for a, b in zip(manual['stems'], actual['stems'], strict=True):
    for key in ('text', 'answer', 'answerMode', 'sourceText'):
        assert a[key] == b[key], key
before = copy.deepcopy(actual)
repair_inflammation_chemotaxis(actual)
assert before == actual
restored = repair_and_restore(copy.deepcopy(bank['groups']))
assert next(g for g in restored if g['id'] == 'p32-g2') == actual
`],{cwd:root,encoding:'utf8'})
  assert.equal(result.status,0,result.stderr || result.stdout)
})
