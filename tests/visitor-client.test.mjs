import test from 'node:test'
import assert from 'node:assert/strict'
import { createVisitorCounter, readVisitorCounts, readVisitorCache, writeVisitorCache, visitorDay, visitorBucket, VISITOR_API, VISITOR_SITE, VISITOR_CACHE_KEY, VISITOR_IDENTITY_KEY, LEGACY_VISITOR_CACHE_KEY } from '../src/visitor-counts.js'

const response = (today = 3, total = 9, headers = {}) => Response.json({ success: true, data: { page_uv: today, site_uv: total, page_pv: 1000, site_pv: 2000 } }, { headers })

test('both publications share a daily bucket without sending actual query strings, referrers or practice data', async () => {
  let calls = 0
  const count = createVisitorCounter(async (url, options) => {
    calls++
    assert.equal(url, VISITOR_API)
    assert.ok(!url.includes('chatgpt.site'))
    assert.equal(options.body, undefined)
    assert.equal(options.credentials, 'omit')
    assert.equal(options.referrerPolicy, 'no-referrer')
    assert.deepEqual(options.headers, { 'x-bsz-referer': visitorBucket(Date.parse('2026-10-31T00:00:00Z')) })
    return response()
  }, () => Date.parse('2026-10-31T00:00:00Z'))
  const values = await Promise.all([count(), count(), count()])
  assert.equal(calls, 1, 'React remounts and concurrent readers do not send duplicate requests')
  assert.deepEqual(values, Array(3).fill({ todayVisitors: 3, totalVisitors: 9 }))
})

test('failed requests can recover; an invalid response never becomes a made-up count', async () => {
  let attempts = 0
  const count = createVisitorCounter(async () => {
    attempts++
    if (attempts === 1) throw new TypeError('Network unavailable')
    if (attempts === 2) return new Response('Blocked', { status: 403 })
    if (attempts === 3) return Response.json({ error: 'unavailable' })
    return response(4, 10)
  })
  for (let i = 0; i < 3; i++) await assert.rejects(count())
  assert.deepEqual(await count(), { todayVisitors: 4, totalVisitors: 10 })
  for (const value of [null, { success: false, data: { page_uv: 3, site_uv: 9 } }, ...['3', -1, 10].map(page_uv => ({ success: true, data: { page_uv, site_uv: 9 } })), { busuanzi_today_uv: 3, busuanzi_site_uv: 9 }]) {
    assert.throws(() => readVisitorCounts(value))
  }
})

test('statistics refresh after the short cache and reset on the Shanghai calendar day', async () => {
  let now = Date.parse('2026-10-31T15:59:50Z'), calls = 0
  const buckets = []
  const count = createVisitorCounter(async (_url, options) => { buckets.push(options.headers['x-bsz-referer']); return response(++calls, 10) }, () => now)
  assert.equal((await count()).todayVisitors, 1)
  now += 5_000
  assert.equal((await count()).todayVisitors, 1)
  now += 5_000
  assert.equal((await count()).todayVisitors, 2, 'a new day bypasses the cache')
  now += 61_000
  assert.equal((await count()).todayVisitors, 3)
  assert.deepEqual(buckets, [`${VISITOR_SITE}__visitor_day__/2026-10-31`, `${VISITOR_SITE}__visitor_day__/2026-11-01`, `${VISITOR_SITE}__visitor_day__/2026-11-01`])
})

test('server-issued visitor identity survives reloads and is only accepted with a valid service response', async () => {
  const values = new Map(), storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) }
  const calls = []
  const fetcher = async (_url, options) => { calls.push(options.headers); return response(3, 9, { 'Set-Bsz-Identity': 'server-signed.identity' }) }
  await createVisitorCounter(fetcher, Date.now, storage)()
  assert.equal(values.get(VISITOR_IDENTITY_KEY), 'server-signed.identity')
  await createVisitorCounter(fetcher, Date.now, storage)()
  assert.equal(calls[1].Authorization, 'Bearer server-signed.identity')
  const failed = createVisitorCounter(async () => Response.json({ success: false }, { headers: { 'Set-Bsz-Identity': 'invalid-response.identity' } }), Date.now, storage)
  await assert.rejects(failed())
  assert.equal(values.get(VISITOR_IDENTITY_KEY), 'server-signed.identity')
})

test('a request crossing Shanghai midnight cannot label yesterday’s bucket as today', async () => {
  let now = Date.parse('2026-10-31T15:59:59Z')
  const count = createVisitorCounter(async () => { now += 2000; return response() }, () => now)
  await assert.rejects(count(), /date changed/)
  assert.deepEqual(await count(), { todayVisitors: 3, totalVisitors: 9 })
})

test('the persistent display cache survives a reload without inventing visits', () => {
  const values = new Map(), storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) }
  const now = Date.parse('2026-10-31T15:59:50Z'), counts = { todayVisitors: 3, totalVisitors: 9 }
  assert.equal(readVisitorCache(storage, now), null)
  writeVisitorCache(counts, storage, now)
  assert.deepEqual(readVisitorCache(storage, now + 1_000), { ...counts, updatedAt: now })
  const tomorrow = now + 20_000, cached = readVisitorCache(storage, tomorrow)
  assert.equal(cached.totalVisitors, 9)
  assert.notEqual(visitorDay(cached.updatedAt), visitorDay(tomorrow), 'yesterday’s daily value must not be shown as today’s count')
  assert.equal(readVisitorCache(storage, now - 1), null, 'ignore future timestamps')
  assert.equal(readVisitorCache(storage, now + 8 * 24 * 60 * 60 * 1000), null, 'expire old display values')
  values.set(VISITOR_CACHE_KEY, JSON.stringify({ site: 'another-site', ...counts, updatedAt: now }))
  assert.equal(readVisitorCache(storage, now), null)
  values.set(VISITOR_CACHE_KEY, JSON.stringify({ site: VISITOR_SITE, todayVisitors: 3, totalVisitors: -1, updatedAt: now }))
  assert.equal(readVisitorCache(storage, now), null)
  values.set(VISITOR_CACHE_KEY, 'broken')
  assert.equal(readVisitorCache(storage, now), null)
  assert.equal(readVisitorCache({ getItem() { throw new Error('blocked') } }, now), null)
  assert.doesNotThrow(() => writeVisitorCache(counts, { setItem() { throw new Error('blocked') } }, now))
})

test('old provider snapshots can be read independently and are never overwritten by the replacement counter', () => {
  const now = Date.now(), values = new Map(), storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) }
  const original = JSON.stringify({ site: VISITOR_SITE, todayVisitors: 12, totalVisitors: 34, updatedAt: now })
  storage.setItem(LEGACY_VISITOR_CACHE_KEY, original)
  writeVisitorCache({ todayVisitors: 1, totalVisitors: 1 }, storage, now)
  assert.equal(readVisitorCache(storage, now).totalVisitors, 1)
  assert.equal(readVisitorCache(storage, now, LEGACY_VISITOR_CACHE_KEY).totalVisitors, 34)
  assert.equal(storage.getItem(LEGACY_VISITOR_CACHE_KEY), original)
  assert.equal(readVisitorCache(storage, now + 30 * 86400000, LEGACY_VISITOR_CACHE_KEY).totalVisitors, 34, 'historical evidence is not discarded by the live-cache expiration')
})
