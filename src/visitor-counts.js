// Both publications belong to one counter. Never send the reader's query,
// answers or actual referring page to the statistics service.
export const VISITOR_API = 'https://bsz.iirose.cn/api'
export const VISITOR_SITE = 'https://rray1228.github.io/neike-306-tiku/'
export const VISITOR_START = '2026-10-31'
export const VISITOR_CACHE_KEY = 'visitor-counts-soxft-v1'
export const VISITOR_IDENTITY_KEY = 'visitor-identity-soxft-v1'

export const visitorDay = time => new Date(time + 8 * 60 * 60 * 1000).toISOString().slice(0, 10)

function validateCounts(todayVisitors, totalVisitors) {
  if (!Number.isSafeInteger(todayVisitors) || !Number.isSafeInteger(totalVisitors)
    || todayVisitors < 0 || totalVisitors < todayVisitors) throw new Error('Invalid visitor statistics')
  return { todayVisitors, totalVisitors }
}

export function readVisitorCounts(value) {
  if (value?.success !== true) throw new Error('Visitor service unavailable')
  return validateCounts(value.data?.page_uv, value.data?.site_uv)
}

// A shared logical page per Shanghai day gives server-deduplicated daily UV.
// The same response supplies the site's all-time UV; PV is never displayed.
export const visitorBucket = time => `${VISITOR_SITE}__visitor_day__/${visitorDay(time)}`

// Only retain actual service responses. This is a display cache, never a counter.
export function readVisitorCache(storage, now = Date.now()) {
  try {
    const value = JSON.parse(storage.getItem(VISITOR_CACHE_KEY))
    if (value?.site !== VISITOR_SITE || !Number.isFinite(value.updatedAt)
      || value.updatedAt > now || now - value.updatedAt > 7 * 24 * 60 * 60 * 1000) return null
    return { ...validateCounts(value.todayVisitors, value.totalVisitors), updatedAt: value.updatedAt }
  } catch { return null }
}

export function writeVisitorCache(counts, storage, now = Date.now()) {
  try { storage.setItem(VISITOR_CACHE_KEY, JSON.stringify({ site: VISITOR_SITE, ...counts, updatedAt: now })) } catch { /* Counting still works when storage is unavailable. */ }
}

export function createVisitorCounter(fetcher = (...args) => fetch(...args), now = Date.now, storage) {
  let pending = null
  let lastSuccess = null
  let identity = null
  const validIdentity = value => typeof value === 'string' && /^[A-Za-z0-9._-]{1,512}$/.test(value)
  try {
    storage ??= globalThis.localStorage
    const saved = storage?.getItem(VISITOR_IDENTITY_KEY)
    if (validIdentity(saved)) identity = saved
  } catch { /* The server can still deduplicate by IP and UserAgent. */ }
  return function countVisitors() {
    const day = visitorDay(now())
    if (lastSuccess?.day === day && now() - lastSuccess.time < 60_000) return Promise.resolve(lastSuccess.counts)
    if (pending?.day === day) return pending.promise
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8_000)
    const headers = { 'x-bsz-referer': visitorBucket(now()) }
    if (identity) headers.Authorization = `Bearer ${identity}`
    const promise = Promise.resolve().then(() => fetcher(VISITOR_API, {
      method: 'POST',
      headers,
      credentials: 'omit', referrerPolicy: 'no-referrer', signal: controller.signal,
    })).then(async response => {
      if (!response.ok) throw new Error('Visitor service unavailable')
      const counts = readVisitorCounts(await response.json())
      const nextIdentity = response.headers.get('Set-Bsz-Identity')
      if (validIdentity(nextIdentity)) {
        identity = nextIdentity
        try { storage?.setItem(VISITOR_IDENTITY_KEY, identity) } catch { /* Keep the in-memory identity. */ }
      }
      if (visitorDay(now()) !== day) throw new Error('Visitor date changed during request')
      return counts
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
