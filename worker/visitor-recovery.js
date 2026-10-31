const LEGACY_API = 'https://cdn.busuanzi.cc/api.php'
const SITE = 'https://rray1228.github.io/neike-306-tiku/'

// An alternate network path for recovering the original public aggregates.
// The target and site key are fixed; this is not an arbitrary fetch proxy.
export async function recoverVisitorSnapshot(request, db, fetcher = fetch, now = new Date()) {
  const headers = { 'Cache-Control': 'no-store' }
  if (request.method !== 'GET') return new Response('Method not allowed', { status: 405, headers: { ...headers, Allow: 'GET' } })
  if (!db) return Response.json({ error: 'Recovery storage unavailable' }, { status: 503, headers })
  await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_snapshots (source TEXT PRIMARY KEY, captured_at TEXT NOT NULL, day TEXT NOT NULL, today_visitors INTEGER NOT NULL, total_visitors INTEGER NOT NULL)').run()
  const cached = await db.prepare('SELECT * FROM visitor_recovery_snapshots WHERE source = ?').bind(LEGACY_API).first()
  if (cached) return Response.json({ source: LEGACY_API, capturedAt: cached.captured_at, day: cached.day, todayVisitors: cached.today_visitors, totalVisitors: cached.total_visitors }, { headers })
  await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_attempts (source TEXT PRIMARY KEY, attempted_at INTEGER NOT NULL)').run()
  const attempt = await db.prepare('INSERT INTO visitor_recovery_attempts (source, attempted_at) VALUES (?, ?) ON CONFLICT (source) DO UPDATE SET attempted_at = excluded.attempted_at WHERE visitor_recovery_attempts.attempted_at < ?').bind(LEGACY_API, now.getTime(), now.getTime() - 600_000).run()
  if (!attempt.meta?.changes) return Response.json({ error: 'A recovery request was already attempted recently', recovered: false }, { status: 429, headers })
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 12_000)
  try {
    const response = await fetcher(LEGACY_API, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body: JSON.stringify({ url: SITE, referrer: '' }), signal: controller.signal })
    if (!response.ok) throw new Error(`Original provider HTTP ${response.status}`)
    const value = await response.json()
    const todayVisitors = value?.busuanzi_today_uv, totalVisitors = value?.busuanzi_site_uv
    if (!Number.isSafeInteger(todayVisitors) || !Number.isSafeInteger(totalVisitors) || todayVisitors < 0 || totalVisitors < todayVisitors) throw new Error('Original provider returned no valid visitor counts')
    const day = new Date(now.getTime() + 8 * 3600000).toISOString().slice(0, 10)
    await db.prepare('INSERT OR IGNORE INTO visitor_recovery_snapshots (source, captured_at, day, today_visitors, total_visitors) VALUES (?, ?, ?, ?, ?)').bind(LEGACY_API, now.toISOString(), day, todayVisitors, totalVisitors).run()
    return Response.json({ source: LEGACY_API, capturedAt: now.toISOString(), day, todayVisitors, totalVisitors }, { headers })
  } catch (error) {
    return Response.json({ error: error?.name === 'AbortError' ? 'Original provider timed out from the server too' : String(error?.message || 'Recovery unavailable'), recovered: false }, { status: 502, headers })
  } finally { clearTimeout(timer) }
}
