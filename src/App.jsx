import { useEffect, useMemo, useState } from 'react'

const SUBJECTS = {
  med: {
    label: '内科',
    title: '内科-学成选择题byBi8bo&戒不掉甜食',
    subtitle: '306 临床医学综合能力（内科）',
    sectionLabel: '内科章节',
    defaultTopic: '呼吸',
    sourceName: '西综-学成选择题（内科汇总去胶带版）.pdf',
  },
  pathology: {
    label: '病理',
    title: '病理-学成选择题byBi8bo&戒不掉甜食',
    subtitle: '306 临床医学综合能力（病理学）',
    sectionLabel: '病理章节',
    defaultTopic: '消化系统',
    sourceName: '病理学西综-学成选择题（去胶带版）.pdf',
  },
  surgery: {
    label: '外科',
    title: '外科-学成选择题byBi8bo&戒不掉甜食',
    subtitle: '306 临床医学综合能力（外科学）',
    sectionLabel: '外科章节',
    defaultTopic: '颈部疾病',
    sourceName: '外科各论除骨科（去胶带版）.pdf',
  },
  physiology: {
    label: '生理',
    title: '生理-学成选择题（2027讲义校正版）',
    subtitle: '306 临床医学综合能力（生理学）',
    sectionLabel: '生理章节',
    defaultTopic: '绪论',
    sourceName: '天天学成选择题（生理学）.pdf',
  },
  biochemistry: {
    label: '生化',
    title: '生化-学成选择题（讲义校对版）',
    subtitle: '生物化学分章题库',
    sectionLabel: '生化知识目录',
    defaultTopic: '糖代谢',
    sourceName: '生化第一章学成选择题（修订扩充版）.docx',
  },
}

const EMPTY_CONTENT = {
  meta: { lectureCount: 0, sourceLabel: '', sourcePages: 0 },
  topics: ['全部'],
  groups: [{ id: 'loading', topic: '全部', kindLabel: '', options: [], stems: [], lectureIds: [] }],
  pages: [],
  lectures: [],
}

const loadJson = (loader) => loader().then((module) => module.default)

const CONTENT_LOADERS = {
  med: () => loadJson(() => import('./data/med-data.json')),
  pathology: () => loadJson(() => import('./data/pathology-data.json')),
  physiology: () => loadJson(() => import('./data/physiology-data.json')),
  surgery: async () => {
    const [surgeryContent, surgeryFractureContent, surgeryDeformityContent, surgeryChronicInjuryContent, surgeryOrthoMixedContent, surgeryOrthoInfectionContent, surgeryNonpurulentArthritisContent, surgeryBoneTumorContent, surgeryTrunkSpineContent, surgeryDegenerativeSpineContent, surgeryLimbFractureContent, surgeryGeneralContent, surgeryGeneralCoreContent, surgeryGeneralLateContent] = await Promise.all([
      loadJson(() => import('./data/surgery-data.json')),
      loadJson(() => import('./data/surgery-fracture-data.json')),
      loadJson(() => import('./data/surgery-deformity-data.json')),
      loadJson(() => import('./data/surgery-chronic-injury-data.json')),
      loadJson(() => import('./data/surgery-ortho-mixed-data.json')),
      loadJson(() => import('./data/surgery-ortho-infection-data.json')),
      loadJson(() => import('./data/surgery-nonpurulent-arthritis-data.json')),
      loadJson(() => import('./data/surgery-bone-tumor-data.json')),
      loadJson(() => import('./data/surgery-trunk-spine-data.json')),
      loadJson(() => import('./data/surgery-degenerative-spine-data.json')),
      loadJson(() => import('./data/surgery-limb-fracture-data.json')),
      loadJson(() => import('./data/surgery-general-data.json')),
      import('./data/surgery-general-core-data.js').then((module) => module.default),
      import('./data/surgery-general-late-data.js'),
    ])
    return {
      ...surgeryContent,
      topics: [...surgeryContent.topics.filter((topic) => topic !== '综合'), '骨科', '外科总论', '综合'],
      groups: [...surgeryContent.groups, ...surgeryFractureContent.groups, ...surgeryDeformityContent.groups, ...surgeryChronicInjuryContent.groups, ...surgeryOrthoMixedContent.groups, ...surgeryOrthoInfectionContent.groups, ...surgeryNonpurulentArthritisContent.groups, ...surgeryBoneTumorContent.groups, ...surgeryTrunkSpineContent.groups, ...surgeryDegenerativeSpineContent.groups, ...surgeryLimbFractureContent.groups, ...surgeryGeneralCoreContent.groups, ...surgeryGeneralLateContent.surgeryGeneralInfectionGroups, ...surgeryGeneralContent.groups, ...surgeryGeneralLateContent.surgeryGeneralLaterGroups],
    }
  },
  biochemistry: async () => {
    const [biochemistryContent, biochemistryLecture2Content, biochemistryLecture3Content, biochemistryLecture4Content, biochemistryLecture5Content, biochemistryLecture6Content, biochemistryLecture7Content, biochemistryLecture8Content, biochemistryLecture9Content] = await Promise.all([
      loadJson(() => import('./data/biochemistry-data.json')),
      loadJson(() => import('./data/biochemistry-lecture2-data.json')),
      loadJson(() => import('./data/biochemistry-lecture3-data.json')),
      loadJson(() => import('./data/biochemistry-lecture4-data.json')),
      loadJson(() => import('./data/biochemistry-lecture5-data.json')),
      loadJson(() => import('./data/biochemistry-lecture6-data.json')),
      loadJson(() => import('./data/biochemistry-lecture7-data.json')),
      loadJson(() => import('./data/biochemistry-lecture8-data.json')),
      loadJson(() => import('./data/biochemistry-lecture9-data.json')),
    ])
    const groups = [...biochemistryContent.groups, ...biochemistryLecture2Content.groups, ...biochemistryLecture3Content.groups, ...biochemistryLecture4Content.groups, ...biochemistryLecture5Content.groups, ...biochemistryLecture6Content.groups, ...biochemistryLecture7Content.groups, ...biochemistryLecture8Content.groups, ...biochemistryLecture9Content.groups].map((group) => ({
      ...group,
      topic: biochemistryParentForTopic(group.topic) || group.topic,
    }))
    return {
      ...biochemistryContent,
      meta: {
        ...biochemistryContent.meta,
        title: '生物化学题库',
        lectureCount: 9,
        groupCount: biochemistryContent.groups.length + biochemistryLecture2Content.groups.length + biochemistryLecture3Content.groups.length + biochemistryLecture4Content.groups.length + biochemistryLecture5Content.groups.length + biochemistryLecture6Content.groups.length + biochemistryLecture7Content.groups.length + biochemistryLecture8Content.groups.length + biochemistryLecture9Content.groups.length,
        stemCount: biochemistryContent.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture2Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture3Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture4Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture5Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture6Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture7Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture8Content.groups.reduce((sum, group) => sum + group.stems.length, 0) + biochemistryLecture9Content.groups.reduce((sum, group) => sum + group.stems.length, 0),
        answerNote: '已收录第 01、02、03、04、05、06、07、08、09 讲题组；每题均只关联本讲讲义页，选项与答案均已按讲义复核。',
      },
      topics: ['糖代谢', '生物氧化', '脂代谢', '氨基酸与蛋白质', '核苷酸代谢'],
      groups,
      pages: [...biochemistryContent.pages, ...biochemistryLecture2Content.pages, ...biochemistryLecture3Content.pages, ...biochemistryLecture4Content.pages, ...biochemistryLecture5Content.pages, ...biochemistryLecture6Content.pages, ...biochemistryLecture7Content.pages, ...biochemistryLecture8Content.pages, ...biochemistryLecture9Content.pages],
      lectures: [...biochemistryContent.lectures, ...biochemistryLecture2Content.lectures, ...biochemistryLecture3Content.lectures, ...biochemistryLecture4Content.lectures, ...biochemistryLecture5Content.lectures, ...biochemistryLecture6Content.lectures, ...biochemistryLecture7Content.lectures, ...biochemistryLecture8Content.lectures, ...biochemistryLecture9Content.lectures],
    }
  },
}

const TOPIC_ICONS = {
  呼吸: 'lungs',
  消化: 'stomach',
  肾脏: 'kidney',
  循环: 'heart',
  血液: 'drop',
  内分泌: 'spark',
  风湿: 'joint',
  中毒: 'skull',
  综合: 'grid',
  消化系统: 'stomach',
  心血管系统: 'heart',
  呼吸系统: 'lungs',
  内分泌系统: 'spark',
  免疫性疾病: 'joint',
  生殖系统: 'grid',
  乳腺疾病: 'grid',
  传染病: 'alert',
  损伤与修复: 'plus',
  局部血液循环障碍: 'drop',
  炎症: 'alert',
  肿瘤: 'grid',
  颈部疾病: 'spark',
  乳房疾病: 'grid',
  胸部疾病: 'lungs',
  胃十二指肠疾病: 'stomach',
  腹部损伤与感染: 'alert',
  小肠与阑尾疾病: 'stomach',
  结直肠与肛管疾病: 'stomach',
  腹外疝: 'grid',
  肝胆胰疾病: 'stomach',
  周围血管疾病: 'drop',
  泌尿外科: 'kidney',
  骨科: 'joint',
  外科总论: 'grid',
  绪论: 'book',
  细胞基本功能: 'spark',
  循环系统: 'heart',
  泌尿系统: 'kidney',
  感觉系统: 'eye',
  中枢神经系统: 'grid',
  '糖无氧氧化与糖有氧氧化': 'spark',
  '红细胞代谢与高能化合物': 'grid',
  '磷酸戊糖途径': 'spark',
  '糖原合成与分解': 'grid',
  '糖异生': 'stomach',
  '糖代谢关键酶与中间物': 'book',
  '胞浆还原当量穿梭与 ATP': 'spark',
  '呼吸链组成与 P/O 比值': 'grid',
  '氧化磷酸化调节与抑制': 'alert',
  糖代谢: 'stomach',
  生物氧化: 'spark',
  脂代谢: 'drop',
  氨基酸与蛋白质: 'book',
  核苷酸代谢: 'book',
}

