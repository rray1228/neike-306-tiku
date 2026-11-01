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
