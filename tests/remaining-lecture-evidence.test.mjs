import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'
const read = name => JSON.parse(readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)))
const med = ['med-data','med-teacher-supplement','med-stage-exam-data','med-practitioner-upper-data'].flatMap(name => read(name).groups)
const surgeryNames = ['surgery-degenerative-spine-data','surgery-ortho-mixed-data','surgery-ortho-infection-data','surgery-fracture-data','surgery-chronic-injury-data','surgery-trunk-spine-data','surgery-deformity-data','surgery-limb-fracture-data','surgery-nonpurulent-arthritis-data','surgery-bone-tumor-data','surgery-practitioner-upper-data','surgery-teacher-supplement','surgery-stage-exam-data']
const surgery = surgeryNames.flatMap(name => read(name).groups)
const old = read('med-reviewed-lecture-evidence')
const remaining = read('med-remaining-reviewed-lecture-evidence')
const ortho = read('surgery-ortho-reviewed-lecture-evidence')
const strip = ({lectureEvidence,lectureEvidencePages,lectureEvidenceNotice,...item}) => ({...item,...(item.stems ? {stems:item.stems.map(strip)} : {})})
for (const [label,groups,review,expectedGroups,expectedStems,maxPage] of [
  ['remaining medicine',med,remaining,237,688,482],
  ['orthopedics',surgery,ortho,142,458,286],
]) {
 test(`${label}: complete coverage and per-stem references preserve all question content`, () => {
  const target = groups.filter(g => label === 'orthopedics' ? g.topic === '骨科' : review.scope.includes(g.topic))
  assert.equal(target.length,expectedGroups)
  assert.equal(target.reduce((n,g)=>n+g.stems.length,0),expectedStems)
  assert.deepEqual(Object.keys(review.groups).sort(),target.map(g=>g.id).sort())
  const updated=applyReviewedEvidence({groups},review)
  assert.deepEqual(updated.groups.map(strip),groups.map(strip))
  for(const group of updated.groups) {
   if (!review.groups[group.id]) { assert.equal(group,groups.find(g=>g.id===group.id)); continue }
   assert.equal(review.groups[group.id].stemPages.length,group.stems.length)
   group.stems.forEach((stem,index)=>{
    assert.ok(lectureForStem(group,index),group.id)
    assert.ok(stem.lectureEvidencePages.length)
    for(const page of stem.lectureEvidencePages) assert.ok(group.lectureEvidencePages.includes(page),group.id)
   })
  }
 })
 test(`${label}: images have genuine AVIF headers and bounded source page metadata`,()=>{
  for(const page of Object.values(review.pages)) {
   assert.ok(page.page>=1 && page.page<=maxPage)
   assert.ok(page.chapterPage>=1)
   assert.equal(page.sourceFile,review.sourceFile)
   const bytes=readFileSync(new URL(`../public/${page.image}`,import.meta.url))
   assert.equal(bytes.toString('ascii',4,8),'ftyp')
   assert.equal(bytes.toString('ascii',8,12),'avif')
  }
 })
}
test('old and new medicine reviews coexist, and important corrected pages are selected',()=>{
 const groups=applyReviewedEvidence({groups:med},old,remaining).groups
 assert.equal(groups.filter(g=>g.lectureEvidence?.image?.startsWith('site-assets/')).length,604)
 const get=id=>groups.find(g=>g.id===id)
 assert.equal(lectureForStem(get('practitioner-upper-20261019-q089'),0).chapterPage,1)
 assert.equal(lectureForStem(get('practitioner-upper-20261019-q093'),0).chapterPage,3)
 assert.equal(lectureForStem(get('practitioner-upper-20261019-q079'),0).chapterPage,9)
 assert.ok(get('p40-g1').lectureEvidencePages.length>=7)
 assert.match(get('med-teacher-08-18').lectureEvidenceNotice,/未找到/)
})
test('peripheral M symptom row accepts A, B and D with source correction recorded',()=>{
 const group=med.find(g=>g.id==='p74-g2')
 assert.deepEqual(group.stems[2].answer,['A','B','D'])
 assert.equal(group.stems[2].sourceAnswerRaw,'AB')
 assert.match(group.stems[2].answerSourceUrl,/avancpharma/)
 assert.equal(group.answerRevision,'penehyclidine-20261023')
 assert.deepEqual(group.stems.map(s=>s.answer.join('')),['C','E','ABD','D'])
})