const BIOCHEMISTRY_DIRECTORY = {
  糖代谢: [
    '糖无氧氧化与糖有氧氧化',
    '红细胞代谢与高能化合物',
    '磷酸戊糖途径',
    '糖原合成与分解',
    '糖异生',
    '糖代谢关键酶与中间物',
  ],
  生物氧化: [
    '胞浆还原当量穿梭与 ATP',
    '呼吸链组成与 P/O 比值',
    '氧化磷酸化调节与抑制',
  ],
}

const MED_LECTURE_TOPIC_RANGES = {
  呼吸: [1, 13],
  消化: [14, 23],
  肾脏: [24, 27],
  血液: [28, 35],
  内分泌: [36, 42],
  风湿: [43, 47],
  中毒: [48, 48],
  循环: [49, 57],
}

const MED_CHAPTER_OVERRIDES = {
  // 消化系统题组的原始 lectureIds 有多处把 14–19 整段讲义混在一起，
  // 这里按疾病讲义重新归类，避免肝脏题目出现在肠道章节下。
  'p20-g1': ['lecture-14'],
  'p20-g2': ['lecture-14'],
  'p21-g1': ['lecture-14'],
  'p21-g2': ['lecture-14'],
  'p21-g3': ['lecture-14'],
  'p22-g1': ['lecture-15'],
  'p22-g2': ['lecture-15', 'lecture-16'],
  'p23-g1': ['lecture-16'],
  'p23-g2': ['lecture-16'],
  'p23-g3': ['lecture-16'],
  'p24-g1': ['lecture-16'],
  'p24-g2': ['lecture-16'],
  'p25-g1': ['lecture-16'],
  'p25-g2': ['lecture-16'],
  'p25-g3': ['lecture-16'],
  'p26-g1': ['lecture-16'],
  'p27-g1': ['lecture-18'],
  'p27-g2': ['lecture-18'],
  'p28-g1': ['lecture-18'],
  'p28-g2': ['lecture-18'],
  'p28-g3': ['lecture-18'],
  'p29-g1': ['lecture-17', 'lecture-18'],
  'p29-g2': ['lecture-18'],
  'p30-g1': ['lecture-19'],
  'p30-g2': ['lecture-20'],
  'p31-g1': ['lecture-20'],
  'p31-g2': ['lecture-21'],
  'p31-g3': ['lecture-21'],
  'p31-g4': ['lecture-21'],
  'p32-g1': ['lecture-21'],
  'p32-g2': ['lecture-22'],
  'p32-g3': ['lecture-22'],
  'p33-g1': ['lecture-22'],
  'p33-g2': ['lecture-17', 'lecture-22'],
  'p33-g3': ['lecture-22'],
  'p34-g1': ['lecture-23'],
  'p34-g2': ['lecture-23'],
  'p34-g3': ['lecture-23'],
  'p36-g1': ['lecture-25'],
  'p36-g2': ['lecture-25'],
  'p36-g3': ['lecture-26'],
  'p42-g1': ['lecture-28'],
  'p42-g2': ['lecture-28'],
  'p42-g3': ['lecture-28'],
  'p45-g1': ['lecture-30'],
  'p45-g2': ['lecture-30'],
  'p45-g3': ['lecture-30'],
  'p45-g4': ['lecture-30'],
  'p47-g1': ['lecture-31'],
  'p47-g2': ['lecture-31'],
  'p50-g1': ['lecture-34'],
  'p54-g1': ['lecture-34'],
  'p54-g2': ['lecture-34'],
  'p56-g1': ['lecture-35'],
  'p57-g1': ['lecture-35'],
  'p59-g1': ['lecture-35'],
  'p60-g1': ['lecture-35'],
  'p71-g1': ['lecture-47'],
  'p71-g2': ['lecture-47'],
}

