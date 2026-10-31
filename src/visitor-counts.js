// Both publications belong to one counter. Never send the reader's query,
// answers, browser identifier or referring page to the statistics service.
export const VISITOR_API = 'https://cdn.busuanzi.cc/api.php'
export const VISITOR_SITE = 'https://rray1228.github.io/neike-306-tiku/'
export const VISITOR_START = '2026-10-31'
export const VISITOR_CACHE_KEY = 'visitor-counts-v1'

export const visitorDay = time => new Date(time + 8 * 60 * 60 * 1000).toISOString().slice(0, 10)

export function readVisitorCounts(value) {
  const todayVisitors = value?.busuanzi_today_uv
  const totalVisitors = value?.busuanzi_site_uv
  if (!Number.isSafeInteger(todayVisitors) || !Number.isSafeInteger(totalVisitors)
    || todayVisitors < 0 || totalVisitors < todayVisitors) throw new Error('Invalid visitor statistics')
  return { todayVisitors, totalVisitors }
}

// Only retain actual service responses. This is a display cache, never a counter.
export function readVisitorCache(storage, now = Date.now()) {
  try {
    const value = JSON.parse(storage.getItem(VISITOR_CACHE_KEY))
    if (value?.site !== VISITOR_SITE || !Number.isFinite(value.updatedAt)
      || value.updatedAt > now || now - value.updatedAt > 7 * 24 * 60 * 60 * 1000) return null
    return { ...readVisitorCounts({ busuanzi_today_uv: value.todayVisitors, busuanzi_site_uv: value.totalVisitors }), updatedAt: value.updatedAt }
  } catch { return null }
}

export function writeVisitorCache(counts, storage, now = Date.now()) {
  try { storage.setItem(VISITOR_CACHE_KEY, JSON.stringify({ site: VISITOR_SITE, ...counts, updatedAt: now })) } catch { /* Counting still works when storage is unavailable. */ }
}

export function createVisitorCounter(fetcher = (...args) => fetch(...args), now = Date.now) {
  let pending = null
  let lastSuccess = null
  return function countVisitors() {
    const day = visitorDay(now())
    if (lastSuccess?.day === day && now() - lastSuccess.time < 60_000) return Promise.resolve(lastSuccess.counts)
    if (pending?.day === day) return pending.promise
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8_000)
    const promise = Promise.resolve().then(() => fetcher(VISITOR_API, {
      method: 'POST',
      // A CORS simple request avoids an extra preflight that can be blocked.
      headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
      body: JSON.stringify({ url: VISITOR_SITE, referrer: '' }),
      credentials: 'omit', referrerPolicy: 'no-referrer', signal: controller.signal,
    })).then(async response => {
      if (!response.ok) throw new Error('Visitor service unavailable')
      return readVisitorCounts(await response.json())
    }).then(counts => {
      lastSuccess = { counts, day, time: now() }
      return counts
    }).finally(() => {
      clearTimeout(timeout)
      if (pending?.promise === promise) pending = null
    })
    pending = { day, promise }
    return promise
  }
}

export const countVisitors = createVisitorCounter()
