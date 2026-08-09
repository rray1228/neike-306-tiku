import fs from 'node:fs'
import { surgeryGeneralInfectionGroups, surgeryGeneralLaterGroups } from '../src/data/surgery-general-late-data.js'

const groups = [...surgeryGeneralInfectionGroups, ...surgeryGeneralLaterGroups]
const errors = []
const choiceGroups = groups.filter((group) => group.kind === 'B')
const fillGroups = groups.filter((group) => group.kind === 'FILL')
const stems = groups.flatMap((group) => group.stems)

if (groups.length !== 22) errors.push(`题组数应为22，实际${groups.length}`)
if (choiceGroups.length !== 19) errors.push(`选择题组应为19，实际${choiceGroups.length}`)
if (fillGroups.length !== 3) errors.push(`填空题组应为3，实际${fillGroups.length}`)
if (stems.length !== 139) errors.push(`题干数应为139，实际${stems.length}`)

const ids = new Set()
for (const group of groups) {
  if (ids.has(group.id)) errors.push(`重复题组ID：${group.id}`)
  ids.add(group.id)
  if (!group.title || !group.lectureEvidence?.image) errors.push(`${group.id} 缺标题或讲义证据`)
  if (group.topic !== '外科总论') errors.push(`${group.id} 章节归属错误`)

  const optionKeys = new Set(group.options.map((option) => option.key))
  if (group.kind === 'B') {
    if (group.options.length < 2) errors.push(`${group.id} 选项不足`)
    if (new Set(group.options.map((option) => option.sourceKey)).size !== group.options.length) errors.push(`${group.id} 原始选项键重复`)
    if (group.options.every((option, index) => option.sourceKey === group.optionOriginalOrder[index])) errors.push(`${group.id} 选项未打乱`)
  }
  for (const stem of group.stems) {
    if (!stem.text.trim()) errors.push(`${group.id} 存在空题干`)
    if (!Array.isArray(stem.answer) || stem.answer.length === 0) errors.push(`${group.id} 存在空答案`)
    if (group.kind === 'B' && stem.answer.some((key) => !optionKeys.has(key))) errors.push(`${group.id} 答案指向不存在的选项`)
    if (group.kind === 'FILL' && (stem.text.match(/____/g) || []).length !== stem.answer.length) errors.push(`${group.id} 填空数与答案数不一致：${stem.text}`)
  }
}

if (Math.max(...choiceGroups.map((group) => group.options.length)) !== 33) errors.push('最长选项池应为33项')

const appSource = fs.readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8')
const orderedInsertion = appSource.indexOf('...surgeryGeneralCoreContent.groups') < appSource.indexOf('...surgeryGeneralInfectionGroups')
  && appSource.indexOf('...surgeryGeneralInfectionGroups') < appSource.indexOf('...surgeryGeneralContent.groups')
  && appSource.indexOf('...surgeryGeneralContent.groups') < appSource.indexOf('...surgeryGeneralLaterGroups')
if (!orderedInsertion) errors.push('外科总论讲义顺序应为30～34、35～36、37～38')

const shallow = surgeryGeneralInfectionGroups.find((group) => group.id === 'surgery-general-infection-02')
const sourceAnswerFor = (text) => shallow.stems.find((stem) => stem.text === text).answer.map((key) => shallow.options.find((option) => option.key === key).sourceKey)
for (const key of ['E', 'J']) {
  if (!sourceAnswerFor('疖').includes(key) || sourceAnswerFor('痈').includes(key)) errors.push(`浅部感染讲义修正未落实：${key}`)
}

if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}

console.log(`外科总论后续内容审计通过：${groups.length}组，${stems.length}题干；感染已置于围术期前，休克与其它总论置于麻醉后。`)
