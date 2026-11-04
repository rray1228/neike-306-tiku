// Preserve both previous question groups without overwriting newer merged answers.
export function migrateJoinedCaseAnswers(selections, submitted, groups) {
  const group = groups.find(g => g.id === 'med-teacher-02-02-03' && g.answerRevision === 'pneumonia-case-v1')
  if (!group) return { selections, submitted }
  const oldKey = group.id, treatmentKey = 'med-teacher-02-04'
  const key = `${oldKey}:${group.answerRevision}`
  if (Object.hasOwn(selections, key) || (!Object.hasOwn(selections, oldKey) && !Object.hasOwn(selections, treatmentKey))) return { selections, submitted }
  const original = selections[oldKey] || {}, treatment = selections[treatmentKey] || {}
  const migrated = { ...original }
  if (treatment[0]) migrated[2] = treatment[0].map(letter => `q4-${letter}`)
  return {
    selections: { ...selections, [key]: migrated },
    submitted: { ...submitted, [key]: Boolean(submitted[oldKey] && submitted[treatmentKey]) },
  }
}

// Only p45-g3 lost its first, unanswered placeholder. Keep the remaining
// two answers in order and retain the old record as a source copy.
export function migrateHemolysisLabAnswers(selections, submitted, groups) {
  const revision = 'hemolysis-lab-no-placeholder-20261104'
  if (!groups.some(group => group.id === 'p45-g3' && group.answerRevision === revision)) return { selections, submitted }
  const oldKey = 'p45-g3:hemolysis-20261011', key = `p45-g3:${revision}`
  if (Object.hasOwn(selections, key) || !Object.hasOwn(selections, oldKey)) return { selections, submitted }
  const old = selections[oldKey], moved = {}
  if (Object.hasOwn(old, 1)) moved[0] = old[1]
  if (Object.hasOwn(old, 2)) moved[1] = old[2]
  return {
    selections: { ...selections, [key]: moved },
    submitted: { ...submitted, [key]: Boolean(submitted[oldKey]) },
  }
}
