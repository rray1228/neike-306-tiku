const LEGACY_API = 'https://cdn.busuanzi.cc/api.php'
const SITE = 'https://rray1228.github.io/neike-306-tiku/'
const DASHBOARD = 'https://www.busuanzi.cc/count.php?search=rray1228.github.io'

async function recoverDashboard(db, fetcher, now) {
  await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_pages (source TEXT PRIMARY KEY, captured_at TEXT NOT NULL, status INTEGER NOT NULL, body TEXT NOT NULL)').run()
  const cached = await db.prepare('SELECT * FROM visitor_recovery_pages WHERE source = ?').bind(DASHBOARD).first()
  if (cached && now.getTime() - Date.parse(cached.captured_at) < 600_000) return Response.json(JSON.parse(cached.body), { headers: { 'Cache-Control': 'no-store' } })
  const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 12_000)
  let result
  try {
    const response = await fetcher(DASHBOARD, { signal: controller.signal })
    const html = (await response.text()).slice(0, 150_000)
    const text = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').slice(0, 25_000)
    result = { source: DASHBOARD, capturedAt: now.toISOString(), status: response.status, text, scriptSources: [...html.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)].map(value => value[1]) }
  } catch (error) { result = { source: DASHBOARD, capturedAt: now.toISOString(), status: 502, error: String(error?.message || 'Dashboard unavailable') } }
  finally { clearTimeout(timer) }
  await db.prepare('INSERT INTO visitor_recovery_pages (source, captured_at, status, body) VALUES (?, ?, ?, ?) ON CONFLICT (source) DO UPDATE SET captured_at = excluded.captured_at, status = excluded.status, body = excluded.body').bind(DASHBOARD, now.toISOString(), result.status, JSON.stringify(result)).run()
  return Response.json(result, { headers: { 'Cache-Control': 'no-store' } })
}

// An alternate network path for recovering the original public aggregates.
// The target and site key are fixed; this is not an arbitrary fetch proxy.
export async function recoverVisitorSnapshot(request, db, fetcher = fetch, now = new Date(), minimumTotal = 700) {
  const headers = { 'Cache-Control': 'no-store' }
  if (request.method !== 'GET') return new Response('Method not allowed', { status: 405, headers: { ...headers, Allow: 'GET' } })
  if (!db) return Response.json({ error: 'Recovery storage unavailable' }, { status: 503, headers })
  if (new URL(request.url).searchParams.get('source') === 'dashboard') return recoverDashboard(db, fetcher, now)
  await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_snapshots (source TEXT PRIMARY KEY, captured_at TEXT NOT NULL, day TEXT NOT NULL, today_visitors INTEGER NOT NULL, total_visitors INTEGER NOT NULL)').run()
  const cached = await db.prepare('SELECT * FROM visitor_recovery_snapshots WHERE source = ?').bind(LEGACY_API).first()
  if (cached && cached.total_visitors >= minimumTotal) return Response.json({ source: LEGACY_API, capturedAt: cached.captured_at, day: cached.day, todayVisitors: cached.today_visitors, totalVisitors: cached.total_visitors }, { headers })
  await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_attempts (source TEXT PRIMARY KEY, attempted_at INTEGER NOT NULL)').run()
  const attempt = await db.prepare('INSERT INTO visitor_recovery_attempts (source, attempted_at) VALUES (?, ?) ON CONFLICT (source) DO UPDATE SET attempted_at = excluded.attempted_at WHERE visitor_recovery_attempts.attempted_at < ?').bind(LEGACY_API, now.getTime(), now.getTime() - 600_000).run()
  if (!attempt.meta?.changes) return Response.json({ error: 'A recovery request was already attempted recently', recovered: false }, { status: 429, headers })
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 12_000)
  try {
    const response = await fetcher(LEGACY_API, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body: JSON.stringify({ url: SITE, referrer: '' }), signal: controller.signal })
    if (!response.ok) throw new Error(`Original provider HTTP ${response.status}`)
    const body = (await response.text()).slice(0, 50_000)
    await db.prepare('CREATE TABLE IF NOT EXISTS visitor_recovery_payloads (source TEXT PRIMARY KEY, captured_at TEXT NOT NULL, body TEXT NOT NULL)').run()
    await db.prepare('INSERT INTO visitor_recovery_payloads (source, captured_at, body) VALUES (?, ?, ?) ON CONFLICT (source) DO UPDATE SET captured_at = excluded.captured_at, body = excluded.body').bind(LEGACY_API, now.toISOString(), body).run()
    const value = JSON.parse(body)
    const integer = value => typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : value
    const todayVisitors = integer(value?.busuanzi_today_uv), totalVisitors = integer(value?.busuanzi_site_uv)
    if (!Number.isSafeInteger(todayVisitors) || !Number.isSafeInteger(totalVisitors) || todayVisitors < 0 || totalVisitors < todayVisitors) throw new Error('Original provider returned no valid visitor counts')
    // This lower bound is the user's recollection, not a fabricated count.
    // Preserve smaller responses for verification, but never call a reset restored.
    if (totalVisitors < minimumTotal) throw new Error('Original response is below the reported historical range; saved for verification, not accepted as restored')
    const serverDate = Date.parse(response.headers.get('Date') || '')
    const capturedAt = Number.isFinite(serverDate) ? new Date(serverDate) : now
    const day = new Date(capturedAt.getTime() + 8 * 3600000).toISOString().slice(0, 10)
    await db.prepare('INSERT INTO visitor_recovery_snapshots (source, captured_at, day, today_visitors, total_visitors) VALUES (?, ?, ?, ?, ?) ON CONFLICT (source) DO UPDATE SET captured_at = excluded.captured_at, day = excluded.day, today_visitors = excluded.today_visitors, total_visitors = excluded.total_visitors WHERE excluded.total_visitors > visitor_recovery_snapshots.total_visitors').bind(LEGACY_API, capturedAt.toISOString(), day, todayVisitors, totalVisitors).run()
    return Response.json({ source: LEGACY_API, capturedAt: capturedAt.toISOString(), day, todayVisitors, totalVisitors }, { headers })
  } catch (error) {
    return Response.json({ error: error?.name === 'AbortError' ? 'Original provider timed out from the server too' : String(error?.message || 'Recovery unavailable'), recovered: false }, { status: 502, headers })
  } finally { clearTimeout(timer) }
}
