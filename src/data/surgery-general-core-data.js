const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ①②③④⑤⑥⑦⑧⑨⑩'

const lectureMeta = {
  30: { id: 'lecture-30', title: '第30讲 · 输血' },
  31: { id: 'lecture-31', title: '第31讲 · 体液失衡' },
  32: { id: 'lecture-32', title: '第32讲 · 营养代谢' },
  33: { id: 'lecture-33', title: '第33讲 · 烧伤' },
}

function stableHash(value) {
  let hash = 2166136261
  for (const character of value) {
    hash ^= character.codePointAt(0)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function shuffledSourceKeys(id, size) {
  const original = [...LETTERS.slice(0, size)]
  const shuffled = [...original]
  let state = stableHash(id)
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    const swapIndex = state % (index + 1)
    ;[shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]]
  }
  if (shuffled.every((key, index) => key === original[index]) && shuffled.length > 1) {
    shuffled.push(shuffled.shift())
  }
  return shuffled
}

function evidence(lectureNumber, page, description) {
  const lecture = lectureMeta[lectureNumber]
  return {
    lectureId: lecture.id,
    page,
    image: `surgery/lecture-pages/lecture-${lectureNumber}-page-${String(page).padStart(2, '0')}.webp`,
    title: `${lecture.title}第${page}页`,
    description,
  }
}

function choiceGroup({ id, title, lecture, page, options, stems, answerRevision }) {
  if (options.length > LETTERS.length) throw new Error(`${id}: option pool exceeds supported keys`)
  const sourceKeys = [...LETTERS.slice(0, options.length)]
  const order = shuffledSourceKeys(id, options.length)
  const currentBySource = Object.fromEntries(order.map((sourceKey, index) => [sourceKey, LETTERS[index]]))
  const normalizedOptions = order.map((sourceKey, index) => ({
    key: LETTERS[index],
    label: options[sourceKeys.indexOf(sourceKey)],
    sourceText: `${sourceKey}. ${options[sourceKeys.indexOf(sourceKey)]}`,
    ocrScore: 1,
    sourceKey,
  }))
  const normalizedStems = stems.map(([text, answer, details = {}]) => {
    if (answer.some(key => !sourceKeys.includes(key))) throw new Error(`${id}: unknown answer key`)
    const remapped = answer.map((sourceKey) => currentBySource[sourceKey])
    return {
      text,
      answer: remapped,
      answerDisplay: remapped.join('、'),
      answerMode: remapped.length > 1 ? '多选' : '单选',
      sourceText: `${text} ${answer.join('、')}`,
      ocrScore: 1,
      ...details,
    }
  })
  const lectureEvidence = evidence(lecture, page, `本题组已按《核心精讲·${title.split('·')[0]}》对应页逐项复核。`)
  return {
    id,
    page: 0,
    title,
    kind: 'B',
    kindLabel: 'B型题',
    options: normalizedOptions,
    stems: normalizedStems,
    sourceText: [title, ...options, ...stems.map(([text]) => text)].join('；'),
    reviewState: '已完成结构校对',
    reviewIssues: [],
    reviewNotes: [],
    topic: '外科总论',
    hideSource: true,
    lectureIds: [lectureEvidence.lectureId],
    lectureEvidence,
    optionShuffleVersion: 1,
    optionOriginalOrder: sourceKeys,
    ...(answerRevision ? { answerRevision } : {}),
  }
}

function fillGroup({ id, title, lecture, page, stems, note, inputMode = 'decimal', answerRevision }) {
  const lectureEvidence = evidence(lecture, page, `本题组数字与公式已按《核心精讲·${title.split('·')[0]}》对应页逐项复核。`)
  return {
    id,
    page: 0,
    title,
    kind: 'FILL',
    kindLabel: '填空题',
    options: [],
    stems: stems.map(([text, answer]) => ({
      text,
      answer,
      answerDisplay: answer.join('；'),
      answerMode: '填空',
      blankLabels: answer.map((_, index) => `第${index + 1}空`),
      inputMode,
      sourceText: text,
      ocrScore: 1,
    })),
    sourceText: [title, ...stems.map(([text]) => text)].join('；'),
    reviewState: '已完成结构校对',
    ...(answerRevision ? { answerRevision } : {}),
    reviewIssues: [],
    reviewNotes: note ? [{ title: '题型规范化', body: note }] : [],
    topic: '外科总论',
    hideSource: true,
    lectureIds: [lectureEvidence.lectureId],
    lectureEvidence,
  }
}

