export const HALF_HOUR = 30 * 60 * 1000
export const IDLE_LIMIT = 5 * 60 * 1000
export const NOTICE_COOLDOWN = 5 * 60 * 1000

export const NOTICE_GROUP_INTERVAL = 20
export const NOTICE_TIME_INTERVAL = 45 * 60000
const PRACTICE_VERSION = 2
const nextBoundary = (value, interval) => (Math.floor(value / interval) + 1) * interval

export function newPractice(now) {
  return { version: PRACTICE_VERSION, groups: [], activeMs: 0, nextGroups: NOTICE_GROUP_INTERVAL, nextActiveMs: NOTICE_TIME_INTERVAL, lastNoticeAt: 0, lastInteractionAt: now, paused: false }
}

export function restorePractice(raw, now) {
  try {
    const value = JSON.parse(raw)
    if (![1, PRACTICE_VERSION].includes(value?.version) || !Array.isArray(value.groups) || !value.groups.every(id => typeof id === 'string')
      || !['activeMs', 'lastNoticeAt', 'lastInteractionAt'].every(key => Number.isFinite(value[key]) && value[key] >= 0)
      || now - value.lastInteractionAt >= HALF_HOUR || value.lastInteractionAt > now) return newPractice(now)
    const groups = [...new Set(value.groups)]
    const currentSchedule = value.version === PRACTICE_VERSION
    // Retain existing practice, but discard the previous random thresholds.
    return { ...value, version: PRACTICE_VERSION, groups, paused: Boolean(value.paused),
      nextGroups: currentSchedule && Number.isSafeInteger(value.nextGroups) && value.nextGroups >= NOTICE_GROUP_INTERVAL ? value.nextGroups : nextBoundary(groups.length, NOTICE_GROUP_INTERVAL),
      nextActiveMs: currentSchedule && Number.isSafeInteger(value.nextActiveMs) && value.nextActiveMs >= NOTICE_TIME_INTERVAL ? value.nextActiveMs : nextBoundary(value.activeMs, NOTICE_TIME_INTERVAL) }
  } catch { return newPractice(now) }
}

export function completePracticeGroup(state, id, now) {
  const current = now - state.lastInteractionAt >= HALF_HOUR ? newPractice(now) : state
  return { ...current, groups: current.groups.includes(id) ? current.groups : [...current.groups, id], lastInteractionAt: now }
}

export function advancePractice(state, from, now, active) {
  if (!active || state.paused) return state
  const until = Math.min(now, state.lastInteractionAt + IDLE_LIMIT)
  return { ...state, activeMs: state.activeMs + Math.max(0, until - from) }
}

export function takePracticeNotice(state, now) {
  const groupsDue = state.groups.length >= state.nextGroups
  const timeDue = state.activeMs >= state.nextActiveMs
  if ((!groupsDue && !timeDue) || (state.lastNoticeAt && now - state.lastNoticeAt < NOTICE_COOLDOWN)) return null
  return {
    state: { ...state, lastNoticeAt: now,
      nextGroups: groupsDue ? state.groups.length + NOTICE_GROUP_INTERVAL : state.nextGroups,
      nextActiveMs: timeDue ? state.activeMs + NOTICE_TIME_INTERVAL : state.nextActiveMs },
    notice: { kind: groupsDue && timeDue ? 'both' : groupsDue ? 'groups' : 'time', groups: state.groups.length, minutes: Math.floor(state.activeMs / 60000) },
  }
}

export function groupHasResponses(group, selections) {
  return group.stems.length > 0 && group.stems.every((stem, index) => {
    const values = selections[index] || []
    if (stem.answerMode === '填空') return stem.answer?.length > 0 && values.length >= stem.answer.length && stem.answer.every((_, blank) => String(values[blank] ?? '').trim())
    if (stem.answerMode === '自评') return Boolean(String(values[0] ?? '').trim())
    if (stem.answerMode === '排序') return values.length > 0 && values.length >= (stem.answer?.length || 0)
    return values.length > 0
  })
}