const CORRECTIONS = {
  'p02-g1:12': {
    title: '讲义校对 · 规范化识别',
    body: 'COPD 在长效支气管扩张剂基础上加用 ICS 的指征，讲义列为：急性加重住院史、每年 ≥2 次中度急性加重、血嗜酸性粒细胞 ≥300/μl、哮喘史或伴哮喘特征。原图中的 “1” 按选项序号应规范为 “I”。',
  },
  'p03-g1:0': {
    title: '讲义校对 · AECOPD 分级',
    body: '原图 OCR 将罗马数字和答案泡连在一起，已按页面视觉内容恢复为 I 级 = A、C、D；II 级 = B、D、E；III 级 = B、E、F。',
  },
  'p86-g3:1': {
    title: '讲义校对 · 稳定型心绞痛预后治疗',
    body: '原题答案将雷诺嗪（G）误列入预防心梗、改善预后。依据冠心病讲义，该题应选 B、D、E、F、H、J、N、O：他汀类（B）、β-R拮抗剂（E）、阿司匹林（F）、ACEI/ARB/ARNI（H）、吲哚布芬（J，阿司匹林不耐受时替代）、依折麦布（O，降脂不足时联用）；替格瑞洛（D）和氯吡格雷（N）仅在支架植入后加用。雷诺嗪（G）属于改善缺血、减轻症状。',
  },
  'p81-g2:2': {
    title: '讲义校对 · S1强弱不等',
    body: '原题页第3小题答案为 A、C、I、M。原数据误将 I（二度Ⅰ型房室阻滞）录成 L（心肌炎）；讲义指出，二度Ⅰ型房室阻滞因 PR 间期进行性延长直至 QRS 波脱落，会出现 S1 强度逐渐减弱和心搏脱落。',
  },
  'p81-g1:3': {
    title: '原题页校对 · S4选项',
    body: 'H 选项原先被误录成“冠心病”，原题页和心音讲义的正确内容是“S4为病理性心音；房颤听不到S4”，因此 S4 的答案 D、H 才能与选项对应。',
  },
  'p08-g4:1': {
    title: '原题页校对 · 小叶性肺炎好发部位',
    body: 'D 选项原先误写为“双肺中叶和背侧”；原题页及肺炎讲义为“双肺下叶和背侧”。小叶性肺炎对应 D，答案字母不变。',
  },
  'p09-g4:0': {
    title: '原题页校对 · 异烟肼选项与答案',
    body: '异烟肼原数据误加 H（高尿酸），原题页答案为 A、B、G；高尿酸是吡嗪酰胺的相关不良反应。B 选项中的“在于酸性病灶”也已按原题页和讲义修正为“在干酪性病灶”。',
  },
  'p09-g4:1': {
    title: '原题页校对 · 药物题干标识',
    body: '已将 G 选项按肺结核讲义修正为“杀死细胞内外TB”；同时去除“利福平R”和“乙胺丁醇E”中误粘入的字母标识，规范为“利福霉素类（如利福平和利福喷丁）”和“乙胺丁醇”；答案分别仍为 EGJ、FK。',
  },
  'p11-g1:1': {
    title: '原题页校对 · 哮喘控制药物选项',
    body: '原题页为“抗IL-4R抗体/抗TSLP抗体”。已修正 OCR 将大写 I 识别为数字 1、并将两个药物选项粘连的问题；同时恢复 A～M 的正常排列。',
  },
  'p13-g1:0': {
    title: '原题页校对 · 杵状指与 5-HT',
    body: '肺癌胸外表现的第一题为“可有杵状指”，原 OCR 漏掉“杵”；原题右侧另有“5-HT”题干，已恢复完整文字。',
  },
  'p14-g1:0': {
    title: '原题页校对 · 肺癌 TNM 分期',
    body: '原题是 10 个独立的 B 型题题干：T1、T2、T3、T4、N0、N1、N2、N3、M0 和远处转移（M1）。原数据曾把 T/N/M 与答案字母粘成 5 行，现已按原题逐行拆开，答案分别为 D、A、F、G、B、H、C、J、K、EIL。',
  },
  'p16-g1:0': {
    title: '讲义校对 · 胸水细胞计数单位',
    body: 'N 选项按原题和胸膜疾病讲义规范为“细胞计数多<100×10^6/L”，已修复 OCR 的度数符号乱码。',
  },
  'p16-g2:0': {
    title: '原题页校对 · 膈神经',
    body: 'C 选项为“膈神经麻痹”，原 OCR 将“膈”误识别为“隔”，已修正。',
  },
  'p20-g1:0': {
    title: '章节归类校对 · 胃食管反流病',
    body: '第 20 页两个题组实际属于消化系统胃食管反流病，已从呼吸系统移入消化系统，并关联胃食管反流病讲义。',
  },
  'p85-g1:1': {
    title: '讲义校对 · 二尖瓣关闭不全',
    body: '原题答案为 ABDFJLNSUaegikmqrv①；l 是二尖瓣脱垂的收缩中晚期喀喇音，不属于二尖瓣关闭不全本题答案，已删除误加的 l。',
  },
  'p85-g1:0': {
    title: '原题页校对 · 瓣膜病选项文字',
    body: '已按第85页原题和瓣膜病讲义逐项核对：a、b 修正为“有相对性二尖瓣狭窄”“有相对性主动脉瓣狭窄”（原题简称“相对性二狭”“相对性主狭”）；同时恢复 L 项“左室：慢性后期离心性肥厚；急性早期正常或轻度扩大”和 x 项“成人：置换术，若老龄重度不耐受TAVR”的原题标点与限定词。',
  },
  'p87-g3:0': {
    title: '原题页校对 · 稳定型心绞痛选项',
    body: 'D 选项原先误录为“明显诱因脑痛”，原题和冠心病讲义均为“明显诱因胸痛，多持续3～5分钟”，已修正。',
  },
  'p88-g1:0': {
    title: '原题页校对 · NSTEMI 与 STEMI 选项',
    body: '已逐项对照第88页原题和冠心病讲义：本题组选项为 A～L；原先误把下一组心肌坏死标志物题的 M“最有价值”合并进来，现已删除。NSTEMI 对应 BDEGIL，STEMI 对应 ACFHJK。',
  },
  'p11-g2:3': {
    title: '讲义校对 · 首选药物',
    body: '支气管哮喘长期控制炎症的首选是吸入型糖皮质激素（ICS）；急性发作的迅速缓解首选 SABA。这里保留原题的药物共用选项组，不改成普通单选题。',
  },
  'p79-g1:8': {
    title: '讲义校对 · 高血压急症',
    body: '高血压急症降压节奏：1 小时内降幅不超过 25%，2–6 小时降至约 160/100 mmHg，24–48 小时逐步降至正常；不应一次性快速降到正常。',
  },
  'p80-g3:0': {
    title: '讲义校对 · 冠心病适用证',
    body: '原题选项 P 与 X 均写作“冠心病”，属于重复选项；已删除 P、保留 X，并同步重排相关答案。结合讲义，冠心病仍属于 ACEI/ARB/ARNI 的适用场景，第1题答案为 C、D、H、V、W、X。',
  },
  'p87-g2:3': {
    title: '讲义校对 · CCS IV级',
    body: 'CCS 心绞痛 IV 级应为“一般体力活动完全受限，轻微活动或休息时也可发作”。原题文字中的“完全不受限”与分级定义矛盾，已依据讲义改正；答案仍为 B。',
  },
  'p92-g1:2': {
    title: '讲义校对 · β-R拮抗剂禁忌证',
    body: 'β-R 拮抗剂禁忌证应为二度Ⅱ型和三度房室传导阻滞，已将 K 选项中的“二度Ⅰ型”改正为“二度Ⅱ型”。同时按原题页恢复 e=收缩压<90、f=房颤、h=急性右室梗死，血管扩张剂不用的答案为 X、e、h。',
  },
  'p81-g2:1': {
    title: '讲义校对 · S1减弱',
    body: '依据讲义，S1 减弱还包括心肌病（J）；规范答案为 B、D、E、G、H、J、L、N。',
  },
  'p83-g3:0': {
    title: '讲义校对 · 左室增大',
    body: '左室增大时心尖搏动多向左下移位，已将 H 选项中的“右下”改正为“左下”。',
  },
  'p83-g4:1': {
    title: '讲义校对 · 水冲脉',
    body: '水冲脉的特征是脉搏骤起骤落，原题 F 选项已按讲义修正，常见相关疾病为甲亢和慢性主动脉瓣关闭不全，规范答案为 F、H、N。',
  },
  'p83-g4:2': {
    title: '讲义校对 · 交替脉',
    body: '交替脉的核心表现是脉搏强弱交替（J），常见于左心衰（L），规范答案为 J、L。',
  },
  'p85-g1:1': {
    title: '讲义校对 · 二尖瓣关闭不全',
    body: '二尖瓣关闭不全还可见心尖收缩中晚期喀喇音（l，常提示二尖瓣脱垂），已补入答案；主动脉瓣狭窄相关 y 选项也已按讲义规范为“儿童青少年非钙化性：分离术”。',
  },
  'p82-g3:0': {
    title: '原题页校对 · 心脏杂音听诊部位',
    body: '第26组原题选项池应为各瓣膜及听诊区：A 肺动脉瓣、B 主动脉瓣第二听诊区、C 三尖瓣、D 二尖瓣、E 室间隔、F 主动脉瓣第一听诊区、G 心脏裸区，已整体恢复。',
  },
  'p82-g4:0': {
    title: '原题页校对 · 瓣膜杂音形态',
    body: '第27组 A 选项应为“一贯型”，与二尖瓣关闭不全的收缩期杂音对应；其余时相和形态选项已按原题页核对。',
  },
  'p27-g1:0': {
    title: '原题页待核对 · 选项池不完整',
    body: '原图的溃疡性结肠炎答案泡含 Y，但页面可见选项只到 X。已保留可核实的答案并标为待核对，不把看不见的 Y 当作有效选项。',
  },
  'p30-g1:13': {
    title: '原题页勘误 · 短期用药',
    body: '第14题原题页答案印作 AT，但该题选项池仅有 A-Q，且讲义明确记载“利福昔明（短期用）”。因此规范答案为 A（利福昔明），不补入不存在的 T。',
  },
}

function Icon({ name, size = 20, stroke = 'currentColor' }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }
  const paths = {
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H19v16H6.5A2.5 2.5 0 0 0 4 21.5z" /><path d="M4 5.5v16M8 7h7M8 11h7" /></>,
    search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
    sliders: <><path d="M4 6h16M4 12h16M4 18h16" /><circle cx="9" cy="6" r="2" fill="white" /><circle cx="15" cy="12" r="2" fill="white" /><circle cx="11" cy="18" r="2" fill="white" /></>,
    settings: <><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" /><circle cx="12" cy="12" r="4" /></>,
    arrow: <><path d="M5 12h13" /><path d="m13 6 6 6-6 6" /></>,
    chevron: <path d="m7 9 5 5 5-5" />,
    left: <><path d="M19 12H5" /><path d="m11 18-6-6 6-6" /></>,
    right: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    bookmark: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.5L6 21z" />,
    bookmarkFill: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.5L6 21z" fill="currentColor" />,
    note: <><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></>,
    file: <><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v5h4M8 12h8M8 16h6" /></>,
    eye: <><path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z" /><circle cx="12" cy="12" r="2.2" /></>,
    check: <path d="m5 12 4.2 4.2L19 6.5" />,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    lungs: <><path d="M12 5v14M12 10c-2.5-3.8-4.3-5.3-5.5-5.3C5.2 4.7 4 8 4 12.5 4 16 6 18 9 18c1.8 0 3-1.4 3-3.2M12 10c2.5-3.8 4.3-5.3 5.5-5.3C18.8 4.7 20 8 20 12.5 20 16 18 18 15 18c-1.8 0-3-1.4-3-3.2" /></>,
    stomach: <><path d="M8 4c0 3 1 4.5 3.5 5.5 2.5 1 4.5 2.8 4.5 5.5a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8c0-2.5 1.5-4 4-4z" /><path d="M8 4c1 2.5 2.5 3 4 3M16 13c2.5 0 3.5-1 4-3" /></>,
    kidney: <><path d="M9 4C5 3.7 3 7 3 11c0 4 2.2 7 5.3 7 2.2 0 3.7-1.6 3.7-4V8.5C12 5.7 10.8 4 9 4Z" /><path d="M15 4c4-.3 6 3 6 7 0 4-2.2 7-5.3 7-2.2 0-3.7-1.6-3.7-4V8.5C12 5.7 13.2 4 15 4Z" /><path d="M9 14c.5-1 1.3-1.5 3-1.5M15 14c-.5-1-1.3-1.5-3-1.5" /></>,
    heart: <><path d="M20.8 8.8c0 5-8.8 10.2-8.8 10.2S3.2 13.8 3.2 8.8A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 8.8 2.8Z" /><path d="M5 11h3l1.2-2.2 2.1 5 1.4-2.8H19" /></>,
    drop: <><path d="M12 3.5s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11Z" /><path d="M9 16.5a3.5 3.5 0 0 0 3 1.5" /></>,
    spark: <><path d="m12 3 1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z" /></>,
    joint: <><circle cx="8" cy="8" r="3" /><circle cx="16" cy="16" r="3" /><path d="m10 10 4 4M5 12l3-1M19 12l-3 1" /></>,
    skull: <><circle cx="12" cy="10" r="7" /><path d="M9 16v3h6v-3M8.5 10h.1M15.4 10h.1M9 13c1.7 1.2 2.3 1.2 3 0 .7 1.2 1.3 1.2 3 0" /></>,
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    alert: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5M12 16h.01" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
    redo: <><path d="M4 8V4m0 0h4M4 4l3.1 3.1A7 7 0 1 1 5 15" /><path d="M4 4 2.8 5.2" /></>,
  }
  return <svg {...common}>{paths[name] || paths.grid}</svg>
}

