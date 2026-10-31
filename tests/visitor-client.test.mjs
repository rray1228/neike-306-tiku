import test from 'node:test'
import assert from 'node:assert/strict'
import { createVisitorCounter, readVisitorCounts, VISITOR_API, VISITOR_SITE } from '../src/visitor-counts.js'

const response = (today = 3, total = 9) => Response.json({ busuanzi_today_uv: today, busuanzi_site_uv: total })

test('both publications use one independent counter without sending query strings, referrers or visitor IDs', async () => {
  let calls = 0
  const count = createVisitorCounter(async (url, options) => {
    calls++
    assert.equal(url, VISITOR_API)
    assert.ok(!url.includes('chatgpt.site'))
    assert.deepEqual(JSON.parse(options.body), { url: VISITOR_SITE, referrer: '' })
    assert.equal(options.credentials, 'omit')
    assert.equal(options.referrerPolicy, 'no-referrer')
    assert.equal(options.headers['Content-Type'], 'text/plain;charset=UTF-8')
    return response()
  })
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
  for (const value of [null, { busuanzi_today_uv: '3', busuanzi_site_uv: 9 }, { busuanzi_today_uv: -1, busuanzi_site_uv: 9 }, { busuanzi_today_uv: 10, busuanzi_site_uv: 9 }]) {
    assert.throws(() => readVisitorCounts(value))
  }
})

test('statistics refresh after the short cache and reset on the Shanghai calendar day', async () => {
  let now = Date.parse('2026-10-31T15:59:50Z'), calls = 0
  const count = createVisitorCounter(async () => response(++calls, 10), () => now)
  assert.equal((await count()).todayVisitors, 1)
  now += 5_000
  assert.equal((await count()).todayVisitors, 1)
  now += 5_000
  assert.equal((await count()).todayVisitors, 2, 'a new day bypasses the cache')
  now += 61_000
  assert.equal((await count()).todayVisitors, 3)
})
