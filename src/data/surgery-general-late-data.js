const KEYS = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '①', '②', '③', '④', '⑤', '⑥', '⑦']

const lectureMeta = {
  34: { id: 'lecture-34', title: '第34讲 · 感染' },
  37: { id: 'lecture-37', title: '第37讲 · 休克' },
  38: { id: 'lecture-38', title: '第38讲 · 其它外科总论' },
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
  const original = KEYS.slice(0, size)
  const shuffled = [...original]
  let state = stableHash(id)
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    const swapIndex = state % (index + 1)
    ;[shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]]
  }
  if (shuffled.every((key, index) => key === original[index]) && shuffled.length > 1) shuffled.push(shuffled.shift())
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

function choiceGroup({ id, title, lecture, page, options, stems, note }) {
  const sourceKeys = KEYS.slice(0, options.length)
  const order = shuffledSourceKeys(id, options.length)
  const currentBySource = Object.fromEntries(order.map((sourceKey, index) => [sourceKey, KEYS[index]]))
  const normalizedOptions = order.map((sourceKey, index) => ({
    key: KEYS[index],
    label: options[sourceKeys.indexOf(sourceKey)],
    sourceText: `${sourceKey}. ${options[sourceKeys.indexOf(sourceKey)]}`,
    ocrScore: 1,
    sourceKey,
  }))
  const normalizedStems = stems.map(([text, answer]) => {
    const remapped = answer.map((sourceKey) => currentBySource[sourceKey])
    return {
      text,
      answer: remapped,
      answerDisplay: remapped.join('、'),
      answerMode: remapped.length > 1 ? '多选' : '单选',
      sourceText: `${text} ${answer.join('、')}`,
      ocrScore: 1,
    }
  })
  const lectureEvidence = evidence(lecture, page, `题干、选项与答案已按《核心精讲·${title.split('·')[0]}》对应页逐项复核。`)
  return {
    id, page: 0, title, kind: 'B', kindLabel: 'B型题', options: normalizedOptions, stems: normalizedStems,
    sourceText: [title, ...options, ...stems.map(([text]) => text)].join('；'),
    reviewState: '已完成结构校对', reviewIssues: [],
    reviewNotes: note ? [{ title: '讲义核对修正', body: note }] : [],
    topic: '外科总论', hideSource: true, lectureIds: [lectureEvidence.lectureId], lectureEvidence,
    optionShuffleVersion: 1, optionOriginalOrder: sourceKeys,
  }
}

function fillGroup({ id, title, lecture, page, stems }) {
  const lectureEvidence = evidence(lecture, page, `数字与单位已按《核心精讲·${title.split('·')[0]}》对应页逐项复核。`)
  return {
    id, page: 0, title, kind: 'FILL', kindLabel: '填空题', options: [],
    stems: stems.map(([text, answer]) => ({
      text, answer, answerDisplay: answer.join('；'), answerMode: '填空',
      blankLabels: answer.map((_, index) => `第${index + 1}空`), inputMode: 'decimal', sourceText: text, ocrScore: 1,
    })),
    sourceText: [title, ...stems.map(([text]) => text)].join('；'), reviewState: '已完成结构校对',
    reviewIssues: [], reviewNotes: [], topic: '外科总论', hideSource: true,
    lectureIds: [lectureEvidence.lectureId], lectureEvidence,
  }
}

