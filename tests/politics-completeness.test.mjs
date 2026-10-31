import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {organizePoliticsContent} from '../src/politics-navigation.js'
const read=name=>JSON.parse(readFileSync(new URL(`../src/data/${name}.json`,import.meta.url)))
const practice=read('politics-data'),book=read('politics-selftest-data'),technique=read('politics-technique-data')
const extra=read('politics-selftest-completion'),homework=read('politics-technique-completion')
const content=organizePoliticsContent(practice,book,technique,extra,homework)
test('all nineteen book self-test sections appear in source order, including sections without matching',()=>{
 assert.deepEqual(content.topics.map(t=>content.lectures.filter(l=>l.topic===t&&l.title.startsWith('自测')).length),[6,3,4,3,3])
 assert.deepEqual(content.lectures.filter(l=>l.topic==='马原'&&l.title.startsWith('自测')).map(l=>l.title),[
 '自测1 · 专题一～专题五','自测2 · 专题六～专题十','自测3 · 专题十一、专题十二','自测4 · 专题十三～专题十五','自测5 · 专题十六～专题十八','自测6 · 专题十九～专题二十'])
 assert.equal(extra.groups.filter(g=>g.judgement).flatMap(g=>g.stems).length,152)
 assert.equal(extra.groups.filter(g=>g.kindLabel==='填空题').flatMap(g=>g.stems).length,19)
 const fiveBlanks=extra.groups.find(g=>g.pdfPage===27).stems[3]
 assert.equal(fiveBlanks.answer.length,5)
 assert.equal(fiveBlanks.answer[4],'政治上层建筑')
})
test('all missing book judgement keys match the supplied answer sections',()=>{
 const keys={14:'BBBBBBAABB',26:'ABABAABABB',33:'BABBABBBB',38:'ABBBAB',53:'BBAAA',80:'AABABBBBAB',92:'BABAABBBBA',111:'BAAABABB',123:'ABAAAAAABB',135:'BBABBBBA',149:'AABABAABBB',171:'ABBBBBBBAA',184:'BBBAABBBBB',198:'BBAABBABBA',210:'BBBBBAABAA',223:'BBABBBAA',233:'BBBBAABB'}
 for(const g of extra.groups.filter(g=>g.judgement))assert.equal(g.stems.map(s=>s.answer[0]).join(''),keys[g.pdfPage],g.id)
})
test('all thirteen technique assignments, drawing and review prompts have an entry',()=>{
 assert.deepEqual(content.topics.map(t=>content.lectures.filter(l=>l.topic===t&&l.title.startsWith('技巧班作业')).length),[5,1,2,3,2])
 assert.deepEqual(homework.groups.filter(g=>g.kindLabel==='思路训练').map(g=>[g.pdfPage,g.stems.length]),[[55,5],[56,2],[63,1],[66,1],[72,1]])
 assert.equal(homework.groups.filter(g=>g.kindLabel==='复盘笔记').length,6)
 assert.equal(homework.groups.find(g=>g.pdfPage===53).stems[0].answerMode,'自评')
 assert.match(homework.groups.find(g=>g.pdfPage===53).stems[0].explanation,/标为“略”/)
 for(const g of homework.groups){assert.ok(g.selfReview);assert.ok(g.stems.every(s=>s.answerMode==='自评'&&s.answer.length===0))}
})
test('existing 333 answers and storage IDs are retained; every new item has source proof and a matching chapter',()=>{
 const old=[...practice.groups,...book.groups,...technique.groups]
 assert.equal(content.groups.length,77)
 assert.equal(content.meta.stemCount,522)
 assert.equal(new Set(content.groups.map(g=>g.id)).size,77)
 for(const g of old)assert.deepEqual(content.groups.find(x=>x.id===g.id).stems,g.stems)
 for(const g of content.groups){
  assert.ok(content.lectures.some(l=>l.id===g.lectureIds[0]&&l.topic===g.topic))
  assert.ok(g.lectureEvidence?.image?.match(/^\/politics\/reference-pages\/[a-f0-9]{24}\.webp$/))
 }
 for(const g of [...extra.groups,...homework.groups])for(const s of g.stems){
  assert.ok(s.text&&s.explanation&&s.answerPdfPage)
  assert.ok(!/====|扫描|公众号|[鹽䯀顯]|国案|经沐/.test(s.text+s.explanation))
  if(!g.selfReview)assert.ok(s.answer.length)
 }
})
