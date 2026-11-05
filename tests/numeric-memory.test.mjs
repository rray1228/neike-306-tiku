import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { migrateNumericRecords, numericSearchRanges, numericHighlightParts, numericAnswerCorrect, numericParts, numericRows, numericRangeParts, numericProseRanges, filterNumericItems } from '../src/numeric-memory.js'
import { studyViewUrl } from '../src/supplement-tests.js'
import { highlightParts, memoryTextMatches, indexMnemonics, searchMnemonics } from '../src/mnemonic-search.js'

const data = JSON.parse(readFileSync(new URL('../src/data/numeric-memory-data.json', import.meta.url)))

test('numeric bank covers all 95 lecture sources with stable unique ids and real source pages', () => {
  assert.equal(data.sources.length, 95)
  assert.equal(data.sources.filter(s => s.subject === 'med').length, 57)
  assert.equal(data.sources.filter(s => s.subject === 'surgery').length, 38)
  assert.equal(new Set(data.items.map(i => i.id)).size, data.items.length)
  for (const item of data.items) {
    assert.ok(item.text && item.chapter && item.blanks.length, item.id)
    assert.ok(item.source.pages.length)
    assert.equal(item.source.images.length, item.source.pages.length)
    for (const image of item.source.images) assert.ok(existsSync(new URL('../public/' + image, import.meta.url)), image)
  }
  for (const source of data.sources) assert.equal(data.items.filter(i => i.source.file === source.file && i.subject === source.subject).length, source.count)
})

test('each cloze can reconstruct the source paragraph exactly with no overlapping answer spans', () => {
  for (const item of data.items) {
    assert.equal(numericParts(item).map(p => p.index === undefined ? p.text : p.answer).join(''), item.text)
    let end = 0
    for (const blank of item.blanks) {
      assert.ok(blank.start >= end, item.id)
      assert.equal(item.text.slice(blank.start, blank.end), blank.answer)
      assert.ok(numericAnswerCorrect(blank.answer, blank.answer))
      end = blank.end
    }
    assert.ok(!/20\d{2}N\d|[ABCD][.．]\s*\d+%|每日计划|真题解析·/.test(item.text), item.id)
  }
})

test('answer normalization accepts range typography and equivalent decimals, preserving order and comparisons', () => {
  for (const value of ['２～３', '2 至 3', '2—3', '2.0-3.00']) assert.ok(numericAnswerCorrect(value, '2-3'))
  for (const value of ['', '3-2', '23', '2', '>2-3', '2-3天']) assert.ok(!numericAnswerCorrect(value, '2-3'))
  assert.ok(numericAnswerCorrect('0.50', '0.5'))
  assert.ok(numericAnswerCorrect('140 / 90', '140/90'))
})

test('shared search accepts range typography without merging numbers and highlights only actual matches', () => {
  for (const query of ['6-8','6–8','６～８','6 - 8']) {
    assert.ok(memoryTextMatches('术后 6-8 周复查',query))
    for (const text of ['68周','16-8周','6-80周']) assert.ok(!memoryTextMatches(text,query),`${text} / ${query}`)
    const parts=highlightParts('6-8周，另有68周和16-8周',query)
    assert.deepEqual(parts.filter(p=>p.match).map(p=>p.text),['6-8'])
  }
  assert.ok(memoryTextMatches('术后 6-8 周复查','术后 6～8'))
  const indexed=indexMnemonics(['6-8周','68周','16-8周'].map((text,n)=>({id:String(n),title:text,subject:'med',chapter:'测试',blocks:[{kind:'fact',parts:[{text}]}]})))
  assert.deepEqual(searchMnemonics(indexed,{query:'6–8'}).map(i=>i.id),['0'])
  const a=filterNumericItems(data.items,{query:'6-8'}).map(i=>i.id)
  assert.ok(a.length)
  assert.deepEqual(filterNumericItems(data.items,{query:'6–8'}).map(i=>i.id),a)
})

test('keyboard rows preserve the complete fact and original blank indices across line breaks', () => {
  for (const item of data.items) {
    const rows = numericRows(item)
    assert.equal(rows.map(row => row.map(part => part.index === undefined ? part.text : part.answer).join('')).join('\n'), item.text, item.id)
    assert.deepEqual(rows.flat().filter(part => part.index !== undefined).map(part => part.index), item.blanks.map((_, index) => index), item.id)
  }
})

