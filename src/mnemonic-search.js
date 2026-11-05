export const MNEMONIC_SUBJECTS = { med: '内科', surgery: '外科', pathology: '病理', physiology: '生理', biochemistry: '生化' }

// NFKC also makes full-width letters, numbers and subscripts searchable.
export function normalizeMnemonicText(text = '') {
  return text.normalize('NFKC').toLowerCase().replace(/[\s\p{P}\p{S}]+/gu, '')
}

export const blockText = (block) => block.parts.map(part => part.text).join('').trim()
const mathText = text => text.normalize('NFKC').toLowerCase().replace(/×/g, '*').replace(/÷/g, '/').replace(/\s+/g, '')
const mathTerms = query => [...query.normalize('NFKC').matchAll(/\d+(?:\.\d+)?(?:\s*[+×*÷/=]\s*\d+(?:\.\d+)?)+/g)].map(match => mathText(match[0]))
const hasMathTerm = (text, term) => {
  let at = text.indexOf(term)
  while (at >= 0) {
    if (!/[\d.]/.test(text[at - 1] || '') && !/[\d.]/.test(text[at + term.length] || '')) return true
    at = text.indexOf(term, at + 1)
  }
  return false
}

export const queryWords = (query) => query.trim().split(/\s+/u).map(normalizeMnemonicText).filter(Boolean)
export const normalizeMemorySearchText = text => text.normalize('NFKC').toLowerCase().replace(/[–—～~－]/g, '-').replace(/\s+/g, '')
export const memoryQueryWords = query => query.normalize('NFKC').replace(/(\d)\s*[-–—～~－]\s*(?=\d)/g, '$1-').trim().split(/\s+/u).filter(Boolean)
const rangeTerms = query => [...query.normalize('NFKC').matchAll(/\d+(?:\.\d+)?\s*[-–—～~－]\s*\d+(?:\.\d+)?/g)].map(match => normalizeMemorySearchText(match[0]))
export function memoryTextMatches(text, query) {
  const normalized = normalizeMemorySearchText(text)
  return memoryQueryWords(query).every(word => {
    const token = normalizeMemorySearchText(word)
    return rangeTerms(word).length ? hasMathTerm(normalized, token) : normalized.includes(token)
  })
}

export function indexMnemonics(items) {
  return items.map(item => ({ ...item,
    mathTitle: mathText([item.title, ...(item.aliases || [])].join('；')),
    mathBody: mathText([item.scope || '', ...item.blocks.map(blockText)].join('；')),
    searchTitle: normalizeMnemonicText([item.title, ...(item.aliases || [])].join(' ')),
    searchContext: normalizeMnemonicText((item.locations || [item]).flatMap(location => [MNEMONIC_SUBJECTS[location.subject], location.chapter, location.section]).join(' ')),
    searchBody: normalizeMnemonicText([item.scope || '', ...item.blocks.map(blockText)].join(' ')),
  }))
}

export function searchMnemonics(items, { query = '', subject = 'all', chapter = '', favoritesOnly = false, favorites = [], matchMode = 'auto' } = {}) {
  const words = queryWords(query)
  const formulas = mathTerms(query)
  const ranges = rangeTerms(query)
  const favoriteIds = new Set(favorites)
  const matches = []
  for (const item of items) {
    const locations = (item.locations || [item]).filter(location => (subject === 'all' || location.subject === subject) && (!chapter || `${location.subject}:${location.chapter}` === chapter))
    if (!locations.length) continue
    if (favoritesOnly && !favoriteIds.has(item.id) && !(item.alternateIds || []).some(id => favoriteIds.has(id))) continue
    const combined = matchMode === 'title' ? item.searchTitle : matchMode === 'knowledge' ? item.searchContext + item.searchBody : item.searchTitle + item.searchContext + item.searchBody
    if (!words.every(word => combined.includes(word))) continue
    if (ranges.length) {
      const text = matchMode === 'title' ? item.mathTitle : matchMode === 'knowledge' ? item.mathBody : item.mathTitle + ' ' + item.mathBody
      if (!ranges.every(term => hasMathTerm(normalizeMemorySearchText(text), term))) continue
    }
    if (formulas.length) {
      const math = matchMode === 'title' ? item.mathTitle : matchMode === 'knowledge' ? item.mathBody : item.mathTitle + ' ' + item.mathBody
      if (!formulas.every(term => hasMathTerm(math, term))) continue
    }
    const score = words.reduce((total, word) => total + (item.searchTitle === word ? 100 : item.searchTitle.includes(word) ? 40 : item.searchContext.includes(word) ? 10 : 1), 0)
    const located = (subject !== 'all' || chapter) ? { ...item, ...locations[0] } : item
    matches.push({ item: located, score, titleMatch: words.length > 0 && words.every(word => item.searchTitle.includes(word)) })
  }
  if (matchMode === 'auto' && matches.some(match => match.titleMatch)) return matches.filter(match => match.titleMatch).sort((a, b) => b.score - a.score).map(match => match.item)
  if (words.length) matches.sort((a, b) => b.score - a.score)
  return matches.map(match => match.item)
}

export function previewBlocks(item, query) {
  const words = queryWords(query)
  let noteCount = 0
  return item.blocks.filter(block => {
    // A mnemonic is one complete decoding, regardless of how many rows it has.
    if (block.kind === 'mapping') return true
    const leadingNote = noteCount++ < 2
    return leadingNote || words.some(word => normalizeMnemonicText(blockText(block)).includes(word))
  })
}

export function highlightParts(text, query) {
  const targets = memoryQueryWords(query).map(word => ({ word, range: rangeTerms(word).length > 0 }))
  if (!targets.length) return [{ text, match: false }]
  const characters = Array.from(text)
  const marked = new Set()
  for (const { word, range } of targets) {
    const normalize = range ? normalizeMemorySearchText : normalizeMnemonicText
    const target = normalize(word)
    if (!target) continue
    let normalized = ''
    const positions = []
    characters.forEach((character,index) => {
      const part = normalize(character)
      normalized += part
      for (let offset=0;offset<part.length;offset++) positions.push(index)
    })
    let from = 0
    while (from < normalized.length) {
      const at = normalized.indexOf(target, from)
      if (at < 0) break
      if (range && ((/^\d/.test(target) && /[\d.]/.test(normalized[at-1] || '')) || (/\d$/.test(target) && /[\d.]/.test(normalized[at+target.length] || '')))) { from = at + target.length; continue }
      for (let i = positions[at]; i <= positions[at + target.length - 1]; i++) marked.add(i)
      from = at + target.length
    }
  }
  const parts = []
  characters.forEach((character, index) => {
    const match = marked.has(index)
    if (parts.length && parts.at(-1).match === match) parts.at(-1).text += character
    else parts.push({ text: character, match })
  })
  return parts
}


export function mnemonicDirectory(items) {
  return Object.entries(MNEMONIC_SUBJECTS).map(([subject, label]) => {
    const chapters = new Map()
    const subjectIds = new Set()
    for (const item of items) {
      const locations = (item.locations || [item]).filter(location => location.subject === subject)
      if (!locations.length) continue
      subjectIds.add(item.id)
      for (const location of locations) {
        const chapter = chapters.get(location.chapter) || { name: location.chapter, ids: new Set(), sections: new Set() }
        chapter.ids.add(item.id)
        if (location.section) chapter.sections.add(location.section)
        chapters.set(location.chapter, chapter)
      }
    }
    return { subject, label, count: subjectIds.size, chapters: [...chapters.values()].map(({ name, ids, sections }) => ({ name, count: ids.size, sections })) }
  })
}
