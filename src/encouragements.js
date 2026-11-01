import quotes from './data/encouragement-quotes.json' with { type: 'json' }

const learningQuotes = quotes.filter(quote => quote.learningRelevant === true)
export const encouragements = learningQuotes
const byId = new Map(learningQuotes.map(quote => [quote.id, quote]))
const catalog = learningQuotes.map(quote => quote.id).join('|')

// Each browser retains its own shuffled deck. Every quotation is drawn once per
// round; a new round cannot begin with the preceding round's last quotation.
export function drawEncouragement(raw, random = Math.random) {
  let saved
  try { saved = JSON.parse(raw) } catch { /* Start a fresh deck. */ }
  const valid = saved?.version === 3 && saved.catalog === catalog && Array.isArray(saved.remaining)
    && saved.remaining.every(id => byId.has(id))
    && new Set(saved.remaining).size === saved.remaining.length
  let remaining = valid ? [...saved.remaining] : []
  const last = byId.has(saved?.last) ? saved.last : null
  if (!remaining.length) {
    remaining = learningQuotes.map(quote => quote.id)
    for (let i = remaining.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1))
      ;[remaining[i], remaining[j]] = [remaining[j], remaining[i]]
    }
    if (remaining.at(-1) === last) [remaining[0], remaining[remaining.length - 1]] = [remaining.at(-1), remaining[0]]
  }
  const id = remaining.pop()
  const quote = byId.get(id)
  return { message: quote.text, quote, state: { version: 3, catalog, remaining, last: id } }
}
