const unique = values => [...new Set(values)]

// Imported papers keep their original lecture/evidence identifiers. Only the
// navigation address is shared with the corresponding 学成 chapter.
export function chapterLectureIds(group) {
  return group.chapterLectureIds ?? group.lectureIds ?? []
}

function chapterTopic(subject, number, fallback) {
  const ranges = {
    med: [[1, 13, '呼吸'], [14, 23, '消化'], [24, 27, '肾脏'], [28, 35, '血液'], [36, 42, '内分泌'], [43, 47, '风湿'], [48, 48, '中毒'], [49, 57, '循环']],
    physiology: [[1, 1, '绪论'], [2, 5, '细胞基本功能'], [6, 8, '血液'], [9, 13, '循环系统'], [14, 17, '呼吸系统'], [18, 22, '消化系统'], [23, 23, '能量代谢与体温'], [24, 26, '泌尿系统'], [27, 29, '感觉系统'], [30, 34, '中枢神经系统'], [35, 40, '内分泌'], [41, 41, '生殖系统']],
    pathology: [[1, 5, '消化系统'], [6, 10, '心血管系统'], [11, 15, '呼吸系统'], [16, 16, '内分泌系统'], [17, 17, '免疫性疾病'], [18, 18, '生殖系统'], [19, 19, '乳腺疾病'], [20, 21, '传染病'], [22, 23, '损伤与修复'], [24, 24, '局部血液循环障碍'], [25, 25, '炎症'], [26, 26, '肿瘤']],
    surgery: [[1, 1, '颈部疾病'], [2, 2, '胸部疾病'], [3, 3, '乳房疾病'], [4, 4, '胸部疾病'], [5, 5, '胃十二指肠疾病'], [6, 7, '腹部损伤与感染'], [8, 9, '小肠与阑尾疾病'], [10, 11, '结直肠与肛管疾病'], [12, 12, '腹外疝'], [13, 16, '肝胆胰疾病'], [17, 17, '周围血管疾病'], [18, 19, '泌尿外科'], [20, 29, '骨科'], [30, 38, '外科总论']],
    biochemistry: [[1, 1, '糖代谢'], [2, 2, '生物氧化'], [3, 3, '糖代谢'], [4, 6, '脂代谢'], [7, 8, '氨基酸与蛋白质'], [9, 9, '核苷酸代谢'], [10, 11, '胆色素代谢与生物转化'], [12, 12, '酶'], [13, 13, '维生素'], [14, 14, '小基因'], [15, 17, '核酸'], [18, 18, '氨基酸与蛋白质'], [19, 20, '核酸']],
  }
  return ranges[subject]?.find(([first, last]) => number >= first && number <= last)?.[2] ?? fallback
}

export function originalQuestionsFirst(groups) {
  return [...groups].sort((a, b) => Number(Boolean(a.supplement)) - Number(Boolean(b.supplement)))
}

export function organizeChapterPractice(content, subject) {
  if (subject === 'politics') return content
  const lectureMap = new Map(content.lectures.map(lecture => [lecture.id, lecture]))
  const aliases = new Map()
  for (const lecture of content.lectures) {
    const match = lecture.id.match(new RegExp(`^foundation-${subject}-(\\d+)$`))
    const canonical = match && `lecture-${match[1].padStart(2, '0')}`
    if (canonical && lectureMap.has(canonical)) aliases.set(lecture.id, canonical)
  }
  // Ethics has no 学成 chapter; both papers belong to the same ethics chapter.
  if (subject === 'med' && lectureMap.has('lecture-99')) aliases.set('foundation-medical-humanities', 'lecture-99')

  const groups = content.groups.map(group => {
    const ids = chapterLectureIds(group).map(id => aliases.get(id) ?? id)
    const primary = ids[0]?.match(/^lecture-(\d+)$/)
    const topic = group.supplement && primary ? chapterTopic(subject, Number(primary[1]), group.topic) : group.topic
    return { ...group, topic, chapterLectureIds: unique(ids) }
  })
  const topics = unique([...content.topics, ...groups.map(group => group.topic)])
    .filter(topic => topic === '全部' || groups.some(group => group.topic === topic))
  const topicOrder = new Map(topics.map((topic, index) => [topic, index]))
  const lectures = [...lectureMap.values()]
  const lectureOrder = new Map(lectures.map((lecture, index) => [lecture.id, index]))
  const rank = group => Math.min(...chapterLectureIds(group).map(id => lectureOrder.get(id) ?? Infinity))
  groups.sort((a, b) => topicOrder.get(a.topic) - topicOrder.get(b.topic)
    || rank(a) - rank(b)
    || Number(Boolean(a.supplement)) - Number(Boolean(b.supplement)))
  return { ...content, groups, topics, lectures, meta: { ...content.meta, lectureCount: lectures.filter(lecture => !aliases.has(lecture.id)).length } }
}
