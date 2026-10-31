import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const data = JSON.parse(readFileSync(new URL('../src/data/politics-selftest-data.json', import.meta.url)))
const practice = JSON.parse(readFileSync(new URL('../src/data/politics-data.json', import.meta.url)))

test('all 17 original matching exercises retain their source pages, item counts and numbering', () => {
  const expected = [[15,11,10],[38,34,6],[49,45,10],[53,49,5],[81,78,10],[93,90,5],[98,95,6],[112,111,9],[124,123,8],[136,135,8],[150,149,8],[172,173,10],[185,186,6],[199,200,7],[211,213,10],[224,226,10],[234,236,8]]
  assert.deepEqual(data.groups.map(g => [g.pdfPage,g.page,g.stems.length]), expected)
  assert.equal(data.groups.flatMap(g=>g.stems).length,136)
  assert.equal(new Set([...data.groups,...practice.groups].map(g=>g.id)).size,24)
  for(const g of data.groups) {
    assert.equal(g.options.length,g.stems.length,g.id)
    assert.deepEqual(g.stems.map(s=>s.number),Array.from({length:g.stems.length},(_,i)=>i+1))
    assert.deepEqual(g.options.map(o=>o.key),Array.from({length:g.options.length},(_,i)=>String.fromCharCode(65+i)))
    assert.deepEqual(g.options.map(o=>o.sourceNumber),g.stems.map(s=>s.number))
    assert.ok(data.referenceImages[g.lectureEvidence.image]?.match(/^\/politics\/reference-pages\/[a-f0-9]{24}\.webp$/))
  }
})
test('all 136 answers agree with the independently reviewed PDF key and retain storage IDs', () => {
  const expected = new Map([
    [11,'BACDFEGIHJ'],[34,'BAECDF'],[45,'BACEDFIHGJ'],[49,'BAEDC'],
    [78,'DABCFEGHIJ'],[90,'DBAEC'],[95,'FDCBAE'],[111,'EFCGABDIH'],
    [123,'BCAHGFED'],[135,'DCHBFEGA'],[149,'AHDCGFEB'],[173,'BADCFEHIGJ'],
    [186,'CDBEAF'],[200,'DEGABFC'],[213,'BDCJEFHGIA'],[226,'CDABEGFIHJ'],[236,'BCADFEHG'],
  ])
  const answerPages = [1,3,4,5,6,7,7,8,9,10,11,12,13,14,15,16,17]
  assert.deepEqual(data.groups.map(g=>g.answerPdfPage),answerPages)
  for(const g of data.groups) {
    assert.equal(g.pendingAnswers,false)
    assert.ok(!g.answerRevision, 'Adding the first answer key must retain saved selections')
    assert.equal(g.stems.map(s=>s.answer[0]).join(''),expected.get(g.page),g.id)
    for(const [i,s] of g.stems.entries()) {
      assert.equal(s.id,`${g.id}-s${String(i+1).padStart(2,'0')}`)
      assert.equal(s.answer.length,1)
      const option=g.options.find(o=>o.key===s.answer[0])
      assert.equal(s.answerOriginalNumber,option.sourceNumber)
      assert.equal(s.answerState,'已按自测答案核对')
      assert.equal(s.answerPdfPage,g.answerPdfPage)
      assert.equal(s.answerDisplay,`${option.key} · ${option.label}`)
    }
  }
})
test('column continuations and OCR confusions preserve the visually reviewed source text', () => {
  const page=n=>data.groups.find(g=>g.pdfPage===n)
  assert.equal(page(15).options[0].label,'思维的物质外壳和现实形式')
  assert.equal(page(15).stems[5].text,'具体时空')
  assert.equal(page(38).options[0].label,'实现社会形态更替的重要手段和决定性环节')
  assert.equal(page(81).options[9].label,'没收官僚资本归新民主主义国家所有')
  assert.equal(page(185).options[5].label,'五卅运动')
  assert.equal(page(211).options[3].label,'摇篮、胎记、精神基因')
  assert.equal(page(234).options[1].label,'完备的法律规范体系')
})