export const surgeryGeneralInfectionGroups = [
  choiceGroup({
    id: 'surgery-general-infection-01', title: '感染·感染类型与抗菌药原则', lecture: 34, page: 1,
    options: ['破伤风','表浅且局限的疖','感染性心内膜炎','病因未明的严重感染','不敏感菌趁机生长繁殖','去除感染灶','手术＞3 h或失血＞1500 ml，术中可给第二剂','通畅引流','总预防用药＜24～48 h','继发性腹膜炎','念珠菌感染','尿路感染','气性坏疽','两性霉素B＋氟胞嘧啶治疗真菌感染','结核','免疫缺陷者的严重感染','脓毒症','长期使用广谱抗生素','院内感染','麻醉开始或术前0.5～2 h首次给药'],
    stems: [['特异性感染',['A','K','M','O']],['条件／机会感染',['S']],['二重感染／菌群交替',['E','K','R']],['无需抗生素',['B']],['外科治疗基本原则',['F','H']],['预防性用药',['G','I','T']],['联合用药',['C','D','J','L','N','O','P','Q']]],
  }),
  choiceGroup({
    id: 'surgery-general-infection-02', title: '感染·浅部组织感染', lecture: 34, page: 2,
    options: ['累及皮肤淋巴管网','小儿多见，早期切开减压防窒息','反复发作可致象皮肿','好发于下肢、面部','危险三角内严禁挤压和切开','乙型溶血性链球菌','化脓性炎','多合并糖尿病','累及疏松结缔组织','可致海绵状静脉窦炎','金黄色葡萄球菌','非化脓性炎','症状消失后继续用药','产生透明质酸酶，感染弥漫','厌氧菌多见，可有捻发感','好发于项背部','边界不清','出现波动感后十字切口引流，切口超过边缘、深达筋膜','不切开引流','多个相邻脓点','产生凝血酶，感染较局限','1个脓点','出现波动感后切开引流','边界清楚'],
    stems: [['疖',['E','J','K','U','V']],['痈',['H','K','P','R','T','U']],['蜂窝织炎',['F','G','I','N','Q','W']],['丹毒',['A','C','D','F','L','M','N','S','X']],['颌下蜂窝织炎',['B']],['产气性皮下蜂窝织炎',['O']],['新生儿皮下坏疽',['K']]],
    note: '原文把“危险三角内严禁挤压和切开、可致海绵状静脉窦炎”误归入痈；讲义明确属于疖，已据此纠正答案。',
  }),
  choiceGroup({
    id: 'surgery-general-infection-03', title: '感染·手部化脓性感染', lecture: 34, page: 4,
    options: ['1、2指活动受限，不能对掌','严禁切开肿胀的手背','针刺样疼痛→剧烈跳痛→疼痛减轻','肿痛明显及时切开，否则可致末节指骨缺血坏死、骨髓炎','3、4、5指活动受限','切口近端不及掌横纹','甲沟旁纵行切开引流','鱼际肿胀','不作鱼口状切口','末节指侧面纵行切口','指神经阻滞麻醉不加肾上腺素','可形成U形脓肿','1、5指分别蔓延至桡、尺侧滑囊','2指可蔓延至鱼际间隙','初发时悬吊前臂、平放患手','掌心凹消失／掌心隆起','肿痛明显及时切开，否则可致肌腱缺血坏死','术后抬高患手、固定在功能位','3、4指可蔓延至掌中间隙','切口近端距腕横纹至少1.5 cm'],
    stems: [['甲沟炎',['G','L']],['脓性指头炎',['C','D','I','J','K','O']],['掌中间隙感染',['B','E','F','P']],['鱼际间隙感染',['A','B','F','H']],['化脓性腱鞘炎',['M','N','Q','R','S']],['化脓性滑囊炎',['T']]],
  }),
  choiceGroup({
    id: 'surgery-general-infection-04', title: '感染·脓毒症', lecture: 34, page: 4,
    options: ['多次血培养阴性考虑厌氧菌、真菌','金黄色葡萄球菌','真菌','迁徙／转移性脓肿','心肌炎','易发生冷休克','导管内采样送检','皮疹','脓液／穿刺液培养','休克者同时补充血容量','处理原发感染灶','G⁻杆菌','寒战发热时进行血培养','寒战高热','多合并需氧菌感染','结膜瘀斑','视网膜灶性絮样斑','血压、体温、WBC三低','1 h内静脉用抗生素','恶臭','厌氧菌'],
    stems: [['G⁻杆菌',['F','L','R']],['金黄色葡萄球菌',['B','D','E','H','N']],['厌氧菌',['O','T','U']],['真菌',['C','P','Q']],['检查',['A','G','I','M']],['治疗',['J','K','S']]],
  }),
  choiceGroup({
    id: 'surgery-general-infection-05', title: '感染·破伤风与气性坏疽', lecture: 34, page: 5,
    options: ['清除变色、不收缩、不出血的肌肉','破伤风梭菌／杆菌','早期彻底清创切开引流','TAT必须皮试','大理石样斑纹','涂片见G⁺粗大杆菌','氨基糖苷类抗生素无效','高锰酸钾处理伤口','伤口黑色、恶臭','捻发感、皮下气肿','缺氧时释放痉挛毒素','整个肢体广泛感染可截肢','重症尽早气管切开防窒息','早期大剂量青霉素','缺氧时释放α毒素／卵磷脂酶','外伤史＋临床表现诊断','梭状芽胞杆菌','溶血性黄疸、血红蛋白尿','TIG最佳，可中和游离毒素','甲硝唑','过氧化氢处理伤口'],
    stems: [['破伤风',['B','C','D','G','K','M','N','P','S','T','U']],['气性坏疽',['A','C','E','F','G','H','I','J','L','N','O','Q','R','T','U']]],
  }),
  fillGroup({
    id: 'surgery-general-infection-06', title: '感染·数字挖空', lecture: 34, page: 5,
    stems: [['亚急性感染病程为____周至____个月。',['3','2']],['预防性抗菌药首次给药：麻醉开始或术前____～____ h。',['0.5','2']],['手术＞____ h或失血＞____ ml，术中可给第二剂。',['3','1500']],['总预防用药＜____～____ h。',['24','48']],['化脓性滑囊炎切口近端距腕横纹至少____ cm。',['1.5']],['破伤风主动免疫基础后每隔____～____年强化一次。',['5','7']],['伤后类毒素抗原____ ml。',['0.5']]],
  }),
]