const groups = [
  choiceGroup({
    id: 'surgery-general-core-t01', title: '输血·输血不良反应', lecture: 30, page: 1,
    options: [
      '输血过快过多，急性肺水肿',
      '重者肾上腺素＋糖皮质激素',
      '瘙痒、荨麻疹、会厌水肿、支气管痉挛、休克，多无发热',
      '最严重',
      '淋巴细胞攻击免疫缺陷受血者，全血细胞减少',
      '延迟性反应可在输血后1～2周出现',
      '最常见',
      '抗休克、肝素、NaHCO₃；有尿利尿，少尿、无尿或高钾血症时血液透析',
      '寒战高热、腰痛、呼吸困难、血压下降、黄疸、Hb尿、急性肾衰',
      '多次输血、经产妇；免疫反应；血压多正常',
      '代谢性碱中毒、高血钾、低血钙、低体温、凝血异常',
    ],
    stems: [
      ['发热', ['G', 'J']], ['溶血', ['D', 'F', 'H', 'I']], ['过敏', ['B', 'C']],
      ['循环超负荷', ['A']], ['移植物抗宿主病（GVHD）', ['E']], ['大量输血', ['K']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-t02', title: '输血·自体输血', lecture: 30, page: 1,
    options: [
      '间隔≥3天', '采血＜10%', '肝破裂', '异位妊娠破裂', '胸腹腔开放性损伤＞4小时',
      '择期手术前1个月开始采血，直到术前3天', '先采的血后输、后采的血先输', '外伤性脾破裂', 'HCT≥30%',
    ],
    stems: [['回收式', ['D', 'H']], ['稀释式', ['G']], ['预存式', ['A', 'B', 'F', 'I']], ['禁忌证', ['E']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-t03', title: '输血·失血量与补充血容量', lecture: 30, page: 2,
    options: ['晶体液、胶体液', '晶体液、胶体液、1/2浓缩红、1/2全血', '晶体液、胶体液、浓缩红', '不输血'],
    stems: [['失血量＜10%', ['D']], ['失血量10%～20%', ['A']], ['失血量20%～30%', ['C']], ['失血量＞30%', ['B']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-t04', title: '输血·血制品选择', lecture: 30, page: 2,
    options: ['白血病', '多次输血', '纤维蛋白原缺乏症', '地中海贫血', '甲型血友病', '再生障碍性贫血', '心功能不全', '肾功能不全', '准备移植者', '经产妇', 'IgA低下', '肝疾病伴凝血障碍'],
    stems: [
      ['浓缩红细胞', ['G']],
      ['洗涤红细胞', ['B', 'H', 'J', 'K']],
      ['少白或去白红细胞', ['A', 'B', 'D', 'F', 'J']],
      ['辐照红细胞', ['A', 'I']],
      ['冰冻血浆或冷沉淀的适用情形', ['C', 'E', 'L'], {
        explanation: '按第30讲第2页，肝疾病伴凝血障碍对应冰冻血浆；纤维蛋白原缺乏症、甲型血友病列在冷沉淀下。这里合并作答，不表示两种制品需要同时使用。',
      }],
    ],
    answerRevision: 'transfusion-plasma-cryo-combined-20261107',
  }),
  fillGroup({
    id: 'surgery-general-core-t05', title: '输血·数字挖空', lecture: 30, page: 2,
    stems: [
      ['Hb＞____ g/L一般不输血；Hb＜____ g/L输浓缩红细胞；____～____ g/L根据情况决定。', ['100', '70', '70', '100']],
      ['失血量＜10%约为____ ml；20%～30%约为____～____ ml；＞30%约为＞____ ml。', ['500', '1000', '1500', '1500']],
      ['预存式自体输血：HCT≥____%，采血＜____%，间隔≥____天。', ['30', '10', '3']],
    ],
  }),

  choiceGroup({
    id: 'surgery-general-core-f01', title: '体液失衡·水钠失衡', lecture: 31, page: 1,
    options: [
      'ADH升高，细胞内液明显减少', '相当于血液浓缩', '红细胞、Hb、HCT降低',
      '休克时同等渗性脱水；无休克时按缺钠公式补钠', '尿比重升高',
      '急性；短期体液丧失达体重5%可出现血容量不足', '5%葡萄糖',
      '慢性；初期尿量增加、后期尿量减少', '晚期食管癌饮水困难',
      '血钠135～150 mmol/L，血浆渗透压280～310 mOsm/L',
      '血钠＞150 mmol/L，血浆渗透压＞310 mOsm/L', '大面积烧伤暴露疗法',
      '组织间液明显减少', '首选平衡盐溶液，次选等渗盐水', '尿比重降低',
      '血钠＜130 mmol/L、高容量性低钠血症、低渗，血液被稀释', '大量出汗', '甘露醇、呋塞米',
      '血钠＜135 mmol/L，血浆渗透压＜280 mOsm/L',
    ],
    stems: [['等渗性脱水', ['B', 'E', 'F', 'J', 'N']], ['低渗性脱水', ['D', 'H', 'M', 'O', 'S']], ['高渗性脱水', ['A', 'E', 'G', 'I', 'K', 'L', 'Q']], ['水中毒', ['C', 'P', 'R']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-f02', title: '体液失衡·高钾血症与低钾血症', lecture: 31, page: 2,
    options: [
      '高尖T波', '肾衰', '醛固酮不足（如ACEI或ARB相关）', '胰岛素',
      '肌无力最早，先四肢后躯干和呼吸肌；腱反射降低', '酸中毒',
      'ST段和T波低平、U波明显、QT间期延长', '碱中毒', '呕吐', '腹泻',
      '代谢性酸中毒、反常性碱性尿', '溶血', '排钾利尿剂', '心搏骤停或室颤最危险',
      '醛固酮过多', '大量输血', '挤压综合征', '甲亢', '胃肠减压',
      '肠麻痹、腹胀、呕吐', '代谢性碱中毒、反常性酸性尿', '保钾利尿剂', '嗜铬细胞瘤',
    ],
    stems: [['高钾血症', ['A', 'B', 'C', 'F', 'K', 'L', 'N', 'P', 'Q', 'V']], ['低钾血症', ['D', 'E', 'G', 'H', 'I', 'J', 'M', 'O', 'R', 'S', 'T', 'U', 'W']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-f03a', title: '体液失衡·高低钾治疗', lecture: 31, page: 3,
    options: [
      '5% NaHCO₃', '浓度＜40 mmol/L', '速度＜20 mmol/h', '尿量＞40 ml/h补钾',
      '立即停用一切含钾药物', '胰岛素＋葡萄糖', '补钾40～80 mmol/d（KCl 3～6 g/d）',
      '排钾利尿剂、阳离子交换树脂、透析', '补钾后未改善考虑低镁血症',
      '首选10%葡萄糖酸钙，拮抗K⁺对心脏的毒性',
    ],
    stems: [['高钾血症', ['A', 'E', 'F', 'H', 'J']], ['静脉补KCl', ['B', 'C', 'D', 'G', 'I']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-f03b', title: '体液失衡·DKA补钾判断', lecture: 31, page: 3,
    options: ['暂缓补钾', '立即补钾', '暂缓补钾，待尿量增加后补钾'],
    stems: [
      ['DKA：K⁺＜3.5 mmol/L', ['B']], ['DKA：K⁺正常且尿量＞40 ml/h', ['B']],
      ['DKA：K⁺正常且尿量＜30 ml/h', ['C']], ['DKA：K⁺＞5.5 mmol/L', ['A']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-f04a', title: '体液失衡·钙失衡', lecture: 31, page: 3,
    options: [
      '补充钙剂，可加服骨化三醇', '肾衰', '痉挛、抽搐', '呼吸困难', 'Trousseau征',
      '急性胰腺炎', 'ST段延长', '甲状旁腺功能减退', 'Chvostek征', '维生素D缺乏',
      '麻木、针刺感', '癔症（呼吸性碱中毒）', 'ST段缩短',
      '甲状旁腺功能亢进', '腱反射亢进', '小肠瘘', '骨肿瘤导致骨质破坏',
    ],
    stems: [['高钙血症', ['M', 'N', 'Q']], ['低钙血症', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'O', 'P']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-f04b', title: '体液失衡·酸碱调节系统', lecture: 31, page: 3,
    options: ['调节PaCO₂', 'NaHCO₃/H₂CO₃、KHb/Hb等', '重吸收HCO₃⁻、分泌H⁺、分泌NH₃/NH₄⁺', 'H⁺-K⁺交换等'],
    stems: [['体液缓冲系统', ['B']], ['肺', ['A']], ['肾', ['C']], ['组织细胞', ['D']]],
  }),
  fillGroup({
    id: 'surgery-general-core-f05', title: '体液失衡·数字挖空', lecture: 31, page: 4,
    stems: [
      ['血钠正常范围____～____ mmol/L，平均____ mmol/L。', ['135', '150', '142']],
      ['血浆渗透压正常范围____～____ mOsm/L。', ['280', '310']],
      ['高钾血症K⁺＞____ mmol/L；低钾血症K⁺＜____ mmol/L。', ['5.5', '3.5']],
      ['低渗性脱水：轻度Na⁺ ____～____，中度____～____，重度＜____ mmol/L。', ['130', '135', '120', '130', '120']],
      ['高钙血症Ca²⁺＞____ mmol/L；低钙血症Ca²⁺＜____ mmol/L。', ['2.75', '2.25']],
      ['17 mmol Na⁺相当于____ g NaCl；13.4 mmol K⁺相当于____ g KCl。', ['1', '1']],
    ],
  }),

  choiceGroup({
    id: 'surgery-general-core-n01a', title: '营养代谢·营养评价', lecture: 32, page: 1,
    options: [
      'BMI＜18.5为营养不良，24～28为超重，≥28为肥胖',
      '负氮平衡即摄入＜排出，蛋白质分解＞合成', '总淋巴细胞计数＜1.8×10⁹/L为营养不良',
      '体重丢失＞10%或3个月内丢失＞5%为营养不良',
      'BMI≥30者能量摄入为正常25～30 kcal/kg的70%～80%', '肱三头肌皮褶厚度、上臂围、握力',
      '白蛋白；更敏感者为前白蛋白、转铁蛋白、视黄醇结合蛋白',
    ],
    stems: [['体重改变', ['D']], ['BMI', ['A', 'E']], ['肌肉和脂肪', ['F']], ['血浆蛋白', ['G']], ['氮平衡', ['B']], ['总淋巴细胞计数', ['C']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-n01b', title: '营养代谢·应激代谢', lecture: 32, page: 1,
    options: ['蛋白质和脂肪分解加强、糖异生等致血糖增高', '静息能量消耗增加50%～100%', '静息能量消耗增加20%～30%', '静息能量消耗增加10%'],
    stems: [['手术', ['D']], ['严重创伤', ['C']], ['多发骨折', ['C']], ['感染', ['C']], ['大面积烧伤', ['B']], ['应激', ['A']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-n02a', title: '营养代谢·肠内营养输入途径', lecture: 32, page: 1,
    options: ['预计肠内营养＜2周', '预计肠内营养＞2周'],
    stems: [
      ['口服', ['A']], ['鼻胃管或鼻十二指肠管', ['A']], ['鼻空肠管', ['A']],
      ['胃造口', ['B']], ['空肠造口', ['B']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-n03a', title: '营养代谢·肠内营养制剂', lecture: 32, page: 1,
    options: [
      '等渗、口感好、最常用',
      '以氨基酸、多肽等为主，残渣少，无需消化即可吸收且不含乳糖',
      '适用于回肠肠瘘', '适用于短肠综合征', '适用于胰腺炎',
      '适合有特殊营养需求者',
      '糖尿病：减少葡萄糖、增加脂肪乳剂量',
      '慢性肾衰：低磷、低蛋白，不需限制糖',
    ],
    stems: [
      ['非要素型或整蛋白型', ['A']],
      ['要素型', ['B', 'C', 'D', 'E']],
      ['组件型', ['F']],
      ['疾病专用型', ['G', 'H']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-n02b', title: '营养代谢·肠外营养适应证与输入途径', lecture: 32, page: 2,
    options: [
      '1周以上不能进食、胃肠道功能障碍或肠内营养无法达标',
      '高位小肠瘘', '短肠综合征', '重症胰腺炎', '急性肾衰',
      '严重感染', '严重烧伤', '溃疡性结肠炎长期腹泻',
      '恶性肿瘤放化疗期间严重呕吐',
      '甲亢术后饮水呛咳', '脑外伤昏迷', '幽门梗阻',
      '上肢末梢静脉输注',
      'PICC、锁骨下静脉或颈内静脉输注',
      '完全肠外营养（TPN）',
      '尽早改为肠内营养，采用鼻空肠管或空肠造口',
    ],
    stems: [
      ['肠外营养适应证', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']],
      ['不需要肠外营养', ['J', 'K', 'L']],
      ['肠外营养＜2周', ['M']],
      ['肠外营养＞2周', ['N']],
      ['重症胰腺炎禁食期', ['O']],
      ['重症胰腺炎肠功能恢复后', ['P']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-n03b', title: '营养代谢·肠外营养成分与配制', lecture: 32, page: 2,
    options: ['谷氨酰胺', '支链氨基酸', '营养液配制要求'],
    stems: [
      ['营养肠黏膜细胞', ['A']],
      ['肝功能不全时加用', ['B']],
      ['不允许在营养液中添加其他药物', ['C']],
    ],
  }),
  choiceGroup({
    id: 'surgery-general-core-n04a', title: '营养代谢·肠内营养并发症', lecture: 32, page: 2,
    options: ['输注过快', '吸入性肺炎', '腹胀、腹泻'],
    stems: [['最常见的并发症', ['C']], ['最严重的并发症', ['B']], ['腹胀、腹泻的常见诱因', ['A']]],
    answerRevision: 'en-complication-matching-20261027',
  }),
  choiceGroup({
    id: 'surgery-general-core-n04b', title: '营养代谢·肠外营养并发症', lecture: 32, page: 2,
    options: [
      '气胸', '空气栓塞', '血管损伤', '神经损伤',
      '立即拔管', '抗生素治疗', '导管尖端细菌培养',
      '伤口愈合延迟', '皮肤干燥脱屑', '脱发',
      '葡萄糖耐受下降', '低磷血症', '低钾血症', '低镁血症', '维生素缺乏', '心衰',
      '肝脂肪浸润', '胆汁淤积', '急性非结石性胆囊炎',
      '肠内缺乏食物刺激', '胆囊收缩素分泌减少', '肠黏膜萎缩', '肠黏膜通透性增加',
      '肠道细菌和内毒素移位', '能量供给过高，尤其葡萄糖过负荷', '体内谷氨酰胺大量消耗',
      '骨钙丢失、骨质疏松', '四肢关节疼痛', '骨折', '血钙升高', '尿钙升高', '碱性磷酸酶（ALP）升高',
    ],
    stems: [
      ['中心静脉置管：非感染性并发症', ['A', 'B', 'C', 'D'], {
        explanation: '按讲义，置管过程中气胸最常见、空气栓塞最严重，还可损伤血管和神经。导管相关感染及其处理另列下一小题。',
      }],
      ['中心静脉导管相关感染：处理', ['E', 'F', 'G'], {
        explanation: '本题按讲义列出的处理措施作答：立即拔管、抗生素治疗，并将导管尖端送细菌培养。',
      }],
      ['必需脂肪酸缺乏：表现', ['H', 'I', 'J']],
      ['再喂养综合征：代谢异常与表现', ['K', 'L', 'M', 'N', 'O', 'P'], {
        explanation: '讲义以低磷为标志，同时列出低钾、低镁、维生素缺乏、葡萄糖耐受下降及心衰。不能漏掉葡萄糖耐受下降，也不要与长期肠外营养代谢性骨病的钙改变混淆。',
      }],
      ['长期肠外营养：肝胆损害及发生机制', ['Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'], {
        explanation: '肝脂肪浸润、胆汁淤积及急性非结石性胆囊炎属于表现；肠内刺激减少、胆囊收缩素减少、肠黏膜屏障改变、细菌和内毒素移位、葡萄糖过负荷及谷氨酰胺消耗属于相关机制。',
      }],
      ['长期肠外营养：代谢性骨病的表现与化验', ['①', '②', '③', '④', '⑤', '⑥'], {
        explanation: '按讲义第3页：骨钙丢失、骨质疏松，四肢关节疼痛甚至骨折；血钙、尿钙及碱性磷酸酶升高。',
      }],
    ],
    answerRevision: 'pn-complications-complete-20261028',
  }),
  fillGroup({
    id: 'surgery-general-core-n05', title: '营养代谢·数字挖空', lecture: 32, page: 2,
    stems: [
      ['蛋白质平均含氮量____%。', ['16']],
      ['EN：＜____周可口服或置管，＞____周行胃造口或空肠造口。', ['2', '2']],
      ['PN：＜____周采用周围静脉，＞____周采用中心静脉。', ['2', '2']],
      ['葡萄糖____～____ g/kg/d；严重应激____～____ g/kg/d；供能占总热量____%～____%。', ['3', '3.5', '2', '3', '50', '60']],
      ['甘油三酯____～____ g/kg/d，供能占总热量____%～____%。', ['0.7', '1.3', '30', '40']],
      ['氨基酸____～____ g/kg/d；糖脂比____∶____，应激时____∶____；氮和热量比1∶（____～____）。', ['1.2', '1.5', '1', '1', '1', '2', '150', '200']],
    ],
  }),

  choiceGroup({
    id: 'surgery-general-core-b01', title: '烧伤·烧伤深度', lecture: 33, page: 2,
    options: [
      '湿润、红白相间，可有小水疱', '红斑状、干燥、无水疱', '温度降低、痛觉迟钝，拔毛微痛',
      '发凉、痛觉消失，拔毛不痛且易拔除', '需植皮，瘢痕增生', '部分表皮生发层或真皮乳头层',
      '部分真皮网状层', '湿润、红润，大小不一的水疱', '3～4周愈合，瘢痕增生',
      '皮肤全层，甚至皮下脂肪、肌肉、骨骼、内脏', '表皮浅层',
      '蜡白焦黄、炭化、树枝状栓塞血管，干燥、无水疱', '疼痛显著、感觉过敏，拔毛痛',
      '10天～2周愈合', '＜1周愈合', '烧灼感、拔毛剧痛',
    ],
    stems: [['Ⅰ度烧伤', ['B', 'K', 'O', 'P']], ['浅Ⅱ度烧伤', ['F', 'H', 'M', 'N']], ['深Ⅱ度烧伤', ['A', 'C', 'G', 'I']], ['Ⅲ度烧伤', ['D', 'E', 'J', 'L']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-b02', title: '烧伤·烧伤严重程度', lecture: 33, page: 2,
    options: ['Ⅲ度烧伤面积＜10%', '烧伤总面积31%～50%', '可有休克', '可有复合伤', 'Ⅱ度烧伤面积＜10%', 'Ⅲ度烧伤面积11%～20%', '烧伤总面积＞50%', '可有吸入性损伤', 'Ⅲ度烧伤面积＞20%', 'Ⅱ度烧伤面积11%～30%', '不计入烧伤严重程度和补液公式，创面无需特殊处理'],
    stems: [['轻度', ['E']], ['中度', ['A', 'J']], ['重度', ['B', 'C', 'D', 'F', 'H']], ['特重度', ['C', 'D', 'G', 'H', 'I']], ['Ⅰ度烧伤', ['K']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-b03', title: '烧伤·分期与治疗', lecture: 33, page: 2,
    options: ['感染性休克是主要死因', '伤后2～3 h最为急剧、6～8 h达高峰，一般持续24～48 h', '抗生素、TAT；感染控制后及时停药', '补液是首选主要治疗措施', '可致低血容量性休克', '早期削痂、切痂、植皮是防治全身感染的关键措施', '先快后慢'],
    stems: [['体液渗出与回吸收期', ['B', 'D', 'E', 'G']], ['急性感染期', ['A', 'C', 'F']]],
    answerRevision: 'burn-phase-no-self-answer-20261027',
  }),
  choiceGroup({
    id: 'surgery-general-core-b04a', title: '烧伤·现场急救与转送', lecture: 33, page: 3,
    options: ['建立静脉输液通道；否则口服含盐饮料', '避免用有色药物涂抹', '疼痛剧烈可酌情用哌替啶、地西泮', '减轻疼痛最好采用冷疗'],
    stems: [['转送', ['A']], ['急救现场', ['B', 'C', 'D']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-b04b', title: '烧伤·创面处理', lecture: 33, page: 3,
    options: ['外层用吸水敷料', '保留水疱皮，较大水疱抽去水疱液', '包扎范围超出创缘3～5 cm', '去除水疱皮', '会阴、Ⅲ度创面等采用暴露疗法', '苯扎溴铵或氯己定消毒，不能用酒精', '敷料内层用油质纱布，可加碘伏和磺胺嘧啶银'],
    stems: [['浅Ⅱ度创面', ['B']], ['深Ⅱ度创面', ['D']], ['包扎', ['A', 'C', 'G']], ['暴露疗法', ['E']], ['创面消毒', ['F']]],
  }),
  choiceGroup({
    id: 'surgery-general-core-b04c', title: '烧伤·吸入性损伤', lecture: 33, page: 3,
    options: ['纤维支气管镜', '面、颈、前胸部尤其口鼻烧伤', '密闭环境', '刺激性咳嗽', '吞咽困难或疼痛', '声嘶', '哮鸣音', '及早气管切开', '痰中有炭屑', '呼吸困难'],
    stems: [
      ['提示吸入性损伤的受伤环境与部位', ['B', 'C']],
      ['提示吸入性损伤的临床表现', ['D', 'E', 'F', 'G', 'I', 'J']],
      ['最直接、准确的检查', ['A']],
      ['讲义列出的早期气道处理', ['H']],
    ],
    answerRevision: 'inhalation-injury-matching-20261027',
  }),
  choiceGroup({
    id: 'surgery-general-core-b05a', title: '烧伤·应激性溃疡', lecture: 33, page: 1,
    options: ['严重烧伤', '好发于胃底、胃体', '严重脑部疾病'],
    stems: [['Curling溃疡', ['A', 'B']], ['Cushing溃疡', ['B', 'C']]],
  }),
  fillGroup({
    id: 'surgery-general-core-b06', title: '烧伤·数字挖空', lecture: 33, page: 2,
    note: '原文第1题只写出公式并把答案标为“公式记忆”，无法实际填写；已按讲义将公式中的固定数字9和46设为两个空。',
    stems: [
      ['12岁以下：头面颈部面积＝（____＋12－年龄）%；双下肢面积＝（____－12＋年龄）%。', ['9', '46']],
      ['成人头面颈____%，双上肢____%，前后躯干（不含会阴）____%，双下肢____%，会阴____%。', ['9', '18', '26', '46', '1']],
      ['第1个24 h：每1%的Ⅱ、Ⅲ度烧伤面积、每kg体重补晶胶液____ ml，另加葡萄糖溶液____ ml。', ['1.5', '2000']],
      ['第1个24 h晶体∶胶体＝____∶____；广泛深度烧伤时____∶____。', ['2', '1', '1', '1']],
      ['第1个24 h前____ h输入补液总量的一半，后____ h输入另一半。', ['8', '16']],
      ['第2个24 h：晶胶液减半＋葡萄糖溶液____ ml。', ['2000']],
      ['包扎范围超出创缘____～____ cm。', ['3', '5']],
    ],
    answerRevision: 'burn-area-no-double-count-20261027',
  }),
]

const surgeryGeneralCoreContent = {
  topics: ['外科总论'],
  groups,
}

export default surgeryGeneralCoreContent