function unique(values) {
  return [...new Set(values)]
}

function assetPath(path) {
  if (!path) return path
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${String(path).replace(/^\/+/, '')}`
}

function answerLetters(stem) {
  return unique((stem.answer || []).map((item) => String(item)))
}

function answerValues(stem) {
  return (stem.answer || []).map((item) => String(item))
}

function isRankingStem(stem) {
  return stem.answerMode === '排序'
}

function isFillStem(stem) {
  return stem.answerMode === '填空'
}

function isMultiStem(group, stem) {
  return !isFillStem(stem) && (group.kind !== 'B' || answerLetters(stem).length > 1 || isRankingStem(stem))
}

function normalizeSelection(selection) {
  return unique((selection || []).map((item) => String(item))).sort()
}

function isUnresolvedStem(stem) {
  return stem.answerState === '待原题页核对' || stem.answerMode === '待核对' || answerLetters(stem).length === 0
}

function sameAnswer(a, b, ordered = false) {
  if (ordered) return JSON.stringify(unique((a || []).map((item) => String(item)))) === JSON.stringify(unique((b || []).map((item) => String(item))))
  return JSON.stringify(normalizeSelection(a)) === JSON.stringify(normalizeSelection(b))
}

function normalizeFillValue(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[－—–~至]/g, '～')
    .replace(/[，,]/g, '、')
}

function stemIsCorrect(selection, stem) {
  const candidates = [isFillStem(stem) ? answerValues(stem) : answerLetters(stem), ...(stem.acceptedAnswers || [])]
  if (isFillStem(stem)) {
    return candidates.some((candidate) => candidate.length === (selection || []).length && candidate.every((value, index) => normalizeFillValue(value) === normalizeFillValue(selection[index])))
  }
  return candidates.some((candidate) => sameAnswer(selection, candidate, isRankingStem(stem)))
}

function readLocalStorage(key, fallback) {
  if (typeof window === 'undefined') return fallback
  try {
    return JSON.parse(window.localStorage.getItem(key) || JSON.stringify(fallback))
  } catch {
    return fallback
  }
}

function groupStorageKey(subject, groupId) {
  return subject === 'med' ? groupId : `${subject}:${groupId}`
}

function omitStudyRecords(records, storageIds) {
  let changed = false
  const next = {}
  for (const [key, value] of Object.entries(records)) {
    if (storageIds.has(key)) {
      changed = true
    } else {
      next[key] = value
    }
  }
  return changed ? next : records
}

function readFavorites() {
  const stored = readLocalStorage('study-favorites-v1', null)
  const items = stored?.version === 1 && Array.isArray(stored.items)
    ? stored.items
    : readLocalStorage('med-favorites', [])
  return Array.isArray(items) ? unique(items.map((item) => String(item))) : []
}

function topicCounts(groups) {
  const counts = {}
  for (const group of groups) counts[group.topic] = (counts[group.topic] || 0) + group.stems.length
  return counts
}

function navigationLectureIds(subject, group) {
  const override = subject === 'med' ? MED_CHAPTER_OVERRIDES[group.id] : null
  const ids = override || (group.lectureIds?.length ? group.lectureIds : (group.lectureEvidence?.lectureId ? [group.lectureEvidence.lectureId] : []))
  if (subject !== 'med') return unique(ids.map((id) => String(id)).filter(Boolean))
  const range = MED_LECTURE_TOPIC_RANGES[group.topic]
  if (!range) return unique(ids.map((id) => String(id)).filter(Boolean))
  return unique(ids.map((id) => String(id)).filter(Boolean)).filter((id) => {
    const number = Number(String(id).replace('lecture-', ''))
    return number >= range[0] && number <= range[1]
  })
}

function lectureChapterTree(content, subject) {
  const lectures = content.lectures || []
  const lectureMap = new Map(lectures.map((lecture) => [lecture.id, lecture]))
  const topics = unique((content.topics || []).filter((item) => item !== '全部'))
  return topics.map((topic) => {
    const topicGroups = content.groups.filter((group) => group.topic === topic)
    const chapterStats = new Map()
    let unassignedStemCount = 0
    const unassignedGroupIds = []
    for (const group of topicGroups) {
      const lectureIds = navigationLectureIds(subject, group).filter((id) => lectureMap.has(id))
      if (!lectureIds.length) {
        unassignedStemCount += group.stems.length
        unassignedGroupIds.push(group.id)
      }
      for (const lectureId of lectureIds) {
        const previous = chapterStats.get(lectureId) || { groupCount: 0, stemCount: 0, groupIds: [] }
        chapterStats.set(lectureId, {
          groupCount: previous.groupCount + 1,
          stemCount: previous.stemCount + group.stems.length,
          groupIds: previous.groupIds.includes(group.id) ? previous.groupIds : [...previous.groupIds, group.id],
        })
      }
    }
    const chapters = lectures
      .filter((lecture) => chapterStats.has(lecture.id))
      .map((lecture) => ({ ...lecture, ...chapterStats.get(lecture.id) }))
    if (unassignedStemCount) chapters.push({ id: `unassigned:${topic}`, title: '未关联讲义', groupCount: 0, stemCount: unassignedStemCount, groupIds: unassignedGroupIds, unassigned: true })
    return { topic, chapters }
  })
}

function biochemistryParentForTopic(topic) {
  return Object.entries(BIOCHEMISTRY_DIRECTORY).find(([, topics]) => topics.includes(topic))?.[0] || ''
}

function App() {
  const [subject, setSubject] = useState(() => {
    const storedSubject = readLocalStorage('study-subject', 'med')
    return SUBJECTS[storedSubject] ? storedSubject : 'med'
  })
  const subjectConfig = SUBJECTS[subject] || SUBJECTS.med
  const [loadedContent, setLoadedContent] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [loadAttempt, setLoadAttempt] = useState(0)
  const content = loadedContent || EMPTY_CONTENT
  const isLoadingContent = loadedContent === null
  const counts = useMemo(() => topicCounts(content.groups), [content])
  const chapterTree = useMemo(() => lectureChapterTree(content, subject), [content, subject])
  const [topic, setTopic] = useState(() => (SUBJECTS[readLocalStorage('study-subject', 'med')] || SUBJECTS.med).defaultTopic)
  const [chapterId, setChapterId] = useState('')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('全部题型')
  const [groupIndex, setGroupIndex] = useState(0)
  const [jumpGroupId, setJumpGroupId] = useState('')
  const [selections, setSelections] = useState(() => readLocalStorage('med-selections', {}))
  const [submitted, setSubmitted] = useState(() => readLocalStorage('med-submitted', {}))
  const [favorites, setFavorites] = useState(readFavorites)
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [notes, setNotes] = useState(() => readLocalStorage('med-notes', {}))
  const [showSource, setShowSource] = useState(false)
  const [showLectureEvidence, setShowLectureEvidence] = useState(false)
  const [showNote, setShowNote] = useState(false)
  const [mobileEvidence, setMobileEvidence] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false
    if (window.innerWidth <= 720) return true
    const stored = window.localStorage.getItem('med-sidebar-collapsed')
    return stored === null ? false : readLocalStorage('med-sidebar-collapsed', false)
  })
  const [evidenceCollapsed, setEvidenceCollapsed] = useState(() => readLocalStorage('med-evidence-collapsed', false))

  useEffect(() => {
    let cancelled = false
    setLoadedContent(null)
    setLoadError(null)
    CONTENT_LOADERS[subject]().then((nextContent) => {
      if (!cancelled) setLoadedContent(nextContent)
    }).catch(() => {
      if (!cancelled) setLoadError('题库数据暂时加载失败，请检查网络后重试。')
    })
    return () => { cancelled = true }
  }, [subject, loadAttempt])

  useEffect(() => {
    if (!chapterId || !loadedContent || typeof window === 'undefined') return undefined
    const frame = window.requestAnimationFrame(() => {
      document.querySelector('[data-study-content]')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [chapterId, loadedContent])

  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('study-subject', JSON.stringify(subject)) }, [subject])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-selections', JSON.stringify(selections)) }, [selections])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-submitted', JSON.stringify(submitted)) }, [submitted])
  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem('study-favorites-v1', JSON.stringify({ version: 1, items: favorites }))
    window.localStorage.setItem('med-favorites', JSON.stringify(favorites))
  }, [favorites])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-notes', JSON.stringify(notes)) }, [notes])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-sidebar-collapsed', JSON.stringify(sidebarCollapsed)) }, [sidebarCollapsed])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-evidence-collapsed', JSON.stringify(evidenceCollapsed)) }, [evidenceCollapsed])

  const favoriteCounts = useMemo(() => {
    const byTopic = {}
    const byChapter = {}
    let total = 0
    for (const group of content.groups) {
      if (!favorites.includes(groupStorageKey(subject, group.id))) continue
      byTopic[group.topic] = (byTopic[group.topic] || 0) + 1
      for (const lectureId of navigationLectureIds(subject, group)) byChapter[lectureId] = (byChapter[lectureId] || 0) + 1
      total += 1
    }
    return { byTopic, byChapter, total }
  }, [content, favorites, subject])
  const currentChapter = chapterTree.flatMap((item) => item.chapters).find((chapter) => chapter.id === chapterId)
  const currentFavoriteCount = chapterId ? (favoriteCounts.byChapter[chapterId] || 0) : (topic === '全部' ? favoriteCounts.total : (favoriteCounts.byTopic[topic] || 0))
  const notebookName = currentChapter ? `${currentChapter.title}收藏本` : (topic === '全部' ? `${subjectConfig.label}收藏本` : `${topic}收藏本`)

  const filteredGroups = useMemo(() => {
    const query = search.trim().toLowerCase()
    const chapterGroupIds = currentChapter?.groupIds || []
    return content.groups.filter((group) => {
      if (chapterId) {
        if (chapterGroupIds.length) {
          if (!chapterGroupIds.includes(group.id)) return false
        } else {
          const groupLectureIds = navigationLectureIds(subject, group)
          if (chapterId.startsWith('unassigned:')) {
            if (groupLectureIds.length) return false
          } else if (!groupLectureIds.includes(chapterId)) return false
        }
      } else if (topic !== '全部' && group.topic !== topic) {
        return false
      }
      if (favoritesOnly && !favorites.includes(groupStorageKey(subject, group.id))) return false
      if (typeFilter !== '全部题型' && group.kindLabel !== typeFilter) return false
      if (!query) return true
      const haystack = [group.title, group.topic, group.sourceText, ...group.options.map((item) => item.label), ...group.stems.map((stem) => stem.text)].join(' ').toLowerCase()
      return haystack.includes(query)
    })
  }, [chapterId, content, currentChapter, favorites, favoritesOnly, search, subject, topic, typeFilter])

  useEffect(() => {
    if (groupIndex >= filteredGroups.length) setGroupIndex(0)
  }, [filteredGroups.length, groupIndex])

  const group = (jumpGroupId && filteredGroups.find((item) => item.id === jumpGroupId)) || filteredGroups[groupIndex] || content.groups[0]
  const groupStorageId = groupStorageKey(subject, group.id)
  const currentSelections = selections[groupStorageId] || {}
  const isSubmitted = Boolean(submitted[groupStorageId])
  const currentPage = content.pages.find((item) => item.page === group.page)
  const favorite = favorites.includes(groupStorageId)
  const activeSystem = group.topic || topic
  const systemStorageIds = useMemo(() => new Set(
    content.groups
      .filter((item) => item.topic === activeSystem)
      .map((item) => groupStorageKey(subject, item.id)),
  ), [activeSystem, content, subject])
  const systemAttemptedGroups = useMemo(() => {
    let total = 0
    for (const storageId of systemStorageIds) {
      if (selections[storageId] || submitted[storageId]) total += 1
    }
    return total
  }, [selections, submitted, systemStorageIds])

  function updateSelection(stemIndex, key) {
    if (isSubmitted) return
    const stem = group.stems[stemIndex]
    setSelections((previous) => {
      const nextGroup = { ...(previous[groupStorageId] || {}) }
      const ordered = isRankingStem(stem)
      const current = ordered ? unique((nextGroup[stemIndex] || []).map((item) => String(item))) : normalizeSelection(nextGroup[stemIndex])
      const multi = isMultiStem(group, stem)
      if (multi) {
        nextGroup[stemIndex] = current.includes(key) ? current.filter((item) => item !== key) : [...current, key]
      } else {
        nextGroup[stemIndex] = [key]
      }
      return { ...previous, [groupStorageId]: nextGroup }
    })
  }

  function updateFillSelection(stemIndex, blankIndex, value) {
    if (isSubmitted) return
    setSelections((previous) => {
      const nextGroup = { ...(previous[groupStorageId] || {}) }
      const current = [...(nextGroup[stemIndex] || [])]
      current[blankIndex] = value
      nextGroup[stemIndex] = current
      return { ...previous, [groupStorageId]: nextGroup }
    })
  }

  function submitGroup() {
    setSubmitted((previous) => ({ ...previous, [groupStorageId]: true }))
  }

  function redoGroup() {
    setSubmitted((previous) => {
      const next = { ...previous }
      delete next[groupStorageId]
      return next
    })
    setSelections((previous) => {
      const next = { ...previous }
      delete next[groupStorageId]
      return next
    })
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
  }

  function redoSystem() {
    if (!activeSystem || activeSystem === '全部' || !systemStorageIds.size) return
    if (typeof window !== 'undefined') {
      const confirmed = window.confirm(`确认重做“${activeSystem}”系统？\n\n将清空该系统 ${systemStorageIds.size} 个题组的选择和提交记录；收藏与笔记会保留。`)
      if (!confirmed) return
    }
    setSelections((previous) => omitStudyRecords(previous, systemStorageIds))
    setSubmitted((previous) => omitStudyRecords(previous, systemStorageIds))
    selectTopic(activeSystem)
    setMobileEvidence(false)
  }

  function goTo(offset) {
    if (!filteredGroups.length) return
    setJumpGroupId('')
    setGroupIndex((previous) => (previous + offset + filteredGroups.length) % filteredGroups.length)
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
  }

  function jumpTo(index) {
    if (!filteredGroups.length) return
    setJumpGroupId('')
    setGroupIndex(Math.min(Math.max(index, 0), filteredGroups.length - 1))
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
  }

  function toggleFavorite() {
    setFavorites((previous) => previous.includes(groupStorageId) ? previous.filter((id) => id !== groupStorageId) : [...previous, groupStorageId])
  }

  function toggleFavoriteNotebook() {
    setFavoritesOnly((value) => !value)
    setJumpGroupId('')
    setGroupIndex(0)
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
  }

  function showAllGroupsInChapter() {
    setFavoritesOnly(false)
    setJumpGroupId('')
    setSearch('')
    setTypeFilter('全部题型')
    setGroupIndex(0)
  }

  function selectTopic(nextTopic) {
    setTopic(nextTopic)
    setChapterId('')
    setJumpGroupId('')
    setSearch('')
    setTypeFilter('全部题型')
    setFavoritesOnly(false)
    setGroupIndex(0)
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
    if (typeof window !== 'undefined') window.requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0, behavior: 'auto' }))
  }

  function selectChapter(nextChapterId) {
    const chapter = chapterTree.flatMap((item) => item.chapters).find((item) => item.id === nextChapterId)
    if (!chapter) return
    setChapterId(nextChapterId)
    setJumpGroupId(chapter.groupIds?.[0] || '')
    if (!chapter.unassigned) {
      const parent = chapterTree.find((item) => item.chapters.some((item) => item.id === nextChapterId))
      if (parent) {
        setTopic(parent.topic)
      }
    }
    setSearch('')
    setTypeFilter('全部题型')
    setFavoritesOnly(false)
    setGroupIndex(0)
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
    setMobileEvidence(false)
    if (typeof window !== 'undefined') {
      if (window.innerWidth <= 720) setSidebarCollapsed(true)
      else setSidebarCollapsed(false)
    }
  }

  function switchSubject(nextSubject) {
    if (nextSubject === subject) return
    const nextConfig = SUBJECTS[nextSubject]
    setSubject(nextSubject)
    setTopic(nextConfig.defaultTopic)
    setChapterId('')
    setJumpGroupId('')
    setSearch('')
    setTypeFilter('全部题型')
    setGroupIndex(0)
    setShowSource(false)
    setShowLectureEvidence(false)
    setShowNote(false)
    setMobileEvidence(false)
    if (typeof window !== 'undefined' && window.innerWidth > 720) setSidebarCollapsed(false)
  }

  if (isLoadingContent) {
    return (
      <main className="app-loading" aria-live="polite">
        <div className="app-loading-mark"><Icon name="book" size={26} stroke="white" /></div>
        <strong>{loadError || `正在加载${subjectConfig.label}题库`}</strong>
        <span>{loadError ? '已加载的学习记录不会丢失。' : '首次进入只下载当前科目，切换其他科目时再加载。'}</span>
        {loadError && <button className="primary-button app-loading-retry" onClick={() => setLoadAttempt((value) => value + 1)}>重新加载 <Icon name="right" size={16} /></button>}
      </main>
    )
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Icon name="book" size={23} stroke="white" /></div>
          <div className="brand-copy"><strong>{subjectConfig.title}</strong><span>{subjectConfig.subtitle}</span></div>
        </div>
        <div className="subject-switch" aria-label="选择科目">
          {Object.entries(SUBJECTS).map(([key, item]) => <button key={key} className={subject === key ? 'active' : ''} onClick={() => switchSubject(key)}>{item.label}</button>)}
        </div>
        <div className="progress-strip">
          <span>本轮进度</span><strong>{filteredGroups.length ? `${Math.min(groupIndex + 1, filteredGroups.length)} / ${filteredGroups.length} 组` : '暂无匹配题组'}</strong>
          <div className="progress-bar"><i style={{ width: `${filteredGroups.length ? ((groupIndex + 1) / filteredGroups.length) * 100 : 0}%` }} /></div>
          <span>{filteredGroups.length ? Math.round(((groupIndex + 1) / filteredGroups.length) * 100) : 0}%</span>
        </div>
        <div className="top-actions">
          <label className="search-box"><Icon name="search" size={18} /><input value={search} onChange={(event) => { setSearch(event.target.value); setJumpGroupId(''); setGroupIndex(0) }} placeholder="搜索题目 / 关键词" /><kbd>⌘ K</kbd></label>
          <label className="filter-box"><Icon name="sliders" size={17} /><select value={typeFilter} onChange={(event) => { setTypeFilter(event.target.value); setJumpGroupId(''); setGroupIndex(0) }}><option>全部题型</option><option>B型题</option><option>填空题</option><option>排序题</option><option>多项选择</option><option>匹配 / 归类</option><option>原题页核对</option></select><Icon name="chevron" size={15} /></label>
          <button className="icon-button" aria-label="设置"><Icon name="settings" size={19} /></button>
        </div>
      </header>

      <div className={`workspace ${sidebarCollapsed ? 'sidebar-collapsed' : ''} ${evidenceCollapsed ? 'evidence-collapsed' : ''}`}>
        <aside className="sidebar">
          <div className="sidebar-heading"><div className="sidebar-title">{subjectConfig.sectionLabel}</div><button className="sidebar-toggle" onClick={() => setSidebarCollapsed((value) => !value)} aria-label={sidebarCollapsed ? '展开章节目录' : '收起章节目录'}><Icon name={sidebarCollapsed ? 'right' : 'left'} size={17} /></button></div>
          <nav className="topic-nav">
            <button className={`favorite-notebook-link ${favoritesOnly ? 'active' : ''}`} onClick={toggleFavoriteNotebook} aria-pressed={favoritesOnly} title={`${notebookName}，共 ${currentFavoriteCount} 个题组`}>
              <span className="topic-icon"><Icon name={favoritesOnly ? 'bookmarkFill' : 'bookmark'} size={21} /></span><span>{notebookName}</span><em>{currentFavoriteCount}</em>
            </button>
            <div className="topic-nav-label">系统 / 讲义章节</div>
            {chapterTree.map(({ topic: system, chapters }) => (
              <div className="topic-tree" key={system}>
                <button className={`topic-link ${topic === system && !chapterId ? 'active' : ''}`} onClick={() => selectTopic(system)} aria-expanded={topic === system}>
                  <span className="topic-icon"><Icon name={TOPIC_ICONS[system]} size={22} /></span><span>{system}</span><span className="topic-counts"><em>{counts[system] || 0}</em>{favoriteCounts.byTopic[system] ? <small title={`${favoriteCounts.byTopic[system]} 个收藏题组`}><Icon name="bookmarkFill" size={10} />{favoriteCounts.byTopic[system]}</small> : null}</span>
                </button>
                {topic === system && chapters.length > 0 && <div className="chapter-nav" aria-label={`${system}讲义章节`}>
                  {chapters.map((chapter) => <button key={chapter.id} className={`chapter-link ${chapterId === chapter.id ? 'active' : ''}`} onClick={() => selectChapter(chapter.id)} title={`跳转到${chapter.title}首题`} aria-label={`跳转到${chapter.title}首题`}><span className="chapter-marker" /><span title={chapter.title}>{chapter.title}</span><em>{chapter.stemCount}</em></button>)}
                </div>}
              </div>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div className="source-stat"><span>题库来源</span><strong>{content.meta.sourceLabel || '学成选择题（题目数据版）'}</strong><small>{content.groups.length} 个题组 · {content.groups.reduce((sum, item) => sum + item.stems.length, 0)} 个题干</small></div>
            <div className="lecture-stat"><span>讲义依据</span><strong>{subjectConfig.label}讲义 PDF 共 {content.meta.lectureCount} 份</strong><Icon name="file" size={18} /></div>
          </div>
        </aside>

        <main className="main-content">
          <div className="mobile-topic-row">
            <button className="text-button directory-button" onClick={() => setSidebarCollapsed((value) => !value)}><Icon name={sidebarCollapsed ? 'right' : 'left'} size={16} />{sidebarCollapsed ? '章节' : '收起目录'}</button>
            <select value={topic} onChange={(event) => selectTopic(event.target.value)} aria-label="选择系统">{content.topics.map((item) => <option key={item}>{item}</option>)}</select>
            <select value={chapterId} onChange={(event) => event.target.value ? selectChapter(event.target.value) : selectTopic(topic)} aria-label="选择讲义章节"><option value="">全部讲义章节</option>{chapterTree.map(({ topic: system, chapters }) => chapters.length > 0 ? <optgroup key={system} label={system}>{chapters.map((chapter) => <option key={chapter.id} value={chapter.id}>{chapter.title}</option>)}</optgroup> : null)}</select>
            <button className={`text-button mobile-favorite-button ${favoritesOnly ? 'selected' : ''}`} onClick={toggleFavoriteNotebook} aria-pressed={favoritesOnly}><Icon name={favoritesOnly ? 'bookmarkFill' : 'bookmark'} size={16} />收藏本 {currentFavoriteCount}</button>
            <button className="text-button" onClick={() => setMobileEvidence((value) => !value)}>{mobileEvidence ? '隐藏讲义' : '显示讲义'} <Icon name="file" size={16} /></button>
            {filteredGroups.length > 0 && activeSystem !== '全部' ? <button className="text-button system-redo-button" onClick={redoSystem} title={`清空${activeSystem}系统全部作答，收藏和笔记保留`}><Icon name="redo" size={16} />重做{activeSystem}{systemAttemptedGroups ? ` · ${systemAttemptedGroups}` : ''}</button> : null}
          </div>
          <div className="desktop-chapter-jump">
            <span>章节快速跳转</span>
            <select value={chapterId} onChange={(event) => event.target.value ? selectChapter(event.target.value) : selectTopic(topic)} aria-label="章节快速跳转">
              <option value="">{topic === '全部' ? '全部章节' : `${topic} · 全部章节`}</option>
              {chapterTree.map(({ topic: system, chapters }) => chapters.length > 0 ? <optgroup key={system} label={system}>{chapters.map((chapter) => <option key={chapter.id} value={chapter.id}>{chapter.title}</option>)}</optgroup> : null)}
            </select>
            {filteredGroups.length > 0 && activeSystem !== '全部' ? <button className="system-redo-button" onClick={redoSystem} title={`清空${activeSystem}系统全部作答，收藏和笔记保留`}><Icon name="redo" size={15} />重做{activeSystem}{systemAttemptedGroups ? ` · ${systemAttemptedGroups}` : ''}</button> : null}
          </div>
          {!filteredGroups.length && <div className="empty-state"><div className="empty-state-icon"><Icon name={favoritesOnly ? 'bookmark' : 'search'} size={22} /></div><h1>{favoritesOnly ? `${notebookName}暂无题组` : '当前筛选下没有题组'}</h1><p>{favoritesOnly ? '点击题组右上角的“收藏”后，它会自动进入当前科目与章节的收藏本。' : '请尝试清除搜索词、切换章节或选择其他题型。'}</p><button className="primary-button" onClick={favoritesOnly ? showAllGroupsInChapter : () => { setTopic('全部'); setSearch(''); setTypeFilter('全部题型'); setGroupIndex(0) }}>{favoritesOnly ? '返回本章全部题组' : '显示全部题库'} <Icon name="arrow" size={17} /></button></div>}
          {filteredGroups.length > 0 && <div className="study-content" data-study-content>
          {favoritesOnly && <div className="favorite-notebook-banner"><span className="favorite-notebook-icon"><Icon name="bookmarkFill" size={18} /></span><div><strong>{notebookName}</strong><small>正在复习已收藏题组 · 共 {filteredGroups.length} 组</small></div><button onClick={showAllGroupsInChapter}>退出收藏本</button></div>}
          <div className="breadcrumb"><span>{group.topic || '综合'}</span>{currentChapter ? <><Icon name="chevron" size={13} /><span>{currentChapter.title}</span></> : null}<Icon name="chevron" size={13} /><span>{group.kindLabel}</span>{group.hideSource ? null : <><Icon name="chevron" size={13} /><strong>原题第 {group.page} 页</strong></>}</div>
          <div className="content-heading">
            <div><h1>{group.title || '题库原题'}</h1><p>{group.kindLabel === '填空题' ? '按题干顺序填写数字或原词，提交后逐题核对。' : (group.kindLabel === '排序题' ? '依次点击选项完成排序；再次点击可移除后重新排列。' : '共用选项组保留在本题组内；每个题干独立作答，提交后逐题反馈。')}</p></div>
            <div className="heading-actions"><button className={`ghost-button ${favorite ? 'selected' : ''}`} onClick={toggleFavorite} aria-pressed={favorite} title={favorite ? `从${group.topic}收藏本移除` : `收藏到${group.topic}收藏本`}><Icon name={favorite ? 'bookmarkFill' : 'bookmark'} size={17} />{favorite ? '已收藏' : '收藏'}</button><button className="ghost-button" onClick={() => setShowNote((value) => !value)}><Icon name="note" size={17} />笔记</button></div>
          </div>

          {showNote && <div className="note-strip"><Icon name="note" size={17} /><input value={notes[groupStorageId] || ''} onChange={(event) => setNotes((previous) => ({ ...previous, [groupStorageId]: event.target.value }))} placeholder="写下你的易错点或记忆口诀…" /></div>}

          <div className={`study-grid ${group.options.length ? '' : 'no-options'}`}>
          {group.options.length > 0 && <OptionBank group={group} />}
          <div className="question-side">
          <section className="question-card">
            <div className="question-card-top"><span className="question-type">{group.kindLabel}</span><span>题组 {groupIndex + 1} / {filteredGroups.length}</span>{group.hideSource ? null : <span>来源页 {group.page}</span>}</div>
            {group.options.some((option) => option.category) && group.stems.some((stem) => stem.optionCategory)
              ? <CategorizedAnswerTable group={group} selections={currentSelections} submitted={isSubmitted} onSelect={updateSelection} />
              : <div className="stem-list">
                {group.stems.map((stem, index) => <StemRow key={`${subject}-${group.id}-${index}`} group={group} stem={stem} index={index} selection={currentSelections[index] || []} submitted={isSubmitted} onSelect={updateSelection} onFill={updateFillSelection} />)}
              </div>}
            <div className="question-card-bottom">
              {isSubmitted ? <div className="submit-summary"><Icon name="check" size={18} /><span>已提交 · {group.stems.filter((stem, index) => !isUnresolvedStem(stem) && stemIsCorrect(currentSelections[index] || [], stem)).length} / {group.stems.filter((stem) => !isUnresolvedStem(stem)).length} 个题干正确{group.stems.some(isUnresolvedStem) ? ` · ${group.stems.filter(isUnresolvedStem).length} 个待原题核对` : ''}</span></div> : <span className="hint-text">完成每个题干后提交；排序题按点击先后记录，填空题按空格顺序判分。</span>}
              <button className={`primary-button ${isSubmitted ? 'redo-button' : ''}`} onClick={isSubmitted ? redoGroup : submitGroup}>{isSubmitted ? '重新作答' : '提交本题组'}<Icon name={isSubmitted ? 'right' : 'arrow'} size={17} /></button>
            </div>
          </section>

          <div className="bottom-nav"><button className="pager-button" onClick={() => goTo(-1)}><Icon name="left" size={18} />上一组</button><GroupJump key={`${subject}-${groupIndex}-${filteredGroups.length}`} current={groupIndex + 1} total={filteredGroups.length} onJump={jumpTo} /><button className="pager-button" onClick={() => goTo(1)}>下一组<Icon name="right" size={18} /></button></div>
          </div>
          </div>
          </div>}
        </main>

        {filteredGroups.length ? <EvidencePanel subject={subject} content={content} group={group} page={currentPage} sourceName={group.sourceName || subjectConfig.sourceName} submitted={isSubmitted} setShowSource={setShowSource} setShowLectureEvidence={setShowLectureEvidence} mobileEvidence={mobileEvidence} setMobileEvidence={setMobileEvidence} evidenceCollapsed={evidenceCollapsed} setEvidenceCollapsed={setEvidenceCollapsed} /> : <EmptyEvidence subjectConfig={subjectConfig} evidenceCollapsed={evidenceCollapsed} setEvidenceCollapsed={setEvidenceCollapsed} />}
      </div>

      {showSource && currentPage && <SourceModal group={group} page={currentPage} sourceName={group.sourceName || subjectConfig.sourceName} onClose={() => setShowSource(false)} />}
      {showLectureEvidence && group.lectureEvidence && <LectureEvidenceModal evidence={group.lectureEvidence} onClose={() => setShowLectureEvidence(false)} />}
      <div className="site-watermark" aria-hidden="true">
        <span>内容制作byBi8bo</span>
        <span>网站制作by戒不掉甜食</span>
      </div>
    </div>
  )
}

function OptionBank({ group }) {
  const categories = unique(group.options.map((option) => option.category).filter(Boolean))
  const categorized = categories.length > 0
  return (
    <aside className={`option-bank option-rail ${categorized ? 'categorized-option-bank' : ''}`}>
      <div className="section-label"><span>共用选项</span><em>{group.kindLabel}</em></div>
      {categorized ? <div className="option-category-list">{categories.map((category) => <section className="option-category" key={category}><h3>{category}</h3><div className="option-grid">{group.options.filter((option) => option.category === category).map((option) => <div className="shared-option" key={option.key}><b>{option.displayKey || option.key}</b><span>{option.label}</span></div>)}</div></section>)}</div> : <div className="option-grid">{group.options.map((option) => <div className="shared-option" key={option.key}><b>{option.displayKey || option.key}</b><span>{option.label}</span></div>)}</div>}
      <p className="option-rail-hint">{categorized ? '选项已按考点分区，区内固定打乱；右侧题干逐题作答。' : '选项固定在左侧，右侧题干逐题作答。'}</p>
    </aside>
  )
}

function GroupJump({ current, total, onJump }) {
  const [value, setValue] = useState(String(current))

  function submitJump(event) {
    event.preventDefault()
    const requested = Number.parseInt(value, 10)
    const next = Number.isFinite(requested) ? Math.min(Math.max(requested, 1), total) : current
    setValue(String(next))
    onJump(next - 1)
  }

  return (
    <form className="group-jump" onSubmit={submitJump}>
      <span>跳至</span>
      <input
        type="number"
        inputMode="numeric"
        min="1"
        max={total}
        step="1"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        aria-label={`跳转到第几组，当前范围共 ${total} 组`}
      />
      <span>/ {total} 组</span>
      <button type="submit">跳转</button>
    </form>
  )
}

function CategorizedAnswerTable({ group, selections, submitted, onSelect }) {
  const categories = unique(group.stems.map((stem) => stem.optionCategory).filter(Boolean))

  return (
    <div className="categorized-answer-tables">
      <div className="answer-table-hint"><Icon name="check" size={15} />左侧查看选项内容，右侧表格只勾选对应字母；多选题可在同一行选择多个。</div>
      {categories.map((category) => {
        const options = group.options.filter((option) => option.category === category)
        const rows = group.stems.map((stem, index) => ({ stem, index })).filter(({ stem }) => stem.optionCategory === category)
        return (
          <section className="answer-table-section" key={category}>
            <div className="answer-table-title"><strong>{category}</strong><span>{rows.length} 个题干 · {options.length} 个共用选项</span></div>
            <div className="answer-table-scroll">
              <table className="answer-table">
                <thead>
                  <tr>
                    <th className="answer-table-number">题号</th>
                    <th className="answer-table-stem">题干</th>
                    {options.map((option) => <th key={option.key} className="answer-table-option" title={option.label}>{option.displayKey || option.key}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {rows.map(({ stem, index }) => <CategorizedAnswerRow key={index} group={group} stem={stem} index={index} options={options} selection={selections[index] || []} submitted={submitted} onSelect={onSelect} />)}
                </tbody>
              </table>
            </div>
          </section>
        )
      })}
    </div>
  )
}

function CategorizedAnswerRow({ group, stem, index, options, selection, submitted, onSelect }) {
  const answer = answerLetters(stem)
  const multi = isMultiStem(group, stem)
  const unresolved = isUnresolvedStem(stem)
  const correct = submitted && !unresolved && stemIsCorrect(selection, stem)
  const missed = submitted && !unresolved && answer.some((item) => !selection.includes(item))
  const answerDisplay = stem.answerDisplay || answer.map((item) => group.options.find((option) => option.key === item)?.displayKey || item).join('、')

  return (
    <>
      <tr className={`answer-table-row ${submitted ? (correct ? 'is-correct' : 'is-wrong') : ''}`}>
        <th scope="row" className="answer-table-number"><span>{String(index + 1).padStart(2, '0')}</span></th>
        <td className="answer-table-stem"><div className="answer-table-stem-copy">{stem.image && <img src={assetPath(stem.image)} alt={stem.imageAlt || '题干图片'} />}{stem.text && <p>{stem.text}</p>}<span className={`answer-mode ${(multi || stem.answerMode === '排序') ? 'is-multi' : ''}`}>{unresolved ? '待核对' : (stem.answerMode === '排序' ? '排序' : (multi ? '多选' : '单选'))}</span></div></td>
        {options.map((option) => {
          const item = option.key
          const label = option.displayKey || item
          const active = selection.includes(item)
          const isAnswer = submitted && answer.includes(item)
          const isMissed = submitted && isAnswer && !active
          const stateLabel = isMissed ? '，漏选' : (submitted && active && !isAnswer ? '，错选' : '')
          return <td key={item} className="answer-table-cell"><button type="button" aria-label={`${String(index + 1).padStart(2, '0')}题，选项 ${label}${stateLabel}`} className={`answer-chip ${active ? 'active' : ''} ${submitted && isAnswer ? 'answer' : ''} ${isMissed ? 'missed' : ''} ${submitted && active && !isAnswer ? 'wrong' : ''}`} onClick={() => onSelect(index, item)} disabled={submitted}>{label}</button></td>
        })}
      </tr>
      {submitted && <tr className={`answer-table-result-row ${unresolved ? 'pending' : (correct ? 'ok' : 'bad')}`}><td colSpan={options.length + 2}><span><Icon name={unresolved ? 'file' : (correct ? 'check' : 'alert')} size={15} />{unresolved ? '原题页核对：暂不自动判分' : (correct ? '正确' : `讲义答案：${answerDisplay}`)}{missed && <span className="missed-legend">橙色 = 漏选</span>}</span></td></tr>}
    </>
  )
}

function StemRow({ group, stem, index, selection, submitted, onSelect, onFill }) {
  const answer = isFillStem(stem) ? answerValues(stem) : answerLetters(stem)
  const multi = isMultiStem(group, stem)
  const ordered = isRankingStem(stem)
  const fill = isFillStem(stem)
  const unresolved = isUnresolvedStem(stem)
  const correct = submitted && !unresolved && stemIsCorrect(selection, stem)
  const wrong = submitted && !unresolved && !correct
  const missed = !fill && submitted && !unresolved && answer.some((item) => !selection.includes(item))
  const choiceOptions = group.options.length
    ? group.options.filter((option) => !stem.optionCategory || option.category === stem.optionCategory)
    : answer.map((item) => ({ key: item, displayKey: item }))
  const keys = choiceOptions.map((option) => option.key)
  const answerDisplay = stem.answerDisplay || answer.map((item) => group.options.find((option) => option.key === item)?.displayKey || item).join('、')
  return (
    <div className={`stem-row ${stem.image ? 'image-stem' : ''} ${submitted ? (correct ? 'is-correct' : 'is-wrong') : ''}`}>
      <div className="stem-main"><span className="stem-number">{String(index + 1).padStart(2, '0')}</span><div className="stem-copy">{stem.image && <figure className="stem-figure"><img src={assetPath(stem.image)} alt={stem.imageAlt || '心电图题干'} /></figure>}{stem.text ? <div className="stem-heading"><p>{stem.text}</p><span className={`answer-mode ${(multi || fill) ? 'is-multi' : ''}`}>{unresolved ? '待核对' : (fill ? '填空' : (ordered ? '排序' : (multi ? '多选' : '单选')))}</span></div> : <div className="stem-image-heading"><span className={`answer-mode ${(multi || fill) ? 'is-multi' : ''}`}>{unresolved ? '待核对' : (fill ? '填空' : (ordered ? '排序' : (multi ? '多选' : '单选')))}</span></div>}{(multi || fill) && !submitted && <small>{fill ? `依次填写 ${answer.length} 个空` : (ordered ? '请按题干要求的先后顺序选择' : '可选择多个共用选项')}</small>}</div></div>
      {fill ? <div className="fill-answers">{answer.map((_, blankIndex) => <label key={blankIndex}><span>{stem.blankLabels?.[blankIndex] || `空${blankIndex + 1}`}</span><input value={selection[blankIndex] || ''} onChange={(event) => onFill(index, blankIndex, event.target.value)} disabled={submitted} inputMode={stem.inputMode || 'text'} aria-label={`${stem.text}第${blankIndex + 1}空`} /></label>)}</div> : <div className="answer-choices">{choiceOptions.map((option) => { const item = option.key; const label = option.displayKey || item; const active = selection.includes(item); const isAnswer = submitted && answer.includes(item); const isMissed = submitted && isAnswer && !active; const order = ordered && active ? selection.indexOf(item) + 1 : null; const stateLabel = isMissed ? '，漏选' : (submitted && active && !isAnswer ? '，错选' : ''); return <button key={item} aria-label={`选项 ${label}${stateLabel}`} className={`answer-chip ${active ? 'active' : ''} ${submitted && isAnswer ? 'answer' : ''} ${isMissed ? 'missed' : ''} ${submitted && active && !isAnswer ? 'wrong' : ''}`} onClick={() => onSelect(index, item)} disabled={submitted}>{label}{order && <sup className="rank-order">{order}</sup>}</button> })}</div>}
      {submitted && <div className={`result-line ${unresolved ? 'pending' : (correct ? 'ok' : 'bad')}`}><Icon name={unresolved ? 'file' : (correct ? 'check' : 'alert')} size={15} />{unresolved ? '原题页核对：暂不自动判分' : (correct ? '正确' : `讲义答案：${answerDisplay}`)}{missed && <span className="missed-legend">橙色 = 漏选</span>}</div>}
    </div>
  )
}

function EvidencePanel({ subject, content, group, page, sourceName, submitted, setShowSource, setShowLectureEvidence, mobileEvidence, setMobileEvidence, evidenceCollapsed, setEvidenceCollapsed }) {
  const lectureItems = group.lectureIds.map((id) => content.lectures.find((lecture) => lecture.id === id)).filter(Boolean)
  const currentEvidence = group.lectureEvidence
  return (
    <aside className={`evidence-panel ${mobileEvidence ? 'mobile-visible' : ''} ${evidenceCollapsed ? 'is-collapsed' : ''}`}>
      <div className="evidence-rail">
        <button className="evidence-toggle" onClick={() => setEvidenceCollapsed(false)} aria-label="展开讲义栏" aria-expanded="false" title="展开讲义栏"><Icon name="left" size={17} /></button>
        <span className="evidence-rail-icon"><Icon name="file" size={18} /></span>
        <span className="evidence-rail-label">讲义</span>
      </div>
      <div className="evidence-panel-content">
      <div className="evidence-section evidence-section-top"><div className="evidence-title"><span className="evidence-icon"><Icon name="check" size={18} /></span><div><h2>讲义依据</h2><p>{lectureItems.length ? `已关联 ${lectureItems.length} 份讲义` : '按章节关联讲义'}</p></div><span className="verified-dot"><Icon name="check" size={13} /></span><button className="evidence-toggle desktop-evidence-toggle" onClick={() => setEvidenceCollapsed(true)} aria-label="收起讲义栏" aria-expanded="true" title="收起讲义栏"><Icon name="right" size={17} /></button><button className="panel-close mobile-panel-close" onClick={() => setMobileEvidence(false)} aria-label="关闭讲义"><Icon name="chevron" size={16} /></button></div>
        {lectureItems.slice(0, 4).map((lecture) => <div className="lecture-item" key={lecture.id}><Icon name="file" size={18} /><div><strong>{lecture.title}</strong><span>第 {lecture.number} 讲 · {currentEvidence?.lectureId === lecture.id ? `对应第 ${currentEvidence.page} 页` : `共 ${lecture.pageCount} 页`}</span></div><span className="relevance">对应</span></div>)}
        <div className="all-lectures">查看全部 {content.meta.lectureCount} 份讲义 <Icon name="right" size={15} /></div>
      </div>
      {currentEvidence && <div className="evidence-section lecture-proof"><div className="lecture-proof-heading"><span>对应讲义页</span><strong>{currentEvidence.title}</strong><p>本题组对应的讲义原页，可点击图片放大查看。</p></div><button className="lecture-proof-image" onClick={() => setShowLectureEvidence(true)} aria-label={`放大查看${currentEvidence.title}`}><img src={assetPath(currentEvidence.image)} alt={`${currentEvidence.title}原页`} /><span><Icon name="eye" size={16} />点击放大查看讲义原页</span></button></div>}
      {page?.image ? <div className="source-thumb"><img src={assetPath(page.image)} alt={`题库原题第 ${group.page} 页`} /><button onClick={() => setShowSource(true)}><Icon name="eye" size={16} /></button></div> : null}
      </div>
    </aside>
  )
}

function EmptyEvidence({ subjectConfig, evidenceCollapsed, setEvidenceCollapsed }) {
  return <aside className={`evidence-panel empty-evidence ${evidenceCollapsed ? 'is-collapsed' : ''}`}><div className="evidence-rail"><button className="evidence-toggle" onClick={() => setEvidenceCollapsed(false)} aria-label="展开讲义栏" aria-expanded="false" title="展开讲义栏"><Icon name="left" size={17} /></button><span className="evidence-rail-icon"><Icon name="file" size={18} /></span><span className="evidence-rail-label">讲义</span></div><div className="evidence-panel-content"><div className="evidence-section"><div className="evidence-title"><span className="evidence-icon"><Icon name="file" size={18} /></span><div><h2>暂无讲义匹配</h2><p>当前筛选没有题组</p></div><button className="evidence-toggle desktop-evidence-toggle" onClick={() => setEvidenceCollapsed(true)} aria-label="收起讲义栏" aria-expanded="true" title="收起讲义栏"><Icon name="right" size={17} /></button></div><div className="empty-evidence-body">切换章节或清除筛选后，这里会显示对应的{subjectConfig.label}讲义依据。</div></div></div></aside>
}

function SourceModal({ group, page, sourceName, onClose }) {
  return <div className="modal-backdrop" onClick={onClose}><div className="source-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><span>原题页</span><h2>{group.topic} · 第 {group.page} 页</h2></div><button className="icon-button" onClick={onClose} aria-label="关闭"><Icon name="close" size={20} /></button></div><div className="modal-image-wrap"><img src={assetPath(page?.image)} alt={`原题页 ${group.page}`} /></div><div className="modal-footer"><span>图片来自“{sourceName}”</span><button className="primary-button" onClick={onClose}>返回题组 <Icon name="arrow" size={16} /></button></div></div></div>
}

function LectureEvidenceModal({ evidence, onClose, contextLabel = '本题组对应的讲义原页' }) {
  return <div className="modal-backdrop" onClick={onClose}><div className="source-modal" role="dialog" aria-modal="true" aria-label="对应讲义页" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><span>对应讲义页</span><h2>{evidence.title}</h2></div><button className="icon-button" onClick={onClose} aria-label="关闭讲义原页"><Icon name="close" size={20} /></button></div><div className="modal-image-wrap lecture-modal-image"><img src={assetPath(evidence.image)} alt={`${evidence.title}原页`} /></div><div className="modal-footer"><span>{contextLabel}</span><button className="primary-button" onClick={onClose}>返回题组 <Icon name="arrow" size={16} /></button></div></div></div>
}

export default App