test('table reconstruction covers source text once and preserves every answer and original index', () => {
  assert.ok(data.items.filter(i => i.layout).length >= 160)
  for (const item of data.items) {
    const ranges = (item.layout || [{type:'text',start:0,end:item.text.length}]).flatMap(block => block.type === 'table'
      ? block.rows.flatMap(row => row.flatMap(cell => cell.ranges))
      : numericProseRanges(item,block.start,block.end))
    const covered = ranges.flatMap(([start,end]) => Array.from({length:end-start},(_,i)=>start+i)).sort((a,b)=>a-b)
    assert.deepEqual(covered,Array.from({length:item.text.length},(_,i)=>i),item.id)
    const blanks = ranges.flatMap(([start,end]) => numericRangeParts(item,start,end)).filter(part => part.index !== undefined)
    assert.deepEqual(blanks.map(part=>part.index).sort((a,b)=>a-b),item.blanks.map((_,i)=>i),item.id)
    for (const part of blanks) assert.equal(part.answer,item.blanks[part.index].answer)
  }
})

test('thyroid comparison table restores disease, manifestations, notes and treatment columns', () => {
  const item = data.items.find(i=>i.id==='numeric-95321d465c2abc')
  const table = item.layout.find(block=>block.type==='table')
  assert.equal(table.columns,7)
  assert.equal(table.headerIncluded,true)
  const rows = table.rows.map(row=>row.map(cell=>cell.ranges.map(([a,b])=>item.text.slice(a,b)).join('').replace(/\s+/g,'')))
  const subacute = rows.find(row=>row[0]==='亚甲炎')
  assert.deepEqual(subacute.slice(1,5),['√','√','√',''])
  assert.match(subacute[5],/1-3周前驱感染.*BMR\/T3\/T4↑/)
  assert.equal(subacute[6],'NSAIDs或激素')
  const hashimoto = rows.find(row=>row[0]==='桥本')
  assert.equal(hashimoto[4],'√')
  assert.match(hashimoto[5],/甲减、TPOAb/)
  assert.equal(hashimoto[6],'甲状腺素')
})

test('surgery cases retain operation-specific conditions rather than collapsing contradictory margins', () => {
  const colorectal = data.items.filter(i => i.chapter === '大肠癌')
  assert.ok(colorectal.some(i => /肿瘤远端距切缘≥10cm/.test(i.text)))
  assert.ok(colorectal.some(i => /未受累.*Dixon 术，切缘≥1cm/s.test(i.text)))
  assert.ok(colorectal.some(i => /距肛缘≥7.*Dixon 术（切缘≥2cm）/s.test(i.text)))
  assert.ok(data.items.some(i => /T 管造影.*胆道无结石残留→术后 4 周拔管/s.test(i.text)))
  assert.ok(data.reviewNotes.some(n => n.page === 2 && /疑义/.test(n.issue)))
  assert.ok(!data.items.some(i => /术后 1\.4 天|术后 2\.7 天/.test(i.text)))
})

test('search, subject, chapter, category, favorites and wrong-answer filters compose', () => {
  const item = data.items.find(i => i.chapter === '大肠癌' && i.category === '手术范围')
  const options = { subject: 'surgery', chapter: 'surgery:大肠癌', category: '手术范围', query: '切缘', records: { [item.id]: { favorite: true, result: 'wrong' } } }
  assert.deepEqual(filterNumericItems(data.items, { ...options, filter: 'favorites' }).map(i => i.id), [item.id])
  assert.deepEqual(filterNumericItems(data.items, { ...options, filter: 'wrong' }).map(i => i.id), [item.id])
  assert.ok(!filterNumericItems(data.items, { ...options, filter: 'new' }).some(i => i.id === item.id))
  assert.equal(filterNumericItems(data.items, { ...options, subject: 'med' }).length, 0)
})

test('numeric view preserves old mnemonic links and clears only incompatible route state', () => {
  assert.equal(new URL(studyViewUrl('https://example.com/?view=mnemonics&memory=numbers&q=test', 'numbers')).search, '?view=numbers')
  assert.equal(new URL(studyViewUrl('https://example.com/?view=mnemonics&memory=numbers', 'mnemonics')).searchParams.get('memory'), 'numbers')
})

