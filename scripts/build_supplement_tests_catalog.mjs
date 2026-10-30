import { readFileSync, readdirSync, writeFileSync } from 'node:fs'

const directory = new URL('../src/data/', import.meta.url)
const labels = { med: '内科', pathology: '病理', surgery: '外科', physiology: '生理', biochemistry: '生化', politics: '政治' }
const catalog = []
for (const file of readdirSync(directory).filter(name => name.endsWith('.json') && name !== 'supplement-tests-catalog.json').sort()) {
  const data = JSON.parse(readFileSync(new URL(file, directory)))
  if (!Array.isArray(data.groups)) continue
  const subject = file.split('-')[0]
  if (!labels[subject]) continue
  // All politics practice and the reviewed endocrine supplement are additional exercises.
  // Other subjects explicitly mark imported homework, exams and practitioner questions.
  const groups = data.groups.filter(group => group.supplement || subject === 'politics' || file === 'physiology-endocrine-summary-data.json')
  if (!groups.length) continue
  const category = file.includes('practitioner') ? '执医题'
    : file.includes('stage-exam') ? '阶段考试'
      : file.includes('teacher') ? '课后巩固'
        : file.includes('technique') ? '技巧班作业'
          : file.includes('selftest') ? '专项自测' : '专题补充练习'
  catalog.push({
    id: file.replace(/(?:-data)?\.json$/, ''), subject, subjectLabel: labels[subject],
    title: data.meta.title || data.meta.sourceLabel || `${labels[subject]} · ${category}`,
    category, sourceFile: file, groupIds: groups.map(group => group.id),
    groupCount: groups.length, stemCount: groups.reduce((sum, group) => sum + group.stems.length, 0),
  })
}
writeFileSync(new URL('supplement-tests-catalog.json', directory), `${JSON.stringify(catalog, null, 2)}\n`)
console.log(`${catalog.length} sources · ${catalog.reduce((sum, item) => sum + item.groupCount, 0)} groups · ${catalog.reduce((sum, item) => sum + item.stemCount, 0)} stems`)
