const unique = values => [...new Set(values)]
const caseText = group => group.stems.length === 1 && (group.sharedStem || group.stems[0].sharedText)
const number = group => Number(group.stems[0].sourceQuestion ?? group.stems[0].number ?? group.sourceQuestion)
const normalize = text => text.replace(/\s+/g, '')
function caseExtension(text, base) {
  let remaining = normalize(base).length, index = 0
  while (remaining && index < text.length) if (!/\s/.test(text[index++])) remaining--
  return text.slice(index).trim()
}

export function combineSharedClinicalCases(content) {
  const buckets = new Map()
  for (const group of content.groups) {
    const text = group.supplement && caseText(group)
    if (!text || !Number.isFinite(number(group))) continue
    const source = `${group.sourceKey || group.sourceName}\n`
    let key = `${source}${normalize(text)}`
    if (!buckets.has(key)) {
      const extended = [...buckets].find(([address, items]) => address.startsWith(source)
        && address.length - source.length > 60 && normalize(text).startsWith(address.slice(source.length))
        && number(group) === number(items.at(-1)) + 1)
      if (extended) key = extended[0]
    }
    const bucket = buckets.get(key) || []
    bucket.push(group)
    buckets.set(key, bucket)
  }
  const replacements = new Map(), removed = new Set()
  for (const bucket of buckets.values()) {
    bucket.sort((a, b) => number(a) - number(b))
    // Only consecutive questions from one source share a case. Never combine
    // separate papers or coincidentally similar clinical descriptions.
    const runs = []
    for (const group of bucket) {
      const run = runs.at(-1)
      if (run && number(group) === number(run.at(-1)) + 1) run.push(group)
      else runs.push([group])
    }
    for (const run of runs.filter(items => items.length > 1)) {
      const first = run[0], last = run.at(-1), options = [], stems = [], sources = [], pages = new Map()
      for (const group of run) {
        const q = number(group), category = `第${q}题选项`, prefix = `q${q}-`
        const optionKeyMap = Object.fromEntries(group.options.map(option => [option.key, `${prefix}${option.key}`]))
        options.push(...group.options.map(option => ({ ...option, key: optionKeyMap[option.key], displayKey: option.displayKey || option.key, category })))
        const refs = (group.stems[0].lectureEvidencePages || group.lectureEvidencePages || [group.lectureEvidence]).filter(Boolean).map(page => ({
          ...page, questionNumbers: [q], optionKeys: (page.optionKeys || []).map(key => optionKeyMap[key]).filter(Boolean),
        }))
        for (const page of refs) {
          const previous = pages.get(page.image)
          pages.set(page.image, previous ? { ...previous, questionNumbers: unique([...previous.questionNumbers, q]), optionKeys: unique([...previous.optionKeys, ...page.optionKeys]) } : page)
        }
        const { sharedText, ...stem } = group.stems[0]
        const extension = caseExtension(caseText(group), caseText(first))
        stems.push({ ...stem, ...(extension ? { sharedText: extension } : {}), optionCategory: category, answer: stem.answer.map(key => optionKeyMap[key]), lectureEvidencePages: refs })
        sources.push({ id: group.id, answerRevision: group.answerRevision, optionKeyMap })
      }
      const merged = {
        ...first, answerRevision: 'shared-case-v1', joinedSourceGroups: sources,
        title: first.title.replace(`第${number(first)}题`, `第${number(first)}—${number(last)}题`),
        sourceQuestion: `${number(first)}—${number(last)}`, sharedStem: caseText(first), sharedQuestionCount: stems.length,
        options, stems, answerLayout: 'rows',
        lectureIds: unique(run.flatMap(group => group.lectureIds || [])),
        lectureEvidencePages: [...pages.values()], lectureEvidence: [...pages.values()][0],
        lectureSummary: unique(run.flatMap(group => group.lectureSummary || [])),
        sourceText: run.map(group => [group.title, group.sourceText].filter(Boolean).join('\n')).join('\n'),
      }
      replacements.set(first.id, merged)
      run.slice(1).forEach(group => removed.add(group.id))
    }
  }
  const groups = content.groups.filter(group => !removed.has(group.id)).map(group => replacements.get(group.id) || group)
  return { ...content, groups, meta: { ...content.meta, groupCount: groups.length } }
}

export function migrateSharedClinicalCases(subject, selections, submitted, favorites, notes, groups) {
  let nextSelections = selections, nextSubmitted = submitted, nextFavorites = favorites, nextNotes = notes
  const storageKey = id => subject === 'med' ? id : `${subject}:${id}`
  for (const group of groups.filter(group => group.joinedSourceGroups)) {
    const base = storageKey(group.id), key = `${base}:${group.answerRevision}`
    const sources = group.joinedSourceGroups.map(source => ({ ...source, base: storageKey(source.id), key: `${storageKey(source.id)}${source.answerRevision ? `:${source.answerRevision}` : ''}` }))
    if (!Object.hasOwn(nextSelections, key) && sources.some(source => Object.hasOwn(selections, source.key))) {
      const migrated = {}
      sources.forEach((source, index) => {
        if (selections[source.key]?.[0]) migrated[index] = selections[source.key][0].map(letter => source.optionKeyMap[letter]).filter(Boolean)
      })
      nextSelections = { ...nextSelections, [key]: migrated }
      nextSubmitted = { ...nextSubmitted, [key]: sources.every(source => submitted[source.key]) }
    }
    if (sources.some(source => nextFavorites.includes(source.base))) {
      const old = new Set(sources.map(source => source.base))
      const merged = unique([...nextFavorites.filter(item => !old.has(item)), base])
      if (JSON.stringify(merged) !== JSON.stringify(nextFavorites)) nextFavorites = merged
    }
    let note = nextNotes[base] || ''
    for (const source of sources.slice(1)) {
      const text = notes[source.base]
      if (text && !note.includes(text)) note = [note, text].filter(Boolean).join('\n\n')
    }
    if (note && note !== nextNotes[base]) nextNotes = { ...nextNotes, [base]: note }
  }
  return { selections: nextSelections, submitted: nextSubmitted, favorites: nextFavorites, notes: nextNotes }
}
