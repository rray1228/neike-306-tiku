import test from 'node:test'
import assert from 'node:assert/strict'
import { DatabaseSync } from 'node:sqlite'
import { recoverVisitorSnapshot } from '../worker/visitor-recovery.js'

function database() {
  const sql = new DatabaseSync(':memory:')
  return { sql, prepare(query) { return { args: [], bind(...args) { this.args = args; return this }, async run() { return { meta: sql.prepare(query).run(...this.args) } }, async first() { return sql.prepare(query).get(...this.args) ?? null } } } }
}
const request = () => new Request('https://example.test/api/visitor-recovery?url=https://unrelated.example/')
const now = new Date('2026-10-31T08:00:00Z')

test('recovery only requests the fixed old provider and persists one verified aggregate', async () => {
  const db = database(); let calls = 0
  db.sql.exec('CREATE TABLE site_visitors (visitor_id TEXT); INSERT INTO site_visitors VALUES (\'preserved\')')
  const fetcher = async (url, options) => {
    calls++
    assert.equal(url, 'https://cdn.busuanzi.cc/api.php')
    assert.deepEqual(JSON.parse(options.body), { url: 'https://rray1228.github.io/neike-306-tiku/', referrer: '' })
    return Response.json({ busuanzi_today_uv: 7, busuanzi_site_uv: 11 })
  }
  const first = await (await recoverVisitorSnapshot(request(), db, fetcher, now)).json()
  assert.equal(first.todayVisitors, 7); assert.equal(first.totalVisitors, 11)
  assert.equal(first.day, '2026-10-31'); assert.equal(first.capturedAt, now.toISOString())
  assert.deepEqual(await (await recoverVisitorSnapshot(request(), db, fetcher, now)).json(), first)
  assert.equal(calls, 1)
  assert.equal(db.sql.prepare('SELECT COUNT(*) AS count FROM site_visitors').get().count, 1)
})

test('failed recovery saves no guessed count and retries are rate limited across requests', async () => {
  const db = database(); let calls = 0
  const invalid = async () => { calls++; return Response.json({ error: 'outage' }) }
  const failed = await recoverVisitorSnapshot(request(), db, invalid, now)
  assert.equal(failed.status, 502); assert.equal((await failed.json()).recovered, false)
  assert.equal(db.sql.prepare('SELECT COUNT(*) AS count FROM visitor_recovery_snapshots').get().count, 0)
  assert.equal((await recoverVisitorSnapshot(request(), db, invalid, now)).status, 429)
  assert.equal(calls, 1)
  const retry = await recoverVisitorSnapshot(request(), db, async () => Response.json({ busuanzi_today_uv: 7, busuanzi_site_uv: 11 }), new Date(now.getTime() + 600_001))
  assert.equal(retry.status, 200)
  assert.equal((await retry.json()).totalVisitors, 11)
})
