import { memoryTextMatches } from './mnemonic-search.js'

export const NUMERIC_SUBJECTS = { surgery: '外科', med: '内科' }

// Normalize typography, never discard inequality signs or reorder range ends.
export function normalizeNumericAnswer(value) {
  return String(value).normalize('NFKC').trim().replace(/\s+/g, '')
    .replace(/[～~—–－至到]/g, '-').replace(/^(\d+)\.0+(?=$|-)/g, '$1')
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
  item.blanks.forEach((blank, index) => {
    if (blank.start < start || blank.end > end) return
    if (cursor < blank.start) parts.push({ text: item.text.slice(cursor, blank.start) })
    parts.push({ ...blank, index })
    cursor = blank.end
  })
  if (cursor < end) parts.push({ text: item.text.slice(cursor, end) })
  return parts
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
