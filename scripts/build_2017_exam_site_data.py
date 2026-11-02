#!/usr/bin/env python3
"""Build chapter-linked website data for the 2017 306 clinical medicine exam."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber


SUBJECT_LABELS = {
    "physiology": "生理学",
    "biochemistry": "生物化学",
    "pathology": "病理学",
    "med": "内科学",
    "surgery": "外科学",
}

SURGERY_TOPIC_BY_LECTURE = {
    1: "颈部疾病", 2: "胸部疾病", 3: "乳房疾病", 4: "胸部疾病",
    5: "胃十二指肠疾病", 6: "腹部损伤与感染", 7: "腹部损伤与感染",
    8: "小肠与阑尾疾病", 9: "小肠与阑尾疾病", 10: "结直肠与肛管疾病",
    11: "结直肠与肛管疾病", 12: "腹外疝", 13: "肝胆胰疾病", 14: "肝胆胰疾病",
    15: "肝胆胰疾病", 16: "肝胆胰疾病", 17: "周围血管疾病",
    18: "泌尿外科", 19: "泌尿外科",
}


def build_answers() -> dict[int, str]:
    ranges = {
        (1, 5): "ABCAA", (6, 10): "DDDCB", (11, 15): "BCCAB", (16, 20): "DDACA",
        (21, 25): "DBDCB", (26, 30): "CCBDC", (31, 35): "CCAAB", (36, 40): "DCABB",
        (41, 45): "BCBDB", (46, 50): "CBCAA", (51, 55): "BBCCB", (56, 60): "BDADD",
        (61, 65): "BACCB", (66, 67): "CD", (68, 69): "AD", (70, 72): "BAD",
        (73, 75): "AAA", (76, 78): "CCA", (79, 81): "ACB", (82, 84): "CBD",
        (85, 87): "DCA", (88, 90): "BBA", (91, 92): "AA", (93, 94): "BC",
        (95, 96): "AD", (97, 99): "BBB", (100, 102): "CCC", (103, 105): "BCB",
        (106, 107): "AD", (108, 110): "ABD", (111, 115): "AADAB", (116, 117): "AD",
        (118, 119): "BC", (120, 121): "BA", (122, 123): "AC", (124, 125): "AC",
        (126, 127): "AC", (128, 129): "CD", (130, 131): "AD", (132, 133): "BC",
        (134, 135): "AB",
    }
    answers: dict[int, str] = {}
    for (start, end), value in ranges.items():
        assert len(value) == end - start + 1
        answers.update({number: value[number - start] for number in range(start, end + 1)})
    answers.update({
        136: "AC", 137: "ABD", 138: "BCD", 139: "ABC", 140: "AB", 141: "AC",
        142: "BC", 143: "AB", 144: "BCD", 145: "CD", 146: "AB", 147: "CD",
        148: "CD", 149: "ACD", 150: "AB", 151: "CD", 152: "BCD", 153: "ACD",
        154: "BD", 155: "ABC", 156: "ABCD", 157: "ABC", 158: "AC", 159: "ABD",
        160: "CD", 161: "BCD", 162: "BCD", 163: "BCD", 164: "AB", 165: "ABD",
    })
    assert set(answers) == set(range(1, 166))
    return answers


ANSWERS = build_answers()


B_GROUPS = [
    (116, 117, {"A": "毛细血管血压增高", "B": "毛细血管通透性增高", "C": "组织液胶体渗透压增高", "D": "血浆胶体渗透压降低"}),
    (118, 119, {"A": "以激素调节为主", "B": "以神经调节为主", "C": "以代谢产物反馈调节为主", "D": "受靶腺激素和下丘脑调节肽的双重调节"}),
    (120, 121, {"A": "RNA编辑", "B": "RNA自身剪接", "C": "RNA加帽", "D": "RNA加多聚A尾"}),
    (122, 123, {"A": "酵母双杂交法", "B": "聚合酶链反应", "C": "染色质免疫沉淀法", "D": "DNA链末端合成终止法"}),
    (124, 125, {"A": "动脉玻璃样变性", "B": "动脉纤维素样变性", "C": "动脉粥样硬化", "D": "动脉中层钙化"}),
    (126, 127, {"A": "化脓性炎", "B": "变质性炎", "C": "浆液性炎", "D": "纤维素性炎"}),
    (128, 129, {"A": "溶栓治疗", "B": "介入取栓治疗", "C": "抗凝治疗", "D": "抗血小板治疗"}),
    (130, 131, {"A": "依地酸二钠钙", "B": "二巯丙醇", "C": "亚甲蓝", "D": "纳洛酮"}),
    (132, 133, {"A": "普萘洛尔", "B": "复方碘溶液", "C": "丙硫氧嘧啶", "D": "醋酸泼尼松"}),
    (134, 135, {"A": "终末血尿伴膀胱刺激征", "B": "无痛性全程肉眼血尿", "C": "疼痛伴血尿", "D": "初始血尿"}),
]


MANUAL = {
    17: ("biochemistry", "氨基酸与蛋白质", "lecture-08", 1), 18: ("biochemistry", "糖代谢", "lecture-03", 2),
    19: ("biochemistry", "脂代谢", "lecture-05", 2), 20: ("biochemistry", "生物氧化", "lecture-02", 1),
    21: ("biochemistry", "氨基酸与蛋白质", "lecture-08", 1), 22: ("biochemistry", "核苷酸代谢", "lecture-09", 1),
    23: ("biochemistry", "核酸", "lecture-20", 1), 24: ("biochemistry", "小基因", "lecture-17", 1),
    25: ("biochemistry", "氨基酸与蛋白质", "lecture-08", 2), 26: ("biochemistry", "小基因", "lecture-14", 3),
    27: ("biochemistry", "小基因", "lecture-19", 1), 28: ("biochemistry", "糖代谢", "lecture-01", 3),
    42: ("med", "循环", "lecture-55", 2), 45: ("med", "呼吸", "lecture-01", 4), 46: ("med", "呼吸", "lecture-04", 2),
    37: ("pathology", "炎症", "lecture-25", 2), 38: ("pathology", "肿瘤", "lecture-26", 2),
    68: ("med", "循环", "lecture-55", 3), 69: ("med", "循环", "lecture-55", 3),
    95: ("surgery", "胃十二指肠疾病", "exam-2017-surgery-peptic-ulcer", 11),
    96: ("surgery", "胃十二指肠疾病", "exam-2017-surgery-peptic-ulcer", 11),
    **{q: ("med", "医学人文", "exam-2017-medical-ethics", None) for q in range(108, 116)},
    116: ("physiology", "循环系统", "lecture-11", 2), 117: ("physiology", "循环系统", "lecture-11", 2),
    118: ("physiology", "生殖系统", "lecture-41", 2), 119: ("physiology", "内分泌", "lecture-36", 1),
    120: ("biochemistry", "小基因", "lecture-17", 2), 121: ("biochemistry", "小基因", "lecture-17", 2),
    122: ("biochemistry", "小基因", "lecture-14", 3), 123: ("biochemistry", "小基因", "lecture-14", 3),
    142: ("biochemistry", "核酸", "lecture-15", 1), 143: ("biochemistry", "糖代谢", "lecture-03", 3),
    144: ("biochemistry", "氨基酸与蛋白质", "lecture-07", 2), 145: ("biochemistry", "氨基酸与蛋白质", "lecture-08", 2),
    146: ("biochemistry", "小基因", "lecture-17", 1), 147: ("biochemistry", "小基因", "lecture-19", 1),
    132: ("med", "内分泌", "lecture-36", 4), 133: ("med", "内分泌", "lecture-36", 4),
    153: ("pathology", "肿瘤", "lecture-26", 2),
    163: ("surgery", "肝胆胰疾病", "exam-2017-surgery-pancreatitis", 8),
}


DETAILED = {
    1: "肠上皮刷状缘的SGLT利用Na⁺电化学梯度逆浓度转运葡萄糖，属继发性主动转运。",
    2: "骨骼肌兴奋-收缩耦联时，横管膜L型钙通道（DHP受体）激活并机械耦联RyR1，使终池Ca²⁺释放。",
    3: "血小板释放ADP和TXA₂会招募、激活更多血小板，推动不可逆聚集。",
    4: "窦房结P细胞最大复极电位绝对值较小，无稳定静息电位，4期可自动去极化。",
    5: "射血结束后主动脉压高于左室压，主动脉瓣关闭，这正是等容舒张期的起点。",
    6: "肺换气是肺泡气与肺毛细血管血液之间的气体交换；外界与肺泡之间是肺通气。",
    7: "去甲肾上腺素的肾上腺素能效导致气道平滑肌舒张；组胺、PGF₂α和乙酰胆碱均促收缩。",
    8: "长链脂肪酸进入肠上皮后重新酰化为甘油三酯，组装成乳糜微粒后经淋巴转运。",
    9: "食物氧热价是某营养物氧化时每消耗1 L氧所产生的热量。",
    10: "摄钾增多会促进远曲小管和集合管主细胞分泌K⁺，并可刺激醛固酮分泌。",
    11: "血管升压素决定集合管对水的通透性，是尿浓缩与稀释的关键体液因子。",
    12: "对光反射中枢位于中脑顶盖前区，并经双侧Edinger-Westphal核传出。",
    13: "EPSP是兴奋性递质引起的局部去极化电位，可发生时间和空间总和。",
    14: "牵张反射中枢在脊髓，感受器为肌梭；脊休克后反射可逐渐恢复，并非永久消失。",
    15: "生长激素促进蛋白质合成、脂肪分解并降低外周组织对葡萄糖的利用。",
    16: "Sertoli支持细胞在FSH作用下分泌雄激素结合蛋白，维持生精小管内高浓度睎酮。",
    17: "蛋白质α螺旋通常为右手螺旋，靠肽链内氢键稳定，氨基酸侧链伸向螺旋外侧。",
    18: "糖原合酶催化UDP-葡萄糖加到糖原非还原端，是糖原合成的关键酶。",
    19: "甲亢时胆固醇转化为胆汁酸的速度加快，清除增多，因而血清胆固醇降低。",
    20: "P/O比值表示氧化磷酸化时每消耗1/2 O₂所生成的ATP数。",
    21: "食物蛋白质的营养价值反映其在体内被利用的程度，与必需氨基酸模式密切相关。",
    22: "天冬氨酸既参与嘌呤和嘶啶环骨架形成，也在尿素循环中提供一个氮。",
    23: "端粒酶由具逆转录酶活性的蛋白质和作为模板的RNA组成。",
    24: "原核和真核转录均以DNA一条链为模板，具有不对称性；其余调控、酶系和加工地点不同。",
    25: "热休克蛋白是分子伴侣，帮助新生肽链正确折叠并防止错误聚集。",
    26: "同一限制性内切酶产生的互补黏性末端可由DNA连接酶连接。",
    27: "蛋白激酶把磷酸基转移到蛋白质特定残基，磷酸化可使靶蛋白活性增强或降低。",
    28: "红细胞Rapoport-Luebering旁路生成2,3-BPG，可降低Hb对O₂的亲和力并促进释氧。",
    29: "凋亡多累及散在细胞，细胞膜保持完整并出芽形成凋亡小体，通常不引起明显炎症。",
    30: "急性左心衰使肺静脉及静脉端毛细血管压骤升，红细胞由毛细血管漏出。",
}


DETAILED.update({
    31: "Langhans巨细胞是结核性肉芽肿的典型组成，其多个细胞核常排列于胞质周边。",
    32: "胸膜上多发、均一的粟粒大小硬结节符合血行播散性结核的粟粒样病变。",
    33: "急进性高血压时小动脉壁可发生纤维素样坏死；良性高血压多见玻璃样变。",
    34: "病毒性肺炎主要累及肺间质，表现为肺泡间隔水肿及单核细胞浸润。",
    35: "HBV表面抗原在肝细胞内质网蓄积，可使胞质呈毛玻璃样外观。",
    36: "肠结核尤其增生型病变可引起肠壁增厚、纤维化和肠腔狭窄。",
    37: "慢性肾盂肾炎本质为化脓性炎，可见肾间质慢性炎细胞浸润和瘢痕。",
    38: "单核或双核巨细胞、明显嗜酸性大核仁提示Reed-Sternberg细胞，首先考虑霍奇金淋巴瘤。",
    39: "水肿绒毛侵入子宫肌层是侵袭性葡萄胎的关键病理特征。",
    40: "SLE的Libman-Sacks心内膜炎赘生物为无菌性纤维素与血小板沉积。",
    41: "肝源性水肿由低白蛋白血症、门静脉高压等导致，可见踝部凹陷性水肿并常伴腹水。",
    42: "剑突下搏动在深吸气时更明显，提示增大的右心室随吸气回心血量增加而搏动增强。",
    43: "医院获得性肺炎常见病原为革兰阴性杆菌，如铜绿假单胞菌和肠杆菌科细菌。",
    44: "胸水pH 6.9、白细胞显著增高并伴发热、肺炎征象，最符合脓胸/复杂性肺炎旁积液。",
    45: "PaCO₂ 68 mmHg表明明显肺泡低通气，因而COPD患者高碳酸血症的直接机制是肺泡通气量下降。",
    46: "双侧肺门淋巴结肿大、肺间质改变和铺路石样黏膜提示结节病，BAL常见淋巴细胞增多及CD4/CD8升高。",
    47: "BNP主要由心室肌在室壁张力增高时分泌，左心室功能不全时可明显升高。",
    48: "夜间静息时发作的心绞痛考虑冠脉痉挛，钙通道阻滞剂既可降压又能解除冠脉痉挛。",
    49: "LVEF明显降低、完全性左束支阻滞并有室壁不同步，符合心脏再同步化治疗指征。",
    50: "阿司匹林抑制COX-1，使胃黏膜保护性前列腺素合成减少，是NSAID溃疡的主要机制。",
    51: "原发性肝癌早期常沿肝内门静脉分支侵袭和播散，以肝内转移为主。",
    52: "肝硬化患者腹水快速增多、脾进一步增大而无发热，提示门静脉血栓形成。",
    53: "上呼吸道感染后3天即出现肉眼血尿的“同步血尿”是IgA肾病的典型线索。",
    54: "溶血时游离Hb与结合珠蛋白结合并被清除，因而血清结合珠蛋白降低。",
    55: "1型糖尿病的本质是胰岛β细胞破坏和胰岛素绝对缺乏，胰岛素分泌曲线低平最能反映其病理生理。",
    56: "环孢素属改善病情抗风湿药；泼尼松为糖皮质激素，阿司匹林和塞来昔布主要对症抗炎。",
    57: "低镁会促进肾小管失钾，使单纯补钾难以纠正，顽固性低钾时应同时查镁。",
    58: "CEA可用于结肠癌预后和复发监测，但肿瘤切除范围由部位、分期及淋巴引流决定，不能因CEA正常而缩小。",
    59: "甲状腺手术后饮水呛咳而发音正常，提示喉上神经内支感觉功能受损。",
    60: "4 cm乳腺肿瘤属T2；同侧腋窝淋巴结相互融合属N2；无远处转移为M0。",
    61: "股疝疝环狭小且边缘坚韧，疝内容物最易发生嵌顿和绞窄。",
    62: "结肠癌在常见胃肠道恶性肿瘤中总体预后相对较好；其余选项左右半结肠表现写反或转移途径错误。",
    63: "高热、黄疸、右上腹痛并休克提示急性棗阻性化脓性胆管炎，应抗休克同时尽快解除胆道棗阻。",
    64: "距肛缘7 cm的直肠癌在能保证切缘和括约肌功能时可行Dixon低位前切除术。",
    65: "高龄患者移位性股骨颈头下型骨折的头端血供破坏严重，人工股骨头置换可早期活动。",
    66: "急性血源性骨髓炎好发于儿童长骨干骨后端，以胫骨和股骨最常见。",
    67: "颈椎病中神经根型最常见，交感型可出现心动过速等表现但并非最多见。",
    68: "劳力性呼吸困难、夜间阵发性呼吸困难、端坐呼吸和双肺底湿啰音构成心源性呼吸困难证据链。",
    69: "左心衰时肺静脉压升高导致肺淤血和肺间质水肿，是该患者呼吸困难的主要机制。",
    70: "MCV明显增大伴贫血、白细胞和血小板减少，提示巨幼细胞性贫血。",
    71: "巨幼细胞性贫血常见舌炎，可表现为光滑、绛红的“牛肉样舌”。",
    72: "巨幼细胞性贫血因DNA合成障碍出现核成熟落后于胞质的“核幼浆老”。",
    73: "急性肺栓塞导致V/Q失调和低氧血症，低氧刺激过度通气，典型为PaO₂和PaCO₂同时降低。",
    74: "肺栓塞是否溶栓主要取决于血流动力学危险分层，即血压及右心功能情况。",
    75: "手术和短期卧床属一过性诱因，首次静脉血栓栓塞抗凝通常至少3个月，本题对应3-6个月。",
    76: "奇脉、颈静脉怒张、脉压差窄、心界向两侧扩大而肺部无啰音，提示大量心包积液。",
    77: "超声心动图可直接显示心包积液量、心腔受压及填塞征象，是最有价值的检查。",
    78: "大量心包积液已造成血流动力学障碍时，关键是立即心包穿刺引流解除压塞。",
    79: "餐后反酸烧心、平卧加重且内镜见食管黏膜破损，符合胃食管反流病。",
    80: "伴食管黏膜破损的GERD首选质子泵抑制剂奥美拉唑强力抑酸并促进愈合。",
    81: "反流性食管炎需维持治疗时，PPI在症状控制和黏膜愈合方面优于H₂受体阻断剂。",
    82: "孕妇发热、腰痛、尿频尿痛且出现白细胞管型，病变已累及上尿路，为急性肾盂肾炎。",
    83: "急性肾盂肾炎最常见的致病菌是大肠埃希菌，多由下尿路上行感染。",
    84: "妊娠30周合并急性肾盂肾炎应住院静脉抗菌治疗，第三代头孢菌素疗效和安全性合适。",
    85: "无痛性浅表淋巴结肿大、发热瘙痒及R-S细胞提示霍奇金淋巴瘤。",
    86: "淋巴瘤的确诊依赖完整淋巴结活检评估结构、细胞形态及免疫表型。",
    87: "网织红细胞15%提示骨髓代偿性增生，结合淋巴瘤更支持自身免疫性溶血。",
    88: "弥漫性甲状腺肿、甲状腺激素升高且TSH受抑制，最符合Graves病。",
    89: "年轻Graves患者的初始治疗可选抗甲状腺药甲巯咪唑，抑制甲状腺激素合成。",
    90: "甲状腺激素仍高且心动过速等症状未缓解时，加用β受体阻滞剂可快速控制交感症状。",
    91: "干燥综合征的评估包括Schirmer试验、涎腺造影及核素检查，双膝X线对确诊无直接价值。",
    92: "原发性干燥综合征的特征性皮肤表现为高丙种球蛋白血症相关的紫癜样皮疹。",
    93: "腹部闭合伤合并休克和腹膜刺激征时，腹腔穿刺可迅速判断有无腹腔内出血。",
    94: "上腹部铝伤、失血性休克和移动性浊音提示实质脏器破裂，最可能为肝脾破裂。",
    95: "突发上腹剧痛、板状腹和既往胃病史提示溃疡穿孔，立位腹平片可快速查见膈下游离气。",
    96: "消化性溃疡穿孔并弥漫性腹膜炎应在复苏、减压和抗感染后急诊手术探查修补。",
    97: "铁钉刺伤后苦笑面容、角弓反张和声刺激诱发痉挛为破伤风，由厹氧芽胞杆菌引起。",
    98: "破伤风伤口应彻底清创并破坏厹氧环境，可用过氧化氢溶液冲洗。",
    99: "破伤风需TAT或特异性人破伤风免疫球蛋白及抗菌药，普通丙种球蛋白不是必需药物。",
    100: "枣核两端尖锐，误吞后最严重的并发症是消化道穿孔及继发性腹膜炎。",
    101: "判断尖锐异物是否造成穿孔，反复腹部物理检查观察腹膜刺激征是最简单有效的方法。",
    102: "症状减轻且无穿孔征象时可继续保守观察，口服液体石蜡促进异物安全排出。",
    103: "慢性髋痛、寒性脓肿、Thomas征阳性和虫蚀样骨破坏符合全髋关节结核。",
    104: "髋部MRI能显示滑膜、软骨、骨髓及关节周围脓肿的累及范围，对明确全髋关节结核最有价值。",
    105: "抗结核治疗后全身情况改善但寒性脓肿不消失，应在有效药物覆盖下行病灶清除术。",
    106: "急性血源性骨髓炎早期局部肿胀尚不明显，干骨后端深压痛是有力体征。",
    107: "局部穿刺抽出脓液并行涂片、培养可直接证实急性化脓性骨髓炎。",
    108: "“大慈恻隐之心”强调医者以仁爱救治患者，体现“医乃仁术”。",
    109: "患者把生命健康委托给掌握专业知识的医务人员，这一特征构成医患信托关系。",
    110: "医生用手绘图形和患者交流，信息不依赖口语或文字，属非语言沟通。",
    111: "患者具有决策能力时应尊重其自主权，但医生仍须充分说明高风险并尽力劝其住院。",
    112: "疾病认知权是患者知悉所患疾病的性质、治疗情况和预后的权利。",
    113: "在紧急状况且其他方案无效时，挽救患者生命是首要原则，不能仅以家属拒签停止抢救。",
    114: "对高血压中危患者长期使用空白安慰剂会剥夺有效治疗，且招募酬劳造成利益冲突，设计不合伦理。",
    115: "HIV感染信息应保密，但属传染病法定报告范围，医生应向疾控机构报告而不向无关人员公开。",
    116: "右心衰导致体静脉压升高，毛细血管静水压增高是组织水肿的主要机制。",
    117: "肾病综合征大量蛋白尿造成低白蛋白血症，血浆胶体渗透压降低导致水肿。",
    118: "分娩和射乳反射中，神经冲动促进催产素释放，所以缩宫素分泌以神经调节为主。",
    119: "PTH分泌主要由血钙等代谢产物通过负反馈直接调节。",
    120: "核酶是具有催化活性的RNA，经典功能之一是催化RNA自身剪接。",
    121: "RNA编辑可改变转录本的核苷酸信息，使蛋白质氨基酸序列与原始hnRNA不完全对应。",
    122: "酵母双杂交法通过转录因子DNA结合域与激活域的重建检测蛋白-蛋白相互作用。",
    123: "染色质免疫沉淀用特异抗体富集目标蛋白及其结合的DNA，用于检测DNA-蛋白相互作用。",
    124: "良性高血压的典型小动脉病变是玻璃样变，管壁增厚、管腔狭窄。",
    125: "心肌梗死最常见的基础病变是冠状动脉粥样硬化旑块破裂并血栓形成。",
    126: "急性蜂窝织炎性阑尾炎以中性粒细胞弥漫浸润阑尾壁为特征，属化脓性炎。",
    127: "风湿性关节炎急性期以浆液和纤维素渗出为主，属浆液性炎。",
    128: "房颤伴左房增大有心源性栓塞风险，需抗凝治疗预防脑卒中。",
    129: "PCI植入药物洗脱支架后需双联抗血小板治疗预防支架内血栓。",
    130: "依地酸二钠钙可螯合铅并促进其排泄，是铅中毒的常用解毒药。",
    131: "纳洛酮是阿片受体拮抗剂，可快速逆转阿片类中毒引起的呼吸抑制。",
    132: "复方碘溶液能抑制甲状腺激素释放并减少甲状腺血流，使腺体缩小变硬，常用于术前准备。",
    133: "丙硫氧嘧啶长期使用可使TSH相对升高，导致甲状腺增大和充血。",
    134: "膀胱结核多由肾结核下行感染，典型为膀胱刺激征伴终末血尿。",
    135: "膀胱癌最典型的首发表现是无痛性、间歇性全程肉眼血尿。",
    136: "肝素通过增强抗凝血酶活性并促进组织因子途径抑制物释放发挥抗凝作用。",
    137: "小肠运动包括紧张性收缩、分节运动、蠕动及逆蠕动；集团蠕动主要见于大肠。",
    138: "CO₂在血中少部分物理溶解，大部分以HCO₃⁻转运，碳酸酐酶加速反应；氨基甲酰Hb形成不需酶。",
    139: "循环血量减少、动脉压下降及致密旑NaCl递送减少均促进肾素分泌；肾交感活动增强而非减弱促肾素。",
    140: "递质释放量主要取决于动作电位频率及进入突触前末梢的Ca²⁺量。",
    141: "刚分泌的汗液近等渗，导管重吸收NaCl后变低渗；汗液几乎不含蛋白质，Na⁺重吸收受醛固酮调节。",
    142: "GC配对稳定性高，适度增加离子强度又能屏蔽磷酸骨架负电排斥，两者都使Tm升高。",
    143: "糖异生绕过丙酮酸激酶不可逆反应需丙酮酸羧化酶和PEP羧激酶。",
    144: "SAM是活性甲基供体，参与磷脂酰胆碱、肌酸及肾上腺素合成的甲基化反应。",
    145: "胞内蛋白质可经溶酶体或泛素-蛋白酶体途径降解；甲硫氨酸循环和脱氨基是氨基酸代谢。",
    146: "TFⅡD中的TBP首先识别TATA盒，并招募包括RNA聚合酶Ⅱ在内的转录起始复合体。",
    147: "Src本身是非受体型酪氨酸激酶，EGF受体具内在性酪氨酸激酶活性。",
    148: "EBV与鼻咽癌及多种淋巴瘤（如Burkitt淋巴瘤）发生密切相关。",
    149: "毛玻璃样肝细胞胞质不透明、呈嗜酸性细颗粒状，内质网蓄积HBsAg，不是淀粉样物质。",
    150: "伤寒小结和子宫内膜结核均为巨噬细胞聚集形成的肉芽肿性炎。",
    151: "CINⅢ包括重度异型增生和原位癌，异型细胞累及上皮超过2/3直至全层但未突破基底膜。",
    152: "类风湿关节炎滑膜可见淋巴细胞浸润、滑膜细胞和血管增生，并可形成血管翳。",
    153: "滤泡性淋巴瘤为成熟B细胞肿瘤，常表达BCL-2、CD20和CD79a；CD3是T细胞标志。",
    154: "慢性肺心病急性加重期的核心是控制感染、改善通气氧疗并处理并发症，利尿和强心须谨慎选用。",
    155: "扩张型心肌病可出现病理Q波、心腔扩大所致二尖瓣反流及核素灌注的斑片样减低，而矛盾运动更典型于室壁瘤。",
    156: "溃疡性结肠炎可并发大出血、肠穿孔、中毒性巨结肠及长期炎症相关癌变。",
    157: "重症AKI可根据血流动力学采用间歇性血液透析、连续性动-静脉或静-静脉血液滤过；本题答案不将腹透列入重症首选。",
    158: "PT反映外源性及共同途径，因子Ⅶ或凝血酶原缺乏可使PT延长；TT主要评估纤维蛋白向纤维蛋白的转化。",
    159: "大量补碱、大剂量胰岛素和糖皮质激素都可使K⁺向细胞内转移或增加肾排钾，导致低钾。",
    160: "胰腺导管腺癌总体预后差、5年生存率低，CA19-9是主要血清标记物；对放疗并非高度敏感，长春新碱非首选。",
    161: "轻度脾破裂可修补，外伤性腹腔内出血在无污染时可自体回输，儿童切脾后可行自体脾片移植；不应等待休克完全纠正才手术止血。",
    162: "GIST起源于Cajal间质细胞，常CD117阳性，危险度与肿瘤长径、核分裂数、部位及破裂有关。",
    163: "急性胰腺炎出现脓肿/感染性坏死、胆道棗阻或保守后急剧恶化时需介入或手术；单一膀胱压22 mmHg不等同手术指征。",
    164: "骨折的特有体征是畸形、反常活动和骨擦音/骨擦感；压痛和肿胀并非特异。",
    165: "粘连性肩关节囊炎具自限性，可观察、理疗和功能锻炼；难治性病例可关节镜松解，长期悬吊会加重僵硬。",
})


def normalize(text: str) -> str:
    text = text.replace("ttsx", "").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip()
    replacements = {
        "Ca2+": "Ca²⁺", "CO2": "CO₂", "O2": "O₂", "PaO2": "PaO₂", "PaCO2": "PaCO₂",
        "Na+": "Na⁺", "K+": "K⁺", "H+": "H⁺", "10 9/L": "10⁹/L", "109/L": "10⁹/L",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bPaO\b", "PaO₂", text)
    text = re.sub(r"\bPaCO\b", "PaCO₂", text)
    if "PaO₂" in text or "PaCO₂" in text:
        text = re.sub(r"\s+2\s+2(?=\s|$)", " ", text).strip()
    text = re.sub(r"\bCO\b", "CO₂", text)
    if "CO₂" in text:
        text = re.sub(r"\s+2(?=\s|$)", " ", text).strip()
    text = re.sub(r"\bO\s+(?=进入|的比值)", "O₂ ", text)
    if "O₂" in text:
        text = re.sub(r"\s+2(?=\s|$)", " ", text).strip()
    text = re.sub(r"\bT\s+N\s+M\s+2\s+2\s+0\b", "T₂N₂M₀", text)
    text = re.sub(r"\bT\s+N\s+M\s+([123])\s+([12])\s+0\b", lambda m: f"T{m.group(1).translate(str.maketrans('123', '₁₂₃'))}N{m.group(2).translate(str.maketrans('12', '₁₂'))}M₀", text)
    text = re.sub(r"10\s*6/L", "10⁶/L", text)
    text = re.sub(r"10\s*9/L", "10⁹/L", text)
    text = re.sub(r"A\s*=\s*P\s*[。.]?\s*2\s*2", "A₂=P₂", text)
    text = re.sub(r"P\s*[>＞]\s*A\s*([，,。]?)\s*2\s*2", r"P₂>A₂\1", text)
    if "CTPA" in text:
        text = re.sub(r"P\s*[>＞]\s*A\s*，", "P₂>A₂，", text)
        text = re.sub(r"\s+2\s+2$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_questions(source: Path) -> dict[int, dict]:
    pages: list[str] = []
    question_pages: dict[int, int] = {}
    with pdfplumber.open(source) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            kept = []
            for line in (page.extract_text(x_tolerance=2, y_tolerance=3) or "").splitlines():
                compact = line.strip()
                if compact.startswith("每日计划 精选答疑") or re.fullmatch(r"-\s*\d+\s*-", compact):
                    continue
                kept.append(line)
                match = re.match(r"\s*(\d{1,3})\.(?!\d)", line)
                if match and 1 <= int(match.group(1)) <= 165:
                    question_pages[int(match.group(1))] = page_number
            pages.append("\n".join(kept))
    raw = "\n".join(pages)
    shared: dict[int, str] = {}
    for match in re.finditer(r"(?ms)^\s*\((\d+)-(\d+)\s*(?:题)?共用题干\)(.*?)(?=^\s*\1\.(?!\d))", raw):
        start, end = int(match.group(1)), int(match.group(2))
        for q in range(start, end + 1):
            shared[q] = normalize(match.group(3))

    starts = list(re.finditer(r"(?m)^\s*(\d{1,3})\.(?!\d)", raw))
    questions: dict[int, dict] = {}
    for index, match in enumerate(starts):
        q = int(match.group(1))
        if not 1 <= q <= 165 or 116 <= q <= 135:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(raw)
        block = raw[match.end():end]
        block = re.split(r"(?m)^\s*\(\d+-\d+\s*(?:题)?共用题干\)", block)[0]
        block = re.split(r"(?m)^\s*(?:二、B\s*型题|三、X\s*型题)", block)[0]
        block = block.split("此为西医综合改革后的试卷", 1)[0]
        markers = list(re.finditer(r"(?m)^\s*([ABCD])\.", block))
        if len(markers) < 4:
            continue
        stem = normalize(block[:markers[0].start()])
        options = {}
        for option_index, marker in enumerate(markers[:4]):
            option_end = markers[option_index + 1].start() if option_index < 3 else len(block)
            options[marker.group(1)] = normalize(block[marker.end():option_end])
        questions[q] = {"stem": stem, "options": options, "sharedStem": shared.get(q), "page": question_pages.get(q)}

    b_section = raw.split("二、B 型题", 1)[-1].split("三、X 型题", 1)[0]
    b_starts = list(re.finditer(r"(?m)^\s*(1(?:1[6-9]|2\d|3[0-5]))\.(?!\d)", b_section))
    b_stems: dict[int, str] = {}
    for index, match in enumerate(b_starts):
        q = int(match.group(1))
        end = b_starts[index + 1].start() if index + 1 < len(b_starts) else len(b_section)
        block = b_section[match.end():end]
        block = re.split(r"(?m)^\s*A\.", block)[0]
        b_stems[q] = normalize(block)
    for start, end, options in B_GROUPS:
        for q in range(start, end + 1):
            questions[q] = {"stem": b_stems[q], "options": options, "sharedStem": None, "page": question_pages.get(q)}
    missing = sorted(set(range(1, 166)) - set(questions))
    if missing:
        raise RuntimeError(f"Could not parse questions: {missing}")
    return questions


def subject_for_question(q: int) -> str:
    if q <= 16 or 116 <= q <= 119 or 136 <= q <= 141:
        return "physiology"
    if 17 <= q <= 28 or 120 <= q <= 123 or 142 <= q <= 147:
        return "biochemistry"
    if 29 <= q <= 40 or 124 <= q <= 127 or 148 <= q <= 153:
        return "pathology"
    if 41 <= q <= 56 or 68 <= q <= 92 or 108 <= q <= 115 or 128 <= q <= 133 or 154 <= q <= 159:
        return "med"
    return "surgery"


def load_content(root: Path) -> tuple[dict[str, list[dict]], dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    contents: dict[str, list[dict]] = defaultdict(list)
    lecture_titles: dict[tuple[str, str], str] = {}
    lecture_topics: dict[tuple[str, str], str] = {}
    for subject in SUBJECT_LABELS:
        for path in sorted((root / "src/data").glob(f"{subject}*data.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                continue
            if not isinstance(data, dict):
                continue
            contents[subject].append(data)
            topic_votes: dict[str, Counter] = defaultdict(Counter)
            for group in data.get("groups", []):
                for lecture_id in group.get("lectureIds", []):
                    topic_votes[lecture_id][group.get("topic", "综合")] += 1
            for lecture in data.get("lectures", []):
                key = (subject, lecture.get("id"))
                lecture_titles[key] = lecture.get("title", lecture.get("id"))
                if topic_votes.get(lecture.get("id")):
                    lecture_topics[key] = topic_votes[lecture.get("id")].most_common(1)[0][0]
    return contents, lecture_titles, lecture_topics


def exact_lecture_map(contents: dict[str, list[dict]]) -> dict[int, tuple[str, str, int | None]]:
    result = {}
    for q in range(1, 166):
        subject = subject_for_question(q)
        for data in contents[subject]:
            for lecture in data.get("lectures", []):
                text = lecture.get("text", "")
                match = re.search(rf"2017N{q}(?!\d)", text)
                if not match:
                    range_match = next((m for m in re.finditer(r"2017N(\d+)-(\d+)", text) if int(m.group(1)) <= q <= int(m.group(2))), None)
                    match = range_match
                if not match:
                    continue
                before = text[:match.start()]
                page_matches = list(re.finditer(r"-\s*(\d+)\s*-", before))
                page = int(page_matches[-1].group(1)) if page_matches else None
                result[q] = (subject, lecture.get("id"), page)
                break
            if q in result:
                break
    return result


def evidence_index(root: Path) -> dict[tuple[str, str], list[dict]]:
    index: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for subject in SUBJECT_LABELS:
        for path in (root / "src/data").glob(f"{subject}*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue

            def walk(value):
                if isinstance(value, dict):
                    if value.get("lectureId") and value.get("image"):
                        item = dict(value)
                        item["_subject"] = subject
                        index[(subject, value["lectureId"])].append(item)
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(data)
    return index


def choose_evidence(root: Path, index: dict, subject: str, lecture_id: str, page: int | None, title: str, q: int) -> dict | None:
    if lecture_id == "exam-2017-medical-ethics":
        return None
    source_subject, source_lecture = subject, lecture_id
    if lecture_id == "exam-2017-surgery-peptic-ulcer":
        source_subject, source_lecture, page = "med", "lecture-16", 11
    elif lecture_id == "exam-2017-surgery-pancreatitis":
        source_subject, source_lecture, page = "med", "lecture-23", 8
    candidates = index.get((source_subject, source_lecture), [])
    if page is not None:
        exact = [item for item in candidates if item.get("page") == page]
        candidates = exact or candidates
    if candidates:
        def score(item):
            item_page = item.get("page")
            return (0 if item_page == page else 1, abs(item_page - page) if isinstance(item_page, int) and isinstance(page, int) else 999)
        picked = min(candidates, key=score)
        return {
            "lectureId": lecture_id,
            "page": picked.get("page", page),
            "image": picked["image"],
            "title": picked.get("title") or title,
            "sourceFile": picked.get("sourceFile", "对应讲义"),
            "description": f"2017年真题第{q}题对应讲义原页。",
        }
    pattern = root / f"public/{source_subject}/lecture-pages/{source_lecture}-page-*.webp"
    files = sorted(pattern.parent.glob(pattern.name))
    if files:
        wanted = next((file for file in files if page is not None and f"page-{page:02}" in file.name), files[0])
        return {
            "lectureId": lecture_id,
            "page": page,
            "image": str(wanted.relative_to(root / "public")),
            "title": f"{title}{f' · 第{page}页' if page else ''}",
            "sourceFile": "对应讲义",
            "description": f"2017年真题第{q}题对应讲义原页。",
        }
    return None


def generic_explanation(q: int, question: dict, chapter: str) -> str:
    answer = ANSWERS[q]
    correct = "；".join(f"{key}.{question['options'][key]}" for key in answer)
    wrong = [f"{key}.{value}" for key, value in question["options"].items() if key not in answer]
    if q >= 136:
        suffix = f"未入选项为{' 、'.join(wrong)}，不符合题干的全部限定。" if wrong else ""
        return f"本题考查“{chapter}”。正确组合为{answer}：{correct}。{suffix}"
    return f"本题考查“{chapter}”。正确选项为{answer}：{correct}。其余选项与题干所问的机制、定义或适应证不符。"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    questions = extract_questions(args.source)
    contents, lecture_titles, lecture_topics = load_content(root)
    exact = exact_lecture_map(contents)
    evidences = evidence_index(root)
    outputs = {subject: {"meta": {"sourceLabel": "2017年临床医学综合能力（西医）真题", "answerNote": "答案按用户提供的答案图录入"}, "topics": [], "pages": [], "lectures": [], "groups": []} for subject in SUBJECT_LABELS}
    synthetic_lectures = {
        "exam-2017-medical-ethics": {"id": "exam-2017-medical-ethics", "number": 2017, "title": "2017真题 医学伦理与医患沟通", "pageCount": 1},
        "exam-2017-surgery-peptic-ulcer": {"id": "exam-2017-surgery-peptic-ulcer", "number": 2017, "title": "2017真题 消化性溃疡穿孔", "pageCount": 1},
        "exam-2017-surgery-pancreatitis": {"id": "exam-2017-surgery-pancreatitis", "number": 2017, "title": "2017真题 急性胰腺炎", "pageCount": 1},
    }
    used_synthetic: dict[str, set[str]] = defaultdict(set)

    for q in range(1, 166):
        subject = subject_for_question(q)
        if q in MANUAL:
            manual_subject, topic, lecture_id, lecture_page = MANUAL[q]
            assert manual_subject == subject
        else:
            mapped = exact.get(q)
            if not mapped:
                raise RuntimeError(f"No lecture mapping for question {q}")
            _, lecture_id, lecture_page = mapped
            topic = lecture_topics.get((subject, lecture_id), "综合")
        if subject == "surgery" and re.fullmatch(r"lecture-(\d+)", lecture_id):
            lecture_number = int(lecture_id.removeprefix("lecture-"))
            if lecture_number in SURGERY_TOPIC_BY_LECTURE:
                topic = SURGERY_TOPIC_BY_LECTURE[lecture_number]
            elif 20 <= lecture_number <= 29:
                topic = "骨科"
            elif 30 <= lecture_number <= 38:
                topic = "外科总论"
        lecture_title = lecture_titles.get((subject, lecture_id), synthetic_lectures.get(lecture_id, {}).get("title", lecture_id))
        evidence = choose_evidence(root, evidences, subject, lecture_id, lecture_page, lecture_title, q)
        question = questions[q]
        answer = ANSWERS[q]
        explanation = DETAILED.get(q) or generic_explanation(q, question, lecture_title)
        correct_labels = [f"{key}. {question['options'][key]}" for key in answer]
        incorrect_labels = [f"{key}. {value}" for key, value in question["options"].items() if key not in answer]
        kind = "X" if q >= 136 else ("B" if q >= 116 else "A")
        group = {
            "id": f"exam-2017-{subject}-q{q:03d}",
            "page": question["page"] or 1,
            "sourceKey": "clinical-2017-exam",
            "sourceName": args.source.name,
            "sourceSection": SUBJECT_LABELS[subject],
            "sourceQuestion": str(q),
            "sourceLabel": "2017年临综真题",
            "title": f"2017真题 · 第{q}题 · {lecture_title.replace('生理 ', '').replace('生化 ', '').replace('病理 ', '').replace('内科含诊断 ', '').replace('内科 ', '').replace('外科 ', '')}",
            "kind": kind,
            "kindLabel": "多项选择" if kind == "X" else ("B型题" if kind == "B" else "单项选择"),
            "answerLayout": "rows",
            "topic": topic,
            "lectureIds": [lecture_id],
            "supplement": True,
            "supplementNotice": "已录入完整题干、答案、解析和讲义要点",
            "answerSourceLabel": "2017真题答案",
            "answerSourceName": "用户提供的答案图",
            "hideSource": True,
            "options": [{"key": key, "displayKey": key, "label": value} for key, value in question["options"].items()],
            "stems": [{
                "number": q,
                "sourceQuestion": q,
                "sourcePage": question["page"],
                "text": question["stem"],
                "answerRaw": answer,
                "answer": list(answer),
                "answerMode": "多选" if kind == "X" else "单选",
                "answerState": "按提供的答案图录入",
                "lectureId": lecture_id,
                "explanation": explanation,
                "knowledgeConnections": [
                    f"讲义定位：{lecture_title}",
                    f"必会项：{' ；'.join(correct_labels)}",
                    f"易混对照：{' ；'.join(incorrect_labels)}" if incorrect_labels else "本题所列选项均需掌握。",
                ],
            }],
            "lectureSummary": [
                f"所属模块：{lecture_title}",
                f"答案依据：{' ；'.join(correct_labels)}",
                explanation,
            ],
        }
        if question.get("sharedStem"):
            group["sharedStem"] = question["sharedStem"]
            group["sharedQuestionCount"] = 1
        if evidence:
            evidence["knowledgePoints"] = [lecture_title, explanation]
            evidence["questionNumbers"] = [q]
            group["lectureEvidence"] = evidence
        else:
            group["lectureEvidenceNotice"] = "本题所属模块以文字讲义要点展示。"
        outputs[subject]["groups"].append(group)
        if lecture_id in synthetic_lectures:
            used_synthetic[subject].add(lecture_id)

    for subject, output in outputs.items():
        output["topics"] = ["全部", *dict.fromkeys(group["topic"] for group in output["groups"])]
        output["lectures"] = [synthetic_lectures[lecture_id] for lecture_id in sorted(used_synthetic[subject])]
        output["meta"].update({"groupCount": len(output["groups"]), "stemCount": len(output["groups"]), "lectureCount": len(output["lectures"])})
        path = root / f"src/data/{subject}-2017-exam-data.json"
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{subject}: {len(output['groups'])} questions -> {path}")
    catalog = [{
        "id": f"{subject}-2017-clinical-exam",
        "subject": subject,
        "subjectLabel": SUBJECT_LABELS[subject].replace("学", ""),
        "title": f"2017年临综真题·{SUBJECT_LABELS[subject]}",
        "category": "2017真题",
        "sourceFile": f"{subject}-2017-exam-data.json",
        "groupIds": [group["id"] for group in outputs[subject]["groups"]],
        "groupCount": len(outputs[subject]["groups"]),
        "stemCount": len(outputs[subject]["groups"]),
    } for subject in SUBJECT_LABELS]
    (root / "src/data/2017-exam-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
