// The second entrance references the original groups, including their answer revisions.
// Add future papers to the catalog without moving or copying question records.
export function studyViewUrl(href, view) {
  const url = new URL(href)
  if (view === 'questions') url.searchParams.delete('view')
  else url.searchParams.set('view', view)
  url.searchParams.delete('paper')
  if (view !== 'mnemonics') {
    url.searchParams.delete('q')
    url.searchParams.delete('mnemonicSubject')
  }
  return url.href
}

export function questionBankUrl(href) {
  const url = new URL(studyViewUrl(href, 'questions'))
  url.pathname = url.pathname.replace(/\/tests\/?$/, '/')
  return url.href
}

export function scopeTestContent(content, paper) {
  if (!paper) return content
  const ids = new Set(paper.groupIds)
  const groups = content.groups.filter(group => ids.has(group.id))
  return {
    ...content,
    groups,
    topics: ['全部', ...new Set(groups.map(group => group.topic))],
    meta: {
      ...content.meta,
      sourceLabel: paper.title,
      groupCount: groups.length,
      stemCount: groups.reduce((sum, group) => sum + group.stems.length, 0),
    },
  }
}
