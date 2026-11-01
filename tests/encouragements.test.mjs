import test from 'node:test'
import assert from 'node:assert/strict'
import { drawEncouragement, encouragements } from '../src/encouragements.js'

test('fifty new learning quotations and reviewed existing quotations include sources', () => {
  assert.equal(encouragements.filter(q => q.id.startsWith('plain-learning-20261101-')).length, 50)
  assert.ok(encouragements.every(q => q.learningRelevant))
  assert.ok(!encouragements.some(q => q.id === 'quote-165'))
  assert.ok(!encouragements.some(q => q.id.startsWith('learning-20261101-')))
  assert.ok(!encouragements.some(q => /君子|不可以已|锲而|弗措|博学之/.test(q.text)))
  assert.equal(new Set(encouragements.map(quote => quote.id)).size, encouragements.length)
  assert.equal(new Set(encouragements.map(quote => quote.text)).size, encouragements.length)
  for (const quote of encouragements) {
    assert.ok(quote.author && quote.work && quote.text)
    assert.equal(new URL(quote.url).protocol, 'https:')
  }
})

test('each reader gets a shuffled deck with no repeats across a whole round', () => {
  const messages = []
  let raw = null
  for (let i = 0; i < encouragements.length; i++) {
    const drawn = drawEncouragement(raw)
    messages.push(drawn.message)
    raw = JSON.stringify(drawn.state)
  }
  assert.equal(new Set(messages).size, encouragements.length)
  assert.notEqual(drawEncouragement(raw).message, messages.at(-1))
  assert.notEqual(drawEncouragement(null, () => 0).message, drawEncouragement(null, () => 0.999).message)
})

test('reload continues the saved deck; invalid saved decks recover safely', () => {
  const first = drawEncouragement(null, () => 0)
  const next = drawEncouragement(JSON.stringify(first.state), () => { throw Error('must not reshuffle a saved deck') })
  assert.notEqual(first.message, next.message)
  for (const raw of ['broken', '{}', '{"version":2,"remaining":[-1]}', '{"version":2,"remaining":[0,0]}']) {
    const drawn = drawEncouragement(raw)
    assert.ok(encouragements.some(quote => quote.text === drawn.message))
  }
})

test('a new round never repeats the preceding last message even with the same shuffle', () => {
  const first = drawEncouragement(null, () => 0)
  const empty = JSON.stringify({ ...first.state, remaining: [] })
  assert.notEqual(drawEncouragement(empty, () => 0).message, first.message)
})

test('old or changed catalogs reset safely, and notices retain quotation attribution', () => {
  const drawn = drawEncouragement('{"version":2,"remaining":[0,1],"last":2}')
  assert.equal(drawn.quote.text, drawn.message)
  assert.equal(drawn.state.remaining.length, encouragements.length - 1)
  const changed = drawEncouragement(JSON.stringify({ ...drawn.state, catalog: 'old-catalog' }))
  assert.equal(changed.state.remaining.length, encouragements.length - 1)
  assert.notEqual(changed.quote.id, drawn.quote.id)
})
