// A new storage revision retains the original records. Joined cross-line blanks
// and fragments from neighbouring crops migrate to their actual text question.
export function sourceStemNumber(group, stem, index) {
  return group.dailySelftest && Number.isInteger(stem.number) ? stem.number : index + 1
}

export function migratePoliticsAnswers(selections, submitted, groups) {
  let nextSelections = selections
  let nextSubmitted = submitted
  for (const group of groups) {
    if (!group.dailySelftest || group.answerRevision !== 'daily-text-v1') continue
    const oldKey = `politics:${group.id}`
    const newKey = `${oldKey}:${group.answerRevision}`
    if (!Object.prototype.hasOwnProperty.call(selections, oldKey) || Object.prototype.hasOwnProperty.call(selections, newKey)) continue
    const original = selections[oldKey]
    const indices = new Map(group.stems.map((stem, index) => [stem.id, index]))
    const migrated = Object.fromEntries(group.stems.map((stem, index) => [index,
      stem.legacyBlankSources.map(sources => [...new Set(sources
        .map(([id, blank]) => original[indices.get(id)]?.[blank])
        .filter(value => typeof value === 'string' && value.length))].join('')),
    ]))
    nextSelections = { ...nextSelections, [newKey]: migrated }
    if (submitted[oldKey]) nextSubmitted = { ...nextSubmitted, [newKey]: true }
  }
  return { selections: nextSelections, submitted: nextSubmitted }
}
