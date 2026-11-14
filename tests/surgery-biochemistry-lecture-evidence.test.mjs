import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'
import surgeryCore from '../src/data/surgery-general-core-data.js'
import { surgeryGeneralInfectionGroups, surgeryGeneralLaterGroups } from '../src/data/surgery-general-late-data.js'
const directory = new URL('../src/data/',import.meta.url)
const read = name => JSON.parse(readFileSync(new URL(`${name}.json`,directory)))
// Imported papers carry their own evidence and are checked in their import tests.
const collect = subject => readdirSync(directory).filter(name=>name.startsWith(subject)&&name.endsWith('.json')&&!/(?:sprint-exam|foundation-mock-exam|easy-review-2027)-data\.json$/.test(name)).flatMap(name=>{
 const d=JSON.parse(readFileSync(new URL(name,directory)))
 return Array.isArray(d.groups) ? d.groups : []
})
const surgery=[...collect('surgery'),...surgeryCore.groups,...surgeryGeneralInfectionGroups,...surgeryGeneralLaterGroups]
const biochemistry=collect('biochemistry')
const reviewedSurgery=read('surgery-remaining-reviewed-lecture-evidence')
const reviewedBiochemistry=read('biochemistry-reviewed-lecture-evidence')
const reviewedOrtho=read('surgery-ortho-reviewed-lecture-evidence')
const biochemistryCollection='27生化跟课版合集【带导图】.pdf'
const strip=({lectureEvidence,lectureEvidencePages,lectureEvidenceNotice,...rest})=>({...rest,...(rest.stems ? {stems:rest.stems.map(strip)} : {})})
for (const [subject,groups,review,count,stems] of [
 ['surgery',surgery,reviewedSurgery,343,1025],
 ['biochemistry',biochemistry,reviewedBiochemistry,336,1005],
]) {
 test(`${subject}: all requested groups receive per-stem evidence without content or storage changes`,()=>{
  const target=groups.filter(g=>subject==='biochemistry'||g.topic!=='骨科')
  assert.equal(target.length,count)
  assert.equal(target.reduce((sum,g)=>sum+g.stems.length,0),stems)
  assert.deepEqual(Object.keys(review.groups).sort(),target.map(g=>g.id).sort())
  const next=applyReviewedEvidence({groups},review)
  assert.deepEqual(next.groups.map(strip),groups.map(strip))
  for(const g of next.groups){
   if(!review.groups[g.id]){assert.equal(g,groups.find(original=>original.id===g.id));continue}
   assert.equal(review.groups[g.id].stemPages.length,g.stems.length,g.id)
   g.stems.forEach((stem,index)=>{
    assert.ok(lectureForStem(g,index),`${g.id} stem ${index}`)
    assert.ok(stem.lectureEvidencePages.length)
    for(const p of stem.lectureEvidencePages)assert.ok(g.lectureEvidencePages.includes(p),g.id)
   })
  }
 })
 test(`${subject}: every source page is bounded and backed by a genuine AVIF file`,()=>{
  const bounds={'27 外科跟课合集【带导图】.pdf':286,'27跟课版内科合集【带导图】.pdf':482,[biochemistryCollection]:193}
  for(const p of Object.values(review.pages)){
   assert.ok(bounds[p.sourceFile],p.sourceFile)
   assert.ok(p.page>=1&&p.page<=bounds[p.sourceFile],p.image)
   const bytes=readFileSync(new URL(`../public/${p.image}`,import.meta.url))
   assert.equal(bytes.toString('ascii',4,8),'ftyp',p.image)
   assert.equal(bytes.toString('ascii',8,12),'avif',p.image)
  }
 })
}
test('orthopedic and other surgery reviews coexist across all surgery sources',()=>{
 const result=applyReviewedEvidence({groups:surgery},reviewedOrtho,reviewedSurgery)
 assert.equal(result.groups.length,485)
 assert.equal(result.groups.filter(g=>g.lectureEvidence?.image?.startsWith('site-assets/')).length,485)
 assert.ok(result.groups.find(g=>g.id==='limb-fracture-dislocation-ankle-ligaments')?.lectureEvidence)
 const caseGroup=result.groups.find(g=>g.id==='surgery-teacher-02-02-03')
 assert.ok(caseGroup.lectureEvidencePages.some(p=>p.sourceSubject==='med'&&p.lectureNumber===13))
})
test('biochemistry uses the collection with mind maps for question groups and both imported exams',()=>{
 assert.equal(reviewedBiochemistry.sourceFile,biochemistryCollection)
 const pages=Object.values(reviewedBiochemistry.pages)
 assert.ok(pages.every(p=>p.sourceFile===biochemistryCollection))
 assert.ok(pages.some(p=>p.page===105))
 assert.ok(pages.some(p=>p.page===193))
 const assetByPage=new Map(pages.map(p=>[p.page,p.image]))
 const additionalQuestions=read('biochemistry-xuecheng-37-data')
 assert.deepEqual(additionalQuestions.map(group=>group.lectureEvidencePages.map(page=>page.page)),[[6],[6],[7],[9],[25],[5],[24],[17,6],[17],[33],[33],[37,38]])
 for(const group of additionalQuestions){
  assert.deepEqual(group.lectureEvidence,group.lectureEvidencePages[0],group.id)
  for(const page of group.lectureEvidencePages){
   assert.equal(page.sourceFile,biochemistryCollection,group.id)
   assert.equal(page.image,assetByPage.get(page.page),group.id)
  }
 }
 const enzymeGroup=additionalQuestions.find(group=>group.id==='xuecheng-37-20261114-q04')
 assert.deepEqual(enzymeGroup.stems.map((_,index)=>lectureForStem(enzymeGroup,index).page),[17,6])
 for(const name of ['biochemistry-foundation-mock-exam-data','biochemistry-sprint-exam-data']){
  for(const group of read(name).groups){
   assert.deepEqual(group.lectureEvidence,group.lectureEvidencePages[0],group.id)
   for(const stem of group.stems)assert.deepEqual(stem.lectureEvidencePages,group.lectureEvidencePages,group.id)
   const evidence=group.lectureEvidencePages.filter(p=>p.sourceFile)
   assert.ok(evidence.length,group.id)
   for(const p of evidence){
    assert.equal(p.sourceFile,biochemistryCollection,group.id)
    assert.equal(p.image,assetByPage.get(p.page),group.id)
   }
  }
 }
})

test('TNM knowledge on mixed exam/summary pages and the adult-heart supplement are retained',()=>{
 const result=applyReviewedEvidence({groups:surgery},reviewedSurgery)
 for(const id of ['practitioner-upper-20261019-q134','surgery-stage-exam-2026-10-q011']){
  const group=result.groups.find(g=>g.id===id)
  assert.equal(lectureForStem(group,0).page,36)
  assert.equal(lectureForStem(group,0).lectureNumber,5)
 }
 const biochemistryResult=applyReviewedEvidence({groups:biochemistry},reviewedBiochemistry)
 const exam=biochemistryResult.groups.find(g=>g.id==='biochemistry-stage-exam-2026-10-q006')
 assert.ok(exam.lectureEvidencePages.some(p=>p.sourceFile===biochemistryCollection&&p.page===45))
})
