import { useCallback, useEffect, useRef, useState } from 'react'
import { advancePractice, completePracticeGroup, HALF_HOUR, newPractice, restorePractice, takePracticeNotice } from './study-milestones.js'
import { drawEncouragement } from './encouragements.js'
import { countVisitors, readVisitorCache, writeVisitorCache, visitorDay, LEGACY_VISITOR_CACHE_KEY } from './visitor-counts.js'

const SESSION_KEY = 'study-practice-session-v1'
const MESSAGE_KEY = 'study-encouragement-deck-v3'

export function usePracticeEncouragement(enabled, blocked) {
  const session = useRef(null)
  const [notice, setNotice] = useState(null)
  const noticeRef = useRef(null)
  const initialized = useRef(false)
  const messageDeck = useRef(null)
  const save = useCallback(() => {
    try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(session.current)) } catch { /* Practice still works without storage. */ }
  }, [])
  useEffect(() => {
    if (!initialized.current) {
      try { session.current = restorePractice(sessionStorage.getItem(SESSION_KEY), Date.now()) } catch { session.current = newPractice(Date.now()) }
      initialized.current = true
    }
    if (!enabled) return undefined
    let previousTick = Date.now()
    let wasVisible = document.visibilityState === 'visible' && document.hasFocus()
    function interact(event) {
      if (noticeRef.current || event.target?.closest?.('.encouragement-dialog')) return
      const now = Date.now()
      if (now - session.current.lastInteractionAt >= HALF_HOUR) session.current = newPractice(now)
      session.current.lastInteractionAt = now
      session.current.paused = false
    }
    function tick() {
      const now = Date.now()
      const visible = document.visibilityState === 'visible' && document.hasFocus()
      session.current = advancePractice(session.current, previousTick, now, wasVisible && !noticeRef.current)
      previousTick = now
      wasVisible = visible
      if (visible && !blocked && !noticeRef.current && !session.current.paused
        && !document.activeElement?.matches('input, textarea, select, [contenteditable="true"]')) {
        const next = takePracticeNotice(session.current, now)
        if (next) {
          session.current = next.state
          let storedDeck = messageDeck.current
          try { storedDeck = localStorage.getItem(MESSAGE_KEY) || storedDeck } catch { /* Keep a deck in memory. */ }
          const drawn = drawEncouragement(storedDeck)
          messageDeck.current = JSON.stringify(drawn.state)
          try { localStorage.setItem(MESSAGE_KEY, messageDeck.current) } catch { /* Practice still works without storage. */ }
          noticeRef.current = { ...next.notice, message: drawn.message, quote: drawn.quote }
          setNotice(noticeRef.current)
        }
      }
      save()
    }
    // Visibility/focus events settle the preceding interval before a hidden tab can accrue time.
    const timer = window.setInterval(tick, 1000)
    window.addEventListener('pointerdown', interact, true)
    window.addEventListener('keydown', interact, true)
    window.addEventListener('wheel', interact, { passive: true })
    document.addEventListener('visibilitychange', tick)
    window.addEventListener('blur', tick)
    window.addEventListener('focus', tick)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('pointerdown', interact, true)
      window.removeEventListener('keydown', interact, true)
      window.removeEventListener('wheel', interact)
      document.removeEventListener('visibilitychange', tick)
      window.removeEventListener('blur', tick)
      window.removeEventListener('focus', tick)
      save()
    }
  }, [enabled, blocked, save])
  const recordCompletion = useCallback(id => {
    if (!session.current) return
    session.current = completePracticeGroup(session.current, id, Date.now())
    save()
  }, [save])
  const dismiss = useCallback((pause = false) => {
    session.current.paused = pause
    session.current.lastInteractionAt = Date.now()
    noticeRef.current = null
    setNotice(null)
    save()
  }, [save])
  return { notice, recordCompletion, dismiss }
}

export function EncouragementDialog({ notice, onDismiss }) {
  const dialog = useRef(null)
  const dismissRef = useRef(onDismiss)
  dismissRef.current = onDismiss
  useEffect(() => {
    const previous = document.activeElement
    dialog.current.querySelector('.primary-button').focus({ preventScroll: true })
    function keydown(event) {
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); dismissRef.current(false) }
      if (event.key === 'Tab') {
        const buttons = [...dialog.current.querySelectorAll('button')]
        const first = buttons[0], last = buttons.at(-1)
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    window.addEventListener('keydown', keydown, true)
    return () => { window.removeEventListener('keydown', keydown, true); if (previous?.isConnected) previous.focus({ preventScroll: true }) }
  }, [])
  const title = notice.kind === 'groups' ? `这一轮，已完成 ${notice.groups} 组。`
    : notice.kind === 'time' ? `已经练习 ${notice.minutes} 分钟了。` : `${notice.groups} 组，${notice.minutes} 分钟。`
  return <div className="modal-backdrop encouragement-backdrop" onClick={() => onDismiss(false)}>
    <section ref={dialog} className="encouragement-dialog" role="dialog" aria-modal="true" aria-labelledby="encouragement-title" aria-describedby="encouragement-message encouragement-attribution" onClick={event => event.stopPropagation()}>
      <button className="encouragement-close" aria-label="关闭鼓励" onClick={() => onDismiss(false)}>×</button>
      <span className="encouragement-eyebrow"><span aria-hidden="true">✨</span> 送你一句话</span>
      <h2 id="encouragement-title">{title}</h2>
      <blockquote className="encouragement-quote">
        <p id="encouragement-message">{notice.message}</p>
        <footer id="encouragement-attribution" className="encouragement-attribution">
          <div>— {notice.quote.author}</div>
        </footer>
      </blockquote>
      <div className="encouragement-actions"><button className="ghost-button" onClick={() => onDismiss(true)}>休息一下</button><button className="primary-button" onClick={() => onDismiss(false)}>继续练习 <span aria-hidden="true">→</span></button></div>
    </section>
  </div>
}

