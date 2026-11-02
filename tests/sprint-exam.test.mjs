import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync,existsSync} from 'node:fs'
const subjects=['med','physiology','biochemistry','pathology','surgery']
const files=subjects.map(s=>JSON.parse(readFileSync(new URL(`../src/data/${s}-sprint-exam-data.json`,import.meta.url))))
const groups=files.flatMap(d=>d.groups)
const question=n=>groups.find(g=>g.stems[0].number===n)
test('sprint import preserves all 165 questions and exact answer modes',()=>{
 assert.equal(groups.length,165)
 assert.deepEqual(groups.map(g=>g.stems[0].number).sort((a,b)=>a-b),Array.from({length:165},(_,i)=>i+1))
 assert.equal(new Set(groups.map(g=>g.id)).size,165)
 for(const g of groups){const s=g.stems[0];assert.deepEqual(g.options.map(o=>o.key),['A','B','C','D']);assert.ok(g.options.every(o=>o.label.length));assert.ok(s.explanation.length>25);assert.ok(s.answer.length);assert.ok(s.answer.every(a=>g.options.some(o=>o.key===a)));assert.equal(s.answerMode,s.number>=136?'多选':'单选')}
 assert.deepEqual(question(154).stems[0].answer,['A','B','C'])
 assert.deepEqual(question(101).stems[0].answer,['A'])
 assert.equal(groups.filter(g=>g.kind==='B').length,20)
})
test('shared stems and evolving case details survive extraction',()=>{
 assert.match(question(78).sharedStem,/37.6-38/)
 assert.doesNotMatch(question(75).options[3].label,/37.6|大炮音/)
 assert.doesNotMatch(question(84).options[3].label,/球形红细胞|1.8/)
 assert.match(question(81).sharedStem,/120/)
 assert.match(question(73).sharedStem,/65mmHg/)
 assert.equal(groups.filter(g=>g.sharedStem).length,40)
 for(let n=116;n<=135;n+=2)assert.deepEqual(question(n).options,question(n+1).options)
})
test('all questions have real lecture images and original question pages',()=>{
 for(const d of files){assert.ok(d.groups.every(g=>d.topics.includes(g.topic)));for(const g of d.groups){assert.ok(g.lectureIds.length);assert.ok(g.lectureEvidencePages.length);for(const e of g.lectureEvidencePages)assert.ok(existsSync(new URL('../public/'+e.image,import.meta.url)),e.image);const page=d.pages.find(p=>p.page===g.page);assert.ok(page);assert.ok(existsSync(new URL('../public/'+page.image,import.meta.url)))}}
 assert.equal(question(143).lectureEvidencePages.filter(e=>e.pageLabel==='解析流程图').length,4)
 for(let n=108;n<=115;n++)assert.equal(question(n).topic,'医学人文')
})
test('ambiguous original key is preserved with an explicit explanation',()=>{
 assert.match(question(14).stems[0].explanation,/重叠/)
 assert.match(question(19).stems[0].explanation,/不止一个/)
 assert.match(question(73).stems[0].explanation,/65|不能/)
 assert.match(question(160).stems[0].explanation,/肠内/)
})