const shockGroups = [
  choiceGroup({
    id: 'surgery-general-shock-01', title: '休克·概述与微循环', lecture: 37, page: 1,
    options: ['补充血容量','只进不出','收缩期／代偿期／休克早期','扩张期／抑制期','组织灌注不足→氧供给不足和氧需求增加','衰竭期','可出现DIC','只出不进','DIC早期／高凝期用肝素抗凝','必要时输血','可联合人工胶体液','炎症介质释放','平衡盐等晶体液'],
    stems: [['本质',['E']],['特征',['L']],['首选治疗',['A','J','K','M']],['收缩期',['C','H']],['扩张期',['B','D']],['衰竭期',['F','G','I']]],
  }),
  choiceGroup({
    id: 'surgery-general-shock-02', title: '休克·休克分度', lecture: 37, page: 2,
    options: ['脉搏＞200次／分且弱','舒张压升高、脉压减小','收缩压90～70 mmHg、脉压减小','脉搏100～200次／分','收缩压＜70 mmHg','收缩压正常或稍升高','失血量20%～40%','失血量＜20%（＜800 ml）','失血量＞40%（＞1600 ml）','意识模糊、昏迷','尚清楚、表情淡漠'],
    stems: [['轻度',['B','F','H']],['中度',['C','D','G','K']],['重度',['A','E','I','J']]],
  }),
  choiceGroup({
    id: 'surgery-general-shock-03', title: '休克·监测指标', lecture: 37, page: 2,
    options: ['反映肺静脉、左心房、左心室功能状态','血压正常但少尿且尿比重低提示肾性肾衰','＞1～1.5提示休克','代表右心房、胸腔大静脉压力','脉率／收缩压','评估缺氧、酸中毒、无氧代谢程度及预后','尿量30 ml/h提示微循环改善、液体已补足','尿量＜25 ml/h且尿比重增加提示血容量不足／肾前性肾衰','＞2提示严重休克','0.5提示无休克','发现隐匿性休克'],
    stems: [['休克指数',['C','E','I','J']],['尿量',['B','G','H']],['胃肠道pH',['K']],['乳酸、碱剩余',['F']],['PAWP／PCWP',['A']],['CVP',['D']]],
  }),
  choiceGroup({
    id: 'surgery-general-shock-04', title: '休克·CVP与BP补液原则', lecture: 37, page: 3,
    options: ['强心、纠酸等','CVP↓、BP正常','CVP↓、BP↓','CVP↑、BP正常','适当补液','充分补液','CVP正常、BP↓','CVP↑、BP↓','补液后BP升高提示血容量不足','补液后CVP升高提示心功能不全','扩静脉'],
    stems: [['血容量严重不足',['C','F']],['血容量不足',['B','E']],['容量血管过度收缩',['D','K']],['心功能不全／血容量相对过多',['A','H']],['补液试验',['G','I','J']]],
  }),
  choiceGroup({
    id: 'surgery-general-shock-05', title: '休克·感染性休克', lecture: 37, page: 3,
    options: ['皮肤较温暖、干燥','尿量＜25 ml/h','泌尿系感染','呼吸＞20次／分或PaCO₂＜4.3 kPa','治疗感染灶／常需外科引流','绞窄性肠梗阻','一部分G⁺菌早期','纠酸','毛细血管充盈时间延长','重症胰腺炎','有效抗生素前提下早期大剂量短时间糖皮质激素','WBC＞12或＜4×10⁹/L，或未成熟白细胞＞10%','补充血容量','皮肤苍白、发绀、湿冷','多巴胺／多巴酚丁胺／去甲肾上腺素／山莨菪碱','外周血管收缩','继发性腹膜炎','脉压＜30 mmHg','体温＞38 ℃或＜36 ℃','心排血量下降','G⁻杆菌／内毒素为主','心率＞90次／分','低动力型／低排高阻型','脉搏细速','AOSC'],
    stems: [['常见病因',['C','F','J','Q','Y']],['冷休克',['B','I','N','P','R','T','U','W','X']],['暖休克',['A','G']],['SIRS',['D','L','S','V']],['治疗',['E','H','K','M','O']]],
  }),
  choiceGroup({
    id: 'surgery-general-shock-06', title: '休克·常考疾病的休克处理', lecture: 37, page: 5,
    options: ['手术探查止血','心包穿刺','同步电复律','补充血容量','手术同时补充血容量','PCI或溶栓','同时治疗感染灶','＜2 h PCI','正性肌力药','补充血容量→处理组织损伤→处理骨折','EVL＋生长抑素／奥曲肽，可考虑TIPS／急诊断流术','禁用硝酸酯类、利尿剂','rt-PA等溶栓→肝素等抗凝','立即穿刺抽气','PPI或联合胃镜','主动脉内球囊反搏IABP','起搏器','人工瓣膜置换术','急诊解除胆道梗阻降低压力'],
    stems: [['急性肺血栓栓塞：高危',['M']],['急性左心衰：SBP＜90 mmHg',['I']],['快速型心律失常：SBP＜90 mmHg',['C']],['严重缓慢型心律失常',['Q']],['急性二尖瓣关闭不全：SBP＜90 mmHg',['P']],['NSTE-ACS：极高危',['H','P']],['STEMI：SBP＜90 mmHg',['F','P']],['右室急性梗死',['D','L']],['心脏压塞',['B']],['感染性心内膜炎：瓣叶穿孔／瘘并心衰休克',['R']],['消化性溃疡上消化道出血：SBP＜90 mmHg',['D']],['食管胃底静脉曲张出血：SBP＜90 mmHg',['D']],['食管胃底静脉曲张出血：BP稳定',['K']],['感染性休克',['D','G']],['进行性血胸',['A','D']],['张力性气胸',['N']],['脾、肝损伤伴休克',['E']],['AOSC伴休克',['D','S']],['骨折伴休克',['J']],['消化性溃疡上消化道出血：BP稳定',['O']]],
  }),
  fillGroup({
    id: 'surgery-general-shock-07', title: '休克·数字挖空', lecture: 37, page: 3,
    stems: [['DIC：血小板＜____；凝血酶原时间延长＞____ s；纤维蛋白原＜____；破碎红细胞＞____%。',['80','3','1.5','2']],['休克指数____提示无休克；＞____～____提示休克；＞____提示严重休克。',['0.5','1','1.5','2']],['CVP正常值____～____ cmH₂O。',['5','10']],['尿量达____ ml/h提示微循环改善；＜____ ml/h且尿比重增高提示血容量不足。',['30','25']],['SIRS：体温＞____ ℃或＜____ ℃；心率＞____次／分；呼吸＞____次／分。',['38','36','90','20']],['SIRS：PaCO₂＜____ kPa（约____ mmHg）。',['4.3','32.29']]],
  }),
]