export function VisitorCount() {
  const [counts, setCounts] = useState(null)
  const [unavailable, setUnavailable] = useState(false)
  const [loading, setLoading] = useState(true)
  const retryNow = useRef(() => {})
  const [legacySnapshot, setLegacySnapshot] = useState(null)
  const [recoveryView, setRecoveryView] = useState(false)
  useEffect(() => {
    let active = true
    let retry
    let failures = 0
    let running = false
    try { setLegacySnapshot(readVisitorCache(localStorage, Date.now(), LEGACY_VISITOR_CACHE_KEY)) } catch { /* Keep the original cache untouched. */ }
    const inspectBackup = new URLSearchParams(location.search).get('recoverStats') === '1'
    setRecoveryView(inspectBackup)
    if (inspectBackup) requestAnimationFrame(() => document.getElementById('visitor-statistics')?.scrollIntoView({ block: 'center' }))
    try { setCounts(readVisitorCache(localStorage)) } catch { /* Storage may be blocked. */ }
    const refresh = async () => {
      if (!active || running) return
      clearTimeout(retry)
      running = true
      setLoading(true)
      try {
        const value = await countVisitors()
        if (active) {
          const updatedAt = Date.now()
          setCounts({ ...value, updatedAt }); setUnavailable(false); failures = 0
          try { writeVisitorCache(value, localStorage, updatedAt) } catch { /* Storage may be blocked. */ }
        }
      } catch {
        if (active) {
          setUnavailable(true)
          setCounts(previous => previous ? { ...previous } : null)
          retry = setTimeout(refresh, [2_000, 10_000, 30_000, 60_000][Math.min(failures++, 3)])
        }
      } finally { running = false; if (active) setLoading(false) }
    }
    retryNow.current = refresh
    const visible = () => { if (document.visibilityState === 'visible') refresh() }
    refresh()
    window.addEventListener('online', refresh)
    document.addEventListener('visibilitychange', visible)
    const interval = setInterval(visible, 60_000)
    return () => {
      active = false
      retryNow.current = () => {}
      clearTimeout(retry)
      clearInterval(interval)
      window.removeEventListener('online', refresh)
      document.removeEventListener('visibilitychange', visible)
    }
  }, [])
  // The replacement counter is still recording, but its fresh totals must not
  // masquerade as the complete historical totals while recovery is unfinished.
  const today = legacySnapshot && visitorDay(legacySnapshot.updatedAt) === visitorDay(Date.now()) ? legacySnapshot.todayVisitors.toLocaleString() : '—'
  return <footer id="visitor-statistics" className="visitor-count" title="正在核对原数据库、原统计服务和本机保存的历史快照。新计数继续保存，不用新接口的小数字替代完整历史。">
    {legacySnapshot ? <><span>今日访客 <strong>{today}</strong></span><i aria-hidden="true">·</i><span>累计访客 <strong>{legacySnapshot.totalVisitors.toLocaleString()}</strong></span><span title={`历史快照保存于 ${new Date(legacySnapshot.updatedAt).toLocaleString('zh-CN')}`}>历史恢复中</span></> : <span>历史访客统计恢复中</span>}
    {recoveryView && <div className="visitor-recovery-backup"><strong>本机原统计备份</strong><p>{legacySnapshot ? '以下是本浏览器保存过的原统计实际回包，未改写原缓存。' : '本浏览器没有可读取的原统计数字备份。原数据库仍保留，正在核对原统计服务。'}</p>{legacySnapshot && <pre>{JSON.stringify({ source: LEGACY_VISITOR_CACHE_KEY, ...legacySnapshot }, null, 2)}</pre>}<details><summary>本次接入的计数状态（尚未接续历史）</summary><p>{loading ? '同步中' : unavailable ? '同步暂不可用' : '正在保存新计数'}</p>{counts && <pre>{JSON.stringify(counts, null, 2)}</pre>}{unavailable && <button className="visitor-retry" disabled={loading} onClick={() => retryNow.current()}>重试同步</button>}</details></div>}
  </footer>
}
