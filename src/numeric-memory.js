import { memoryTextMatches, highlightParts } from './mnemonic-search.js'

export function numericSearchRanges(text, query) {
  let offset=0
  return highlightParts(text,query).flatMap(part=>{
    const start=offset;offset+=part.text.length
    return part.match ? [[start,offset]] : []
  })
}

export function numericHighlightParts(text, start, end, hits) {
  let cursor=start
  const parts=[]
  for(const [a,b] of hits) {
    const low=Math.max(a,start),high=Math.min(b,end)
    if(low>=high)continue
    if(cursor<low)parts.push({text:text.slice(cursor,low),match:false})
    parts.push({text:text.slice(low,high),match:true});cursor=high
  }
  if(cursor<end)parts.push({text:text.slice(cursor,end),match:false})
  return parts
}

export const NUMERIC_SUBJECTS = { surgery: '外科', med: '内科' }

// Normalize typography, never discard inequality signs or reorder range ends.
export function normalizeNumericAnswer(value) {
  const superscripts='⁰¹²³⁴⁵⁶⁷⁸⁹'
  return String(value).replace(/10([⁰¹²³⁴⁵⁶⁷⁸⁹]+)/g,(_,digits)=>'10^'+Array.from(digits,c=>superscripts.indexOf(c)).join('')).normalize('NFKC').trim().replace(/\s+/g, '').toUpperCase()
    .replace(/[～~—–－−至到]/g, '-').replace(/^(\d+)\.0+(?=$|-)/g, '$1')
    .replace(/:/g,'/').replace(/([CTLS])(\d+)-\1(\d+)/g,'$1$2-$3')
}

export function numericAnswerCorrect(value, answer) {
  const normalize = text => normalizeNumericAnswer(text).split('-').map(part => /^\d+(?:\.\d+)?$/.test(part) ? String(Number(part)) : part).join('-')
  return normalize(value) !== '' && normalize(value) === normalize(answer)
}

export function numericParts(item) {
  const parts = []
  let offset = 0
  item.blanks.forEach((blank, index) => {
    parts.push({ text: item.text.slice(offset, blank.start) })
    parts.push({ ...blank, index })
    offset = blank.end
  })
  parts.push({ text: item.text.slice(offset) })
  return parts
}

export function numericRows(item) {
  const rows = [[]]
  for (const part of numericParts(item)) {
    if (part.index !== undefined) { rows.at(-1).push(part); continue }
    part.text.split('\n').forEach((text, index) => {
      if (index) rows.push([])
      rows.at(-1).push({ text })
    })
  }
  return rows
}

export function numericRangeParts(item, start, end) {
  const parts = []
  let cursor = start
  const events=[...item.blanks.map((blank,index)=>({...blank,index})).filter(blank=>blank.start>=start&&blank.end<=end),
    ...(item.hints || []).filter(hint=>hint.start<end&&hint.end>start).map(hint=>({start:Math.max(start,hint.start),end:Math.min(end,hint.end),hint:true}))].sort((a,b)=>a.start-b.start)
  for(const event of events) {
    if(cursor<event.start)parts.push({text:item.text.slice(cursor,event.start),start:cursor,end:event.start})
    parts.push(event.hint ? {...event,text:item.text.slice(event.start,event.end)} : event)
    cursor=event.end
  }
  if (cursor < end) parts.push({ text: item.text.slice(cursor, end), start:cursor, end })
  return parts
}

export function migrateNumericRecords(records, items) {
  let result=records
  for(const item of items) {
    const record=result[item.id]
    if(!record)continue
    let revision=record.answerRevision || 1
    let values=record.values || []
    let changed=false
    for(const migration of item.answerMigrations || []) {
      if(revision!==migration.fromRevision)continue
      values=migration.indices.map(index=>index<0?'':values[index] || '')
      revision=migration.toRevision
      changed=true
    }
    if(changed) {
      const submitted=Boolean(record.submitted)&&values.length===item.blanks.length&&values.every(value=>value.trim())
      const answerResult=submitted ? (item.blanks.every((blank,index)=>numericAnswerCorrect(values[index],blank.answer))?'correct':'wrong') : record.result==='wrong'?'wrong':null
      if(result===records)result={...records}
      result[item.id]={...record,values,submitted,result:answerResult,answerRevision:revision}
    }
  }
  return result
}

export function numericProseRanges(item, start, end) {
  const ranges = []
  const pattern = /\n(?=[①-⑳]|（(?:\d+|[一二三四五六七八九十]+)）|小结|常考|注意|[一二三四五六七八九十]+[、．])/g
  const text = item.text.slice(start, end)
  let cursor = start
  for (const match of text.matchAll(pattern)) {
    const boundary = start + match.index + 1
    ranges.push([cursor, boundary]); cursor = boundary
  }
  if (cursor < end) ranges.push([cursor, end])
  return ranges
}

export function filterNumericItems(items, { subject = 'all', chapter = '', category = '', query = '', filter = 'all', records = {} } = {}) {
  return items.filter(item => (subject === 'all' || item.subject === subject)
    && (!chapter || `${item.subject}:${item.chapter}` === chapter)
    && (!category || item.category === category)
    && memoryTextMatches(`${item.chapter} ${item.section} ${item.text} ${item.category}`, query)
    && (filter !== 'favorites' || records[item.id]?.favorite)
    && (filter !== 'wrong' || records[item.id]?.result === 'wrong')
    && (filter !== 'new' || !records[item.id]?.result))
}