const otherGroups = [
  choiceGroup({
    id: 'surgery-general-other-01', title: '其它外科总论·灭菌方法', lecture: 38, page: 1,
    options: ['锐利器械','橡胶','油剂','环氧乙烷／过氧化氢低温等离子体／低温甲醛蒸汽','持续1小时','内镜','最常用，适合大多数物品','金属器械','玻璃','仪器','灭菌物品有效期2周','粉剂','导管','γ射线','戊二醛等浸泡10小时'],
    stems: [['高压蒸汽',['G','K']],['化学气体',['D','F','J','M']],['煮沸',['B','E','H','I']],['化学药液浸泡',['A','F','O']],['干热／火烧',['C','I','L']],['电离辐射',['N']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-02', title: '其它外科总论·手术区与特殊污染处理', lecture: 38, page: 1,
    options: ['由外周开始消毒','由中心向四周消毒','切口周围15 cm','肩部以下、腰部以上身前区至腋中线＋双侧手臂＋手术台面以上','重新洗手＋消毒＋更换手套','40%甲醛＋高锰酸钾熏蒸','乙肝','2000 mg/L有效氯浸泡1小时＋高压蒸汽灭菌','铜绿假单胞菌','开放性结核','气性坏疽'],
    stems: [['一般皮肤消毒',['B','C']],['感染区／肛门区',['A','C']],['无菌区域',['D']],['手套破损／接触有菌处',['E']],['手术室熏蒸',['F','I','K']],['器械特殊处理',['G','H','I','J']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-03', title: '其它外科总论·急性肝衰竭', lecture: 38, page: 1,
    options: ['肝臭','肝浊音界进行性缩小','乙肝','扑翼样震颤','PTA≤40%','肝性脑病','胆酶分离'],
    stems: [['我国最主要原因',['C']],['表现与化验',['A','B','D','E','F','G']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-04', title: '其它外科总论·创伤', lecture: 38, page: 1,
    options: ['加压包扎无法止血的四肢大出血','禁用细绳、电线','切除创缘皮肤1～2 mm','窒息','清创后不一期缝合','开放伤','闭合伤','盲管伤','休克','心跳呼吸骤停','贯通伤','清创后一期缝合','张力性气胸'],
    stems: [['按皮肤／黏膜完整性分类',['F','G']],['开放伤',['H','K']],['止血带',['A','B']],['开放伤清创',['C']],['规定时限内',['L']],['超过时限／火器伤／重污染',['E']],['优先抢救',['D','I','J','M']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-05', title: '其它外科总论·移植与微创', lecture: 38, page: 2,
    options: ['易并发严重感染','易发生GVHD','CO₂气腹相关并发症','排斥反应发生率最高','肾','供受者ABO血型不符','慢性排斥反应是最大障碍','小肠','受者已有供者特异性HLA抗体','角膜','皮肤','皮肌瓣'],
    stems: [['组织移植',['J','K','L']],['超急性排斥反应',['F','I']],['移植疗效最显著',['E','G']],['小肠移植',['A','B','D','H']],['腹腔镜手术',['C']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-06', title: '其它外科总论·肿瘤预防与癌痛', lecture: 38, page: 2,
    options: ['高危人群定期筛查','药物以外的治疗','强阿片类：吗啡','早发现、早诊断、早治疗','从小剂量开始，视止痛效果逐渐增量','疫苗','非阿片类：阿司匹林','防止癌症发生','定期给药','弱阿片类：可待因','姑息、对症治疗','戒烟','口服→直肠→注射'],
    stems: [['一级预防',['F','H','L']],['二级预防',['A','D']],['三级预防',['K']],['癌痛阶梯',['B','C','G','J']],['癌痛给药原则',['E','I','M']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-07', title: '其它外科总论·抗肿瘤药分类', lecture: 38, page: 2,
    options: ['甲氨蝶呤','赫赛汀','阿糖胞苷','三苯氧胺／他莫昔芬','阿霉素','紫杉醇','伊马替尼','泼尼松','博来霉素','环磷酰胺','放线菌素','长春碱','美罗华','丝裂霉素','氟尿嘧啶'],
    stems: [['细胞毒素类',['J']],['抗代谢类',['A','C','O']],['抗生素类',['E','I','K','N']],['生物碱类',['F','L']],['激素类',['D','H']],['靶向药',['B','G','M']]],
  }),
  choiceGroup({
    id: 'surgery-general-other-08', title: '其它外科总论·常见体表肿瘤与囊肿', lecture: 38, page: 2,
    options: ['疼痛','颜色不均匀','表面小黑点','变大','手术切除效果好','生长缓慢','单胚层囊性畸胎瘤','位于基底细胞层，易恶变','对放疗敏感','皮带区','直径＞6 mm','哑铃状','眉梢和颅骨骨缝','切面黄色','破溃后可呈鼠咬状','质软','分叶状','瘙痒','不规则','浸润性生长','足底','高度恶性','头面部多见','头面和背部','老年人多见','色素加深','破溃','很少转移','不对称','低度恶性','囊内豆渣物','出血','手掌'],
    stems: [['皮肤基底细胞癌',['E','F','I','O','T','W','Y','②','④']],['黑色素瘤',['B','K','S','V','③']],['交界痣',['A','D','H','J','R','U','Z','①','⑥','⑦']],['脂肪瘤',['N','P','Q']],['皮脂腺囊肿',['C','X','⑤']],['皮样囊肿',['G','L','M']]],
  }),
  fillGroup({
    id: 'surgery-general-other-09', title: '其它外科总论·数字挖空', lecture: 38, page: 1,
    stems: [['高压蒸汽灭菌物品有效期____周。',['2']],['煮沸灭菌持续____小时。',['1']],['戊二醛等化学药液浸泡____小时。',['10']],['皮肤消毒范围包括切口周围____ cm。',['15']],['器械用____ mg/L有效氯浸泡____小时。',['2000','1']],['止血带每____小时放松____～____分钟，使用不超过____小时。',['1','1','2','4']],['开放伤清创时切除创缘皮肤____～____ mm。',['1','2']],['一般伤口伤后____～____小时内可一期缝合。',['6','8']],['头面部伤口____小时内、头皮伤口____小时内可一期缝合。',['12','24']],['黑色素瘤警示直径＞____ mm。',['6']]],
  }),
]

export const surgeryGeneralLaterGroups = [...shockGroups, ...otherGroups]
