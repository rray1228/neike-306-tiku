import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { applyReviewedEvidence, lectureForStem } from '../src/med-lecture-evidence.js'
import surgeryCore from '../src/data/surgery-general-core-data.js'
import { surgeryGeneralInfectionGroups, surgeryGeneralLaterGroups } from '../src/data/surgery-general-late-data.js'
const directory = new URL('../src/data/',import.meta.url)
const read = name => JSON.parse(readFileSync(new URL(`${name}.json`,directory)))
// Imported papers carry their own evidence and are checked in their import tests.
const collect = subject => readdirSync(directory).filter(name=>name.startsWith(subject)&&name.endsWith('.json')&&!/(?:sprint-exam|foundation-mock-exam)-data\.json$/.test(name)).flatMap(name=>{
 const d=JSON.parse(readFileSync(new URL(name,directory)))
 return Array.isArray(d.groups) ? d.groups : []
})
const surgery=[...collect('surgery'),...surgeryCore.groups,...surgeryGeneralInfectionGroups,...surgeryGeneralLaterGroups]
const biochemistry=collect('biochemistry')
const reviewedSurgery=read('surgery-remaining-reviewed-lecture-evidence')
const reviewedBiochemistry=read('biochemistry-reviewed-lecture-evidence')
const reviewedOrtho=read('surgery-ortho-reviewed-lecture-evidence')
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
  const bounds={'27 外科跟课合集【带导图】.pdf':286,'27跟课版内科合集【带导图】.pdf':482,'【精编版】生化合集.pdf':183,'27生化跟课版合集【带导图】.pdf':193}
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
test('biochemistry favors the selected precise collection and the small-gene and DNA rows have knowledge pages',()=>{
 assert.equal(reviewedBiochemistry.sourceFile,'【精编版】生化合集.pdf')
 assert.ok(Object.values(reviewedBiochemistry.pages).filter(p=>p.sourceFile===reviewedBiochemistry.sourceFile).length>=100)
 assert.ok(Object.values(reviewedBiochemistry.pages).some(p=>p.page===90))
 assert.ok(Object.values(reviewedBiochemistry.pages).some(p=>p.page===183))
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
 assert.ok(exam.lectureEvidencePages.some(p=>p.sourceFile==='27生化跟课版合集【带导图】.pdf'&&p.page===45))
})