test('reviewed numeric additions cover energies, ratios, short facts, negative values and scientific powers', () => {
  const answers = text => data.items.filter(i=>i.text.includes(text)).flatMap(i=>i.blanks.map(b=>b.answer.replace(/\s/g,'')))
  for(const answer of ['360','120-200']) assert.ok(answers('除颤').includes(answer),answer)
  assert.ok(answers('30:2').includes('30:2'))
  assert.ok(answers('多见于＜10 岁').includes('10'))
  assert.ok(answers('BE').includes('-2.3'))
  assert.ok(answers('CR 后体内白血病细胞').includes('10^10-10^12'))
  assert.ok(answers('CR 后体内白血病细胞').includes('10^8-10^9'))
  const anesthesia=data.items.find(i=>i.text.includes('一次限量小结 mg'))
  for(const answer of ['100','400','40','80','150','1000']) assert.ok(anesthesia.blanks.some(b=>b.answer===answer),answer)
  for(const i of data.items) for(const hint of i.hints || []) assert.ok(!i.blanks.some(b=>b.start<hint.end&&b.end>hint.start),i.id)
  assert.ok(data.items.filter(i=>i.reviewedImage).length>=7)
  assert.ok(numericAnswerCorrect('10¹⁰–10¹²','10^10-10^12'))
  assert.ok(numericAnswerCorrect('C5-C6','C5-6'))
  assert.ok(numericAnswerCorrect('30：2','30/2'))
  assert.ok(numericAnswerCorrect('−2.30','-2.3'))
})

test('saved attempts migrate across multiple answer revisions without reassigning values to other blanks', () => {
  const item={id:'test',blanks:[{answer:'2'},{answer:'1'}],answerRevision:3,answerMigrations:[{fromRevision:1,toRevision:2,indices:[-1,0,1]},{fromRevision:2,toRevision:3,indices:[2,1]}]}
  const saved={test:{values:['1','2'],submitted:true,result:'correct',favorite:true},other:{favorite:true}}
  const result=migrateNumericRecords(saved,[item])
  assert.deepEqual(result.test,{values:['2','1'],submitted:true,result:'correct',favorite:true,answerRevision:3})
  assert.deepEqual(saved.test.values,['1','2'])
  assert.equal(result.other,saved.other)
  assert.equal(migrateNumericRecords(result,[item]),result)
  const added={...item,blanks:[{answer:'2'},{answer:'3'}],answerRevision:2,answerMigrations:[{fromRevision:1,toRevision:2,indices:[1,-1]}]}
  const migrated=migrateNumericRecords(saved,[added]).test
  assert.deepEqual(migrated.values,['2',''])
  assert.equal(migrated.submitted,false)
  assert.equal(migrated.result,null)
  assert.equal(migrated.favorite,true)
  const wrong=migrateNumericRecords({test:{...saved.test,result:'wrong'}},[added]).test
  assert.equal(wrong.result,'wrong')
})

test('search highlighting spans a number blank and its following unit using source offsets', () => {
  const text='术后6-8周复查，另有16-8周'
  const hits=numericSearchRanges(text,'6–8周')
  assert.deepEqual(hits,[[2,6]])
  assert.deepEqual(numericHighlightParts(text,2,5,hits),[{text:'6-8',match:true}])
  assert.deepEqual(numericHighlightParts(text,5,text.length,hits),[{text:'周',match:true},{text:'复查，另有16-8周',match:false}])
})

test('biliary comparison restores merged disease labels and removes phantom columns', () => {
  const item=data.items.find(i=>i.id==='numeric-786c4ebb90a7a4')
  const tables=item.layout.filter(b=>b.type==='table')
  assert.equal(tables.length,2)
  for(const table of tables)assert.equal(table.columns,5)
  const rows=tables.flatMap(t=>t.rows).map(row=>row.map(cell=>cell.ranges.map(([a,b])=>item.text.slice(a,b)).join('').replace(/\s/g,'')))
  assert.ok(rows.some(row=>row[0]==='肝内胆管结石及炎症'&&row[1]==='多×'))
  assert.ok(rows.some(row=>row[0]==='胆管闭锁'&&row[1]==='√且持续性'))
  assert.ok(rows.some(row=>row[0]==='先天性胆管扩张症'&&row[1]==='√且间歇性'))
  assert.ok(rows.some(row=>row[0]==='十二指肠癌'&&row[1].includes('晚、慢、浅')))
})
