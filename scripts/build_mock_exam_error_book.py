#!/usr/bin/env python3
"""Build a system-organized error book for the 2027 mock exam."""

from __future__ import annotations

import argparse
import html
import re
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


WRONG_NUMBERS = [
    9, 10, 11, 12, 16, 19, 21, 22, 26, 27, 30, 38, 39, 41, 42, 44, 46,
    50, 54, 60, 68, 69, 70, 73, 75, 76, 78, 80, 83, 84, 95, 96, 98,
    102, 119, 122, 124, 125, 126, 127, 135, 136, 137, 138, 139, 140,
    142, 149, 151, 154, 155, 156, 157, 162, 163, 164,
]


# q, system, discipline, answer, lecture, page, lecture recap, trap/review cue
ROWS = [
    (19, "基础机制与分子生物学", "生物化学", "A", "生化第12讲《酶》", "6", "辅酶与酶蛋白结合松散，在反应中承担电子、原子或基团的转移载体作用；辅基则结合紧密。", "不要把“辅酶”等同于维持酶构象；先问它在反应中转移了什么。"),
    (21, "基础机制与分子生物学", "生物化学", "A", "生化第4讲《血浆脂蛋白》", "2", "乳糜微粒的甘油三酯需毛细血管内皮面的脂蛋白脂肪酶 LPL 水解；LPL 缺陷会使乳糜微粒显著潴留。", "见“乳糜微粒升高”优先想 LPL/apoC-II，不是 HMG-CoA 还原酶。"),
    (22, "基础机制与分子生物学", "生物化学", "D", "生化第7讲《氨基酸代谢》", "3", "联合脱氨基包括转氨基和 L-谷氨酸氧化脱氨基：转氨酶以 VitB6 衍生的磷酸吡哆醛为辅酶，谷氨酸脱氢酶使用 NAD+ 或 NADP+，后两者来源于 VitPP。", "把“转氨基-B6”和“氧化脱氨基-PP”成对记忆，因此选 VitB6、VitPP。"),
    (26, "基础机制与分子生物学", "生物化学", "B", "生化第19讲《基因表达调控》", "3", "活性染色质结构疏松、对核酸酶敏感，CpG 岛倾向低甲基化；组蛋白乙酰化及部分泛素化与活性转录相关。", "做染色质题先用“疏松-敏感-低甲基化”排除，再判断组蛋白修饰。"),
    (27, "基础机制与分子生物学", "生物化学", "D", "生化第14讲《小基因》", "3-4", "基因治疗载体常用病毒载体；逆转录病毒可将外源基因整合至靶细胞基因组，在备选项中最合适。", "质粒更像实验室工具；题干问“人体基因治疗”时先考虑病毒载体。"),
    (122, "基础机制与分子生物学", "生物化学", "B", "生化第18讲《翻译》", "1", "原核翻译起始时，16S rRNA 与 mRNA 上的 Shine-Dalgarno 序列互补配对，定位起始密码。", "建立固定配对：S-D-16S；肽酰转移酶活性-23S rRNA（大亚基）。"),
    (136, "基础机制与分子生物学", "生理学", "ABD", "生理第1讲《绪论》", "7", "前馈控制是在被控变量尚未明显变化前，由预先信息启动调节。脱衣入水前的体温调节、起跑前心率增快和见食物后的消化液分泌均属于此类。", "正式答案排除 C。判断时抓“刺激结果尚未发生，调节已提前启动”，不要把所有促进效应都归入前馈。"),
    (137, "基础机制与分子生物学", "生理学", "ABC", "生理第8讲《生理性止血》", "1", "胶原、肾上腺素和 5-HT 都可促进血小板活化/聚集；前列环素 PGI2 来自内皮，升高血小板 cAMP 而抑制聚集。", "把 PGI2 与 TXA2 做成对照：前者抗聚集/扩血管，后者促聚集/缩血管。"),
    (138, "基础机制与分子生物学", "生理学", "BCD", "生理第16讲《肺换气和气体运输》", "6", "Hb 由 R 型转为 T 型时对 O2 亲和力降低，氧解离曲线右移、P50 升高，对 H+ 和 CO2 的结合能力增强。", "题干问“错误”，A 是正确现象，BCD 均把方向写反。"),
    (142, "基础机制与分子生物学", "生物化学", "ABD", "生化第12讲《酶》", "3", "关键酶常位于代谢途径起始处或分叉后的第一个反应，且常为别构酶或受激素调节的酶；它通常催化慢反应，活性不是最高。", "A、B、D 描述关键酶的常见位置与调节特征；C 把限速作用误写成活性最高。"),
    (149, "基础机制与分子生物学", "病理学", "ACD", "病理第23讲《适应和损伤》", "3, 7-8", "含铁血黄素、近端小管玻璃样小滴和脂褐素均与溶酶体消化/自噬有关；胆汁性肝硬化羽毛状变是胆色素/胆盐淤积损伤。", "判断“与溶酶体相关”时，抓吞噬后残余物、重吸收小滴和自噬色素。"),
    (10, "神经与感觉", "生理学", "A", "生理第27讲《视觉》", "8, 14", "视力 1.0 的标准是最小视角约 1 分角。视网膜中央凹单线联系、视锥细胞直径小，因而视敏度最高。", "“一个视锥细胞直径”是解剖生理依据，“1 分角”才是 1.0 视力的标准定义。"),
    (11, "神经与感觉", "生理学", "D", "生理第29讲《其它感觉》", "1-4", "前庭器官过强或过久受刺激可引起心率加快、呼吸加快、血压下降，以及恶心、呕吐、出汗等前庭自主神经反应。", "心率与血压不是同向变化：常见 HR↑、BP↓。"),
    (119, "神经与感觉", "生理学", "B", "生理第30讲《神经元及胶质细胞》", "3", "Aβ（II 类）有髓纤维主要传导触压觉和本体感觉，与精细触压觉相匹配；Aδ 更常与粗略触压觉、快痛和温度觉相联系。", "记配对：Aβ-触压/本体；Aδ-快痛/温度/粗触压；C-慢痛。"),
    (16, "内分泌与生殖", "生理学", "D", "生理第41讲《生殖》", "3-4", "排卵后黄体形成，孕激素明显升高，并使基础体温升高，因此孕激素升高更能证明“已经发生排卵”。", "LH 峰值是排卵的触发/预测信号，孕激素升高是排卵后证据。"),
    (38, "内分泌与生殖", "病理学", "C", "病理第16讲《内分泌系统疾病》", "3", "亚急性甲状腺炎又称肉芽肿性/巨细胞性甲状腺炎，可见滤泡部分破坏、胶质外溢和异物巨细胞构成的结核样肉芽肿。", "其肿大常不对称/结节状并疼痛；广泛破坏萎缩、大量淋巴细胞更偏向桥本。"),
    (9, "肾脏与体液", "生理学", "C", "生理第26讲《小管转运、尿浓缩稀释》", "12-13", "髓袢升支粗段对水不通透，主动重吸收 NaCl，末端小管液为低渗。高渗性脱水时 ADH 高，集合管尿液趋向高渗。", "沿肾单位画一条渗透压曲线：降支升、升支降，粗段末低渗。"),
    (42, "肾脏与体液", "内科学", "A", "内科第47讲《系统性血管炎》", "1", "肺-肾综合征、新月体肾炎、抗 GBM 阴性并有皮肤紫癜，更符合 ANCA 相关的显微镜下多血管炎。", "抓“抗 GBM 阴性”排 Goodpasture；呼吸道肉芽肿缺如时也支持 MPA 而非 GPA。"),
    (80, "肾脏与体液", "内科学", "D", "内科第22讲《肝硬化》", "4-5", "肝硬化大量腹水患者利尿后少尿，需警惕有效循环血容量不足/肝肾综合征；停用利尿剂并静脉补充白蛋白是关键处理之一。", "肝肾综合征尿钠低、蛋白尿不重；少尿时不能继续加大利尿剂。"),
    (83, "肾脏与体液", "内科学", "D", "内科第27讲《原发性肾小球疾病》", "16", "乙型肝炎相关性肾炎最常见的病理类型是膜性肾病，常呈肾病综合征。", "继发性肾病综合征固定配对：HBV-膜性；糖尿病-KW 结节；SLE-满堂亮。"),
    (84, "肾脏与体液", "内科学", "B", "内科第27讲《原发性肾小球疾病》", "7, 16", "肾病综合征不主张高蛋白饮食，否则可增加肾小球高滤过和蛋白尿。HBV 相关性肾炎需以抗病毒为基础，其他治疗按风险选用。", "低白蛋白血症不等于高蛋白饮食；这是常见的直觉型陷阱。"),
    (140, "肾脏与体液", "生理学", "ABD", "生理第26讲《小管转运、尿浓缩稀释》", "4", "乙酰唑胺抑制碳酸酐酶，使近端小管 Na+-H+ 交换和 HCO3- 重吸收下降：尿量、尿 HCO3- 和尿 K+ 增加，尿 H+ 下降。", "先写“碳酸酐酶被抑制”的主链，再推出碱性尿、低钾和代谢性酸中毒。"),
    (157, "肾脏与体液", "内科学", "ACD", "内科第26讲《肾衰竭》", "2", "慢性肾病性贫血的常用治疗包括促红细胞生成素、HIF-PH 抑制剂罗沙司他和补铁；红细胞输注不作为常规长期方案。", "注意本例高血压：使用 ESA 前要先控压；题目问的是治疗类别，不是让三者同时上。"),
    (44, "呼吸系统", "内科学", "B", "内科第8讲《肺结核》", "1-2", "青年女性、长期干咳与低热、颈部成串淋巴结，加上上肺片状影和小空洞，典型指向干酪性肺炎/肺结核。", "肺炎题先抓病程：3 个月+低热+上肺空洞，不要被“片状影”带向急性细菌性肺炎。"),
    (46, "呼吸系统", "内科学", "C", "内科第3讲《急性肺血栓栓塞症》", "1", "突发胸膜性胸痛+少量咯血+单侧下肢肿胀是 PTE/DVT 链条；反复自然流产与血小板减少提示抗磷脂综合征这一高凝背景。", "把情境信息串成“APS-DVT-PTE-肺梗死性胸水”，不要逐个症状分开看。"),
    (68, "呼吸系统", "内科学", "B", "内科第9讲《支气管哮喘》", "2", "反复夜间/凌晨干咳、抗菌药无效、胸片正常且非发作期肺功能可正常，考虑咳嗽变异性哮喘；首选支气管激发试验证实气道高反应。", "激发试验用于基础肺功能正常/非发作期；舒张试验用于已有气流受限。"),
    (69, "呼吸系统", "内科学", "D", "内科第9讲《支气管哮喘》", "3", "呼出气一氧化氮 FeNO 反映嗜酸性气道炎症，可用于评估对吸入糖皮质激素治疗的反应性。", "PEF 适合监测气流变化与病情；FeNO 更直接回答“激素反应”。"),
    (73, "呼吸系统", "内科学", "B", "内科第13讲《胸膜疾病》", "6", "大量右侧胸腔积液使右胸廓饱满、肝浊音界可下移，纵隔和心界向健侧（左）移位；积液上方可闻及管状呼吸音。", "液体占位会将纵隔推向健侧。选项 B 的“肝界上移+心界右移”方向均错。"),
    (75, "呼吸系统", "内科学", "D", "内科第13讲《胸膜疾病》", "4", "血性渗出液、淋巴细胞为主、LDH 高、ADA 不高，合并硬而无痛的锁骨上淋巴结，首先按恶性胸水处理：胸腔引流并胸膜固定（化疗药/滑石粉）。", "PPD 阳性不能压过恶性证据；ADA 30 U/L 也不支持结核性胸水。"),
    (154, "呼吸系统", "内科学", "ACD", "内科第10讲《ARDS》", "2-3", "ARDS 治疗包括高浓度吸氧以尽快改善氧合、小潮气量+适当 PEEP、允许性高碳酸血症/呼吸性酸中毒，并保持肺相对干燥、必要时利尿。", "B 的“大潮气量复张”会增加容量伤和压伤，是最应先排除的项。"),
    (12, "心血管系统", "生理学", "D", "生理第32讲《递质和受体》", "3", "去甲肾上腺素激活 α2 受体可使小肠壁平滑肌舒张；α1 受体主要使皮肤/内脏血管和胃肠括约肌收缩。", "把胃肠道分成“壁肌舒张、括约肌收缩”两个方向记。"),
    (70, "心血管系统", "内科学", "A", "内科第53讲《心瓣膜病》", "6", "二尖瓣狭窄导致重度肺动脉高压，可出现 Graham-Steell 杂音。左心室通常不大，心尖搏动可仍在左第 5 肋间锁骨中线。", "MS 的 S1 常亢进，心影偏“梨形”而非球形；Graham-Steell 杂音一般不产生舒张期震颤。"),
    (76, "心血管系统", "内科学", "C", "内科第54讲《冠心病》", "10-11", "急性下壁心梗后第 6 天突发肺水肿，胸骨左缘第 3 肋间新出现伴震颤的全收缩期杂音，提示室间隔穿孔。", "乳头肌断裂的杂音重点在心尖部；室间隔穿孔在胸骨左缘并常有震颤。"),
    (78, "心血管系统", "内科学", "C", "内科第54讲《冠心病》", "11", "下壁心梗常累及右冠脉和房室结供血，可并发高度或三度房室传导阻滞，表现为极度心动过缓、心律不齐和意识障碍。", "看心梗部位联想并发症：下壁-房室结-缓慢性心律失常。"),
    (155, "心血管系统", "内科学", "AC", "内科第54讲《冠心病》", "11", "急性心梗合并肺水肿可用吗啡镇痛并减轻交感兴奋；频发室早/短阵室速可用利多卡因。强心苷和短效硝苯地平不是此时的常规处理。", "心梗多选先排除会增加心律失常/低血压风险的药；按“疼痛-心衰-心律失常”分别处理。"),
    (41, "消化与肝胆胰", "生物化学", "B", "生化第10讲《胆色素代谢》", "2", "Crigler-Najjar 综合征由胆红素 UDP-葡萄糖醛酸转移酶严重缺陷引起，未结合胆红素显著升高，I 型可致核黄疸。", "四种遗传性黄疸按 UCB/CB 和转运/结合缺陷做成 2x2 表。"),
    (50, "消化与肝胆胰", "内科学", "D", "内科第16讲《消化性溃疡与消化道出血》", "3", "十二指肠溃疡疼痛向背部放射，血淀粉酶升高，但无突发弥漫性腹膜炎，提示慢性穿孔/穿透至胰腺。", "急性穿孔=刀割样痛+板状腹+膈下游离气；穿透性=背痛+淀粉酶高。"),
    (60, "消化与肝胆胰", "外科学", "A", "外科第7讲《腹部损伤》", "3", "左半结肠损伤合并黄色脓液、粪便溢出和弥漫性腹膜炎，污染重，宜造口/外置，而不是一期修补或吻合。", "结肠损伤先看“左/右半+污染轻重”；左半且粪性腹膜炎倾向造口。"),
    (95, "消化与肝胆胰", "外科学", "D", "外科第10讲《大肠癌》", "1", "长期黏液血便、贫血、左腹包块并急性肠梗阻强烈提示左半结肠癌；结肠镜可直视并取活检，是确诊的金标准。", "题目问“明确诊断”而非分期：肠镜+病理优先于 MRI。"),
    (96, "消化与肝胆胰", "外科学", "C", "外科第10讲《大肠癌》", "1", "左半结肠癌并急性梗阻时，可先置入支架解除梗阻，作为转换至限期根治手术的桥接。", "先解决梗阻再根治。无明显坏死/穿孔时，支架桥接能降低急诊手术风险。"),
    (98, "消化与肝胆胰", "外科学", "A", "外科第16讲《胆系疾病》", "7", "Reynolds 五联征提示急性梗阻性化脓性胆管炎。B 超快速、无创，可显示胆管扩张和结石，是首选影像学检查。", "危重患者检查按“快、床旁、无创”排序；确诊后立即胆道减压。"),
    (102, "消化与肝胆胰", "外科学", "C", "外科第15讲《胰腺肿瘤》", "2", "胰头十二指肠切除术后第 5 天，腹腔引流量骤增且淀粉酶极高，直接提示胰肠吻合口漏/胰瘘。", "术后引流液“淀粉酶高”是胰漏的定位线索；“胆红素高”才更支持胆漏。"),
    (139, "消化与肝胆胰", "生理学", "ABCD", "生理第20讲《胃内消化》", "3", "胃期由食物扩张胃底/胃体通过迷走-迷走长反射和壁内神经丛短反射促进，蛋白质消化产物促进胃液素释放；分泌量大且酸度/胃蛋白酶含量高。", "不要把“胃期胃液分泌”与“胃排空调节”混在一起；两组长/短反射可同时出现。"),
    (151, "消化与肝胆胰", "病理学", "ACD", "病理第3讲《肝硬化》", "2-3", "小结节性肝硬化的结节通常不超过 3 mm，纤维间隔较细；假小叶中央静脉可缺如、偏位或出现两个以上，再生肝细胞可体积增大、双核、核大深染。", "按正式答案选 ACD。复习时把小结节的直径和纤维间隔特征，与假小叶中央静脉及再生细胞改变分别整理。"),
    (156, "消化与肝胆胰", "内科学", "ACD", "内科第14讲《胃食管反流病》", "2", "GERD 的食管症状包括反流、烧心，以及由食管痉挛引起的胸痛、吞咽困难和胸骨后异物感；癔球症归入食管外症状。", "区分“胸骨后异物感”与“咽部癔球感”，部位决定归类。"),
    (162, "消化与肝胆胰", "外科学", "ABCD", "外科第9讲《阑尾炎》", "4", "慢性阑尾炎钡灌肠可见阑尾不充盈、充盈不全、腔不规则和排空延迟至 3 天以上。", "这是一组典型的“全选”影像学表现，不要因为四项都像对而主动删项。"),
    (163, "消化与肝胆胰", "外科学", "ABD", "外科第16讲《胆系疾病》", "3", "胆总管探查指征包括小粒/泥沙样胆囊结石、反复胰腺炎或胆管炎、触及胆总管结石/蛔虫以及胆总管扩张；扩张标准通常是 >10 mm，不是 >5 mm。", "数字陷阱是本题核心：胆总管正常约 6-8 mm，>5 mm 不足以作探查指征。"),
    (30, "血液、肿瘤与损伤修复", "病理学", "C", "病理第22讲《损伤的修复》", "1-2", "肉芽组织主要由新生毛细血管、成纤维细胞、巨噬细胞及其他炎细胞构成；一般不含神经纤维。", "“肉芽组织”不是“肉芽肿”；前者是修复性新生组织。"),
    (39, "血液、肿瘤与损伤修复", "病理学", "B", "病理第19讲《乳腺疾病》", "2", "浸润性小叶癌细胞常呈单行串珠样或靶环样排列，常转移至脑脊液、浆膜、卵巢、子宫和骨髓。", "抓特殊转移部位：小叶癌-脑脊液/浆膜/女性生殖器官/骨髓。"),
    (54, "血液、肿瘤与损伤修复", "内科学", "C", "内科第29讲《再生障碍性贫血》", "1", "再障主要与造血干/祖细胞损伤、免疫异常和造血微环境改变有关。骨髓脂肪化、CD34+ 细胞减少、TNF 升高可见，CD4/CD8 比值倾向降低。", "本题问“不包括”，把 CD8+ 细胞扩增导致的比值方向记牢。"),
    (124, "血液、肿瘤与损伤修复", "病理学", "B", "病理第26讲《肿瘤》", "4", "淋巴管瘤属良性脉管肿瘤，可呈局部浸润性生长、易复发，但不发生转移。", "“浸润性生长”不等于恶性；脉管瘤是经典例外。"),
    (125, "血液、肿瘤与损伤修复", "病理学", "A", "病理第26讲《肿瘤》", "6", "鼻咽癌是恶性上皮性肿瘤，呈浸润性生长，并常早期经淋巴道转移至颈部淋巴结。", "“癌多淋巴转移”是总规律，鼻咽癌+颈部淋巴结是高频特征。"),
    (126, "血液、肿瘤与损伤修复", "内科学", "C", "内科第35讲《淋巴瘤》", "5", "混合细胞型经典型霍奇金淋巴瘤中，典型 RS 细胞（双核镜影细胞）与多种炎细胞混合存在。", "陷窝细胞-结节硬化型；爆米花细胞-NLPHL；典型镜影 RS-混合细胞型。"),
    (127, "血液、肿瘤与损伤修复", "内科学", "D", "内科第35讲《淋巴瘤》", "5", "经典型霍奇金淋巴瘤中，淋巴细胞减少型的 EBV 感染率最高，可接近 100%，且常与 HIV 感染相关。", "分型表要横向对齐：结节硬化-EBV 低；淋巴细胞减少-EBV 最高。"),
    (135, "血管与运动系统", "外科学", "A", "外科第17讲《周围血管疾病》", "3-4", "产后全下肢肿胀、发绀、皮温下降和动脉搏动减弱提示髪青股肿/严重深静脉血栓；Perthes 试验用于判断深静脉是否通畅。", "四试验配对：Buerger-动脉；Trendelenburg-大隐静脉瓣；Pratt-交通支瓣；Perthes-深静脉。"),
    (164, "血管与运动系统", "外科学", "ACD", "外科第28讲《四肢骨折和脱位》", "5-7", "前臂双骨折需解剖复位并警惕骨筋膜室综合征。稳定性与不稳定性骨折并存时先复稳定者；两者均不稳定时，下段先桡骨，中上段先尺骨。X 线证实愈合前禁止旋转。", "B 把中段的复位顺序写反。口诀：两斜不稳定，桡下尺上。"),
]


B_OVERRIDES = {
    119: ("A.Aα类纤维\nB.Aβ类纤维\nC.Aδ类纤维\nD.B类纤维", "传导皮肤精细触压觉的神经纤维是"),
    122: ("A.5S rRNA\nB.16S rRNA\nC.18S rRNA\nD.28S rRNA", "在蛋白质生物合成的起始阶段，识别 S-D 序列的是"),
    124: ("A.鼻咽癌\nB.淋巴管瘤\nC.甲状腺滤泡癌\nD.卵巢粒层细胞瘤", "呈浸润性生长，不发生淋巴转移的是"),
    125: ("A.鼻咽癌\nB.淋巴管瘤\nC.甲状腺滤泡癌\nD.卵巢粒层细胞瘤", "呈浸润性生长，常发生淋巴转移的是"),
    126: ("A.结节性淋巴细胞为主型\nB.结节硬化型\nC.混合细胞型\nD.淋巴细胞减少型", "上述霍奇金淋巴瘤中镜影细胞最常见于"),
    127: ("A.结节性淋巴细胞为主型\nB.结节硬化型\nC.混合细胞型\nD.淋巴细胞减少型", "上述霍奇金淋巴瘤中 EBV 感染最常见于"),
    135: ("A.Perthes 试验\nB.Buerger 试验\nC.Pratt 试验\nD.Trendelenburg 试验", "女性，29 岁。产后 1 周，左腰部酸痛不适 3 天，伴左下肢突发肿胀 2 天。查体：左下肢全肢肿胀，小腿屈肌部位张力高，足背水肿，左大腿和小腿皮肤青紫，足部皮温降低，足背动脉搏动极微弱。对该患者最有助于诊断的试验是"),
}


def normalize(text: str) -> str:
    text = text.replace("ttsx", "")
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_exam(source: Path) -> tuple[dict[int, dict], dict[int, str]]:
    page_texts = []
    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            lines = []
            for line in (page.extract_text(x_tolerance=2, y_tolerance=3) or "").splitlines():
                if line.startswith("每日计划 精选答疑"):
                    continue
                if re.fullmatch(r"-\s*\d+\s*-", line.strip()):
                    continue
                lines.append(line.replace("ttsx", ""))
            page_texts.append("\n".join(lines))
    raw = "\n".join(page_texts)

    shared = {}
    for m in re.finditer(r"\((\d+)-(\d+)\s*题共用题干\)(.*?)(?=\n\s*\1\.)", raw, re.S):
        start, end = int(m.group(1)), int(m.group(2))
        stem = normalize(m.group(3))
        for q in range(start, end + 1):
            shared[q] = stem

    starts = list(re.finditer(r"(?m)^\s*(\d{1,3})\.(?!\d)", raw))
    questions = {}
    for i, match in enumerate(starts):
        q = int(match.group(1))
        if not 1 <= q <= 165:
            continue
        end = starts[i + 1].start() if i + 1 < len(starts) else len(raw)
        block = raw[match.end():end]
        block = re.split(r"\(\d+-\d+\s*题共用题干\)", block)[0]
        markers = list(re.finditer(r"(?m)^\s*([ABCD])\.", block))
        if len(markers) < 4:
            continue
        stem = normalize(block[:markers[0].start()])
        opts = {}
        for j, om in enumerate(markers[:4]):
            oend = markers[j + 1].start() if j + 1 < 4 else len(block)
            opts[om.group(1)] = normalize(block[om.end():oend])
        questions[q] = {"stem": stem, "sharedStem": shared.get(q), "options": opts}

    for q, (option_text, stem) in B_OVERRIDES.items():
        opts = {}
        for line in option_text.splitlines():
            opts[line[0]] = line[2:]
        questions[q] = {"stem": stem, "sharedStem": None, "options": opts}
    return questions, shared


def points(q: int) -> float:
    if q <= 40:
        return 1.5
    if q <= 115:
        return 2.0
    if q <= 135:
        return 1.5
    return 2.0


def qtype(q: int) -> str:
    if q <= 115:
        return "A型题"
    if q <= 135:
        return "B型题"
    return "X型题"


def esc(text: str) -> str:
    return html.escape(text).replace("\n", "<br/>")


class ErrorBookDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, pagesize=A4, **kwargs)
        frame = Frame(17 * mm, 18 * mm, A4[0] - 34 * mm, A4[1] - 34 * mm, id="main")
        self.addPageTemplates(PageTemplate(id="body", frames=frame, onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7DEE5"))
        canvas.setLineWidth(0.45)
        canvas.line(17 * mm, 14 * mm, A4[0] - 17 * mm, 14 * mm)
        canvas.setFont("CJK", 8)
        canvas.setFillColor(colors.HexColor("#66727D"))
        canvas.drawString(17 * mm, 9 * mm, "2027考研西综·摸底考试错题本")
        canvas.drawRightString(A4[0] - 17 * mm, 9 * mm, f"{doc.page}")
        canvas.restoreState()


def build(source: Path, output: Path) -> None:
    questions, _ = extract_exam(source)
    missing = [q for q in WRONG_NUMBERS if q not in questions]
    if missing:
        raise RuntimeError(f"Failed to extract questions: {missing}")
    if sorted(q for q, *_ in ROWS) != sorted(WRONG_NUMBERS):
        raise RuntimeError("Metadata rows do not match the requested wrong-question list")

    font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    if not font.exists():
        font = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
    pdfmetrics.registerFont(TTFont("CJK", str(font)))

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = ErrorBookDoc(
        str(output),
        title="2027考研西综摸底考试错题本",
        author="Codex",
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    ss = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=ss["Title"], fontName="CJK", fontSize=25, leading=34, textColor=colors.HexColor("#132A35"), alignment=TA_LEFT, spaceAfter=10)
    subtitle = ParagraphStyle("subtitle", parent=ss["Normal"], fontName="CJK", fontSize=11, leading=18, textColor=colors.HexColor("#53646D"), spaceAfter=16)
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="CJK", fontSize=18, leading=25, textColor=colors.HexColor("#123A43"), spaceBefore=8, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="CJK", fontSize=13, leading=19, textColor=colors.HexColor("#123A43"), spaceBefore=6, spaceAfter=6)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="CJK", fontSize=9.4, leading=15, textColor=colors.HexColor("#25333A"), spaceAfter=5)
    small = ParagraphStyle("small", parent=body, fontSize=8.2, leading=12.5, textColor=colors.HexColor("#596A72"))
    question_style = ParagraphStyle("question", parent=body, fontSize=9.5, leading=15.2, spaceAfter=6)
    option_style = ParagraphStyle("option", parent=body, fontSize=9.1, leading=14.2, leftIndent=4 * mm, firstLineIndent=-4 * mm, spaceAfter=1.5)
    label_style = ParagraphStyle("label", parent=small, fontSize=8.2, leading=12, textColor=colors.HexColor("#0B6B62"))
    white_center = ParagraphStyle("white_center", parent=body, fontSize=20, leading=24, textColor=colors.white, alignment=TA_CENTER)
    metric = ParagraphStyle("metric", parent=body, fontSize=9.2, leading=13, alignment=TA_CENTER)

    story = []
    story += [
        Spacer(1, 10 * mm),
        Paragraph("2027考研西综", subtitle),
        Paragraph("基础强化摸底考试<br/><font color='#0B6B62'>系统化错题本</font>", title),
        Paragraph("根据你提供的 56 道错题整理，包含计分、漏洞画像、完整题目、标准答案、对应讲义回扣与复盘提示。", subtitle),
    ]
    score_box = Table(
        [[Paragraph("198", white_center), Paragraph("/ 300", white_center)],
         [Paragraph("总分", metric), Paragraph("正确率 66.0%", metric)]],
        colWidths=[42 * mm, 42 * mm], rowHeights=[21 * mm, 10 * mm],
    )
    score_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B6B62")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#E7F2EF")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#0B6B62")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B7D4CF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story += [score_box, Spacer(1, 8 * mm)]

    section_rows = [
        ["题型/区段", "错题", "得分", "得分率"],
        ["1-40 A型 (1.5分)", "13/40", "40.5/60", "67.5%"],
        ["41-115 A型 (2分)", "21/75", "108/150", "72.0%"],
        ["116-135 B型 (1.5分)", "7/20", "19.5/30", "65.0%"],
        ["136-165 X型 (2分)", "15/30", "30/60", "50.0%"],
    ]
    t = Table([[Paragraph(esc(str(c)), small) for c in row] for row in section_rows], colWidths=[64 * mm, 30 * mm, 35 * mm, 31 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163F49")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D3D8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [Paragraph("计分拆解", h2), t, Spacer(1, 6 * mm)]
    story += [
        Paragraph("漏洞画像", h1),
        Paragraph("<b>1. X 型题是最大失分口。</b> 30 题错 15 题，本区得分率只有 50%。错题中反复出现“全选/多个正确”和“方向、数字、绝对词”陷阱，说明主要问题是选项逐项验证不足，不只是知识点缺失。", body),
        Paragraph("<b>2. 临床决策链需要串起来。</b> 呼吸、肾脏、心血管和消化多道题都在考“病史/体征 - 诊断 - 首选检查 - 当前处理”。错题常落在后两步，如 FeNO、结肠镜、B 超、支架桥接、白蛋白扩容。", body),
        Paragraph("<b>3. 相似概念的边界容易混淆。</b> 典型对包括：亚甲炎 vs 桥本，穿透性溃疡 vs 急性穿孔，恶性胸水 vs 结核性胸水，Perthes vs Pratt，胸骨后异物感 vs 癔球症。", body),
        Paragraph("<b>4. 基础学科的“一对一映射”不够稳。</b> 辅酶功能、VitB2/VitB6、LPL、16S rRNA、组蛋白修饰、胆红素遗传缺陷都属于可通过对照表快速补齐的失分。", body),
        PageBreak(),
        Paragraph("复习优先级", h1),
    ]

    system_counter = Counter(r[1] for r in ROWS)
    system_lost = defaultdict(float)
    for q, system, *_ in ROWS:
        system_lost[system] += points(q)
    priority = sorted(system_counter, key=lambda s: (-system_lost[s], -system_counter[s]))
    p_rows = [["顺位", "系统", "错题数", "失分"]]
    for idx, system in enumerate(priority, 1):
        p_rows.append([str(idx), system, str(system_counter[system]), f"{system_lost[system]:g}"])
    pt = Table([[Paragraph(esc(c), small) for c in row] for row in p_rows], colWidths=[18 * mm, 88 * mm, 28 * mm, 26 * mm])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163F49")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D3D8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [pt, Spacer(1, 5 * mm)]
    story += [
        Paragraph("建议先用 7 天完成一轮：前 3 天复习消化/肝胆胰、呼吸、肾脏与体液；第 4-5 天复习基础机制、血液肿瘤、心血管；第 6 天复习感觉/内分泌/骨科；第 7 天只做 56 题的遮答复测。若将 15 道 X 型错题全部改正，总分可先回到 228 分。", body),
        PageBreak(),
    ]

    by_system = defaultdict(list)
    for row in ROWS:
        by_system[row[1]].append(row)

    for system in priority:
        rows = sorted(by_system[system], key=lambda r: r[0])
        story += [Paragraph(system, h1), Paragraph(f"本系统 {len(rows)} 道错题，共失分 {system_lost[system]:g} 分。", subtitle)]
        for q, _, discipline, answer, lecture, lecture_page, recap, trap in rows:
            item = questions[q]
            header_data = [[
                Paragraph(f"<b>Q{q}</b>", body),
                Paragraph(f"{discipline} · {qtype(q)} · {points(q):g}分", small),
                Paragraph(f"<b>正确 {answer}</b>", label_style),
            ]]
            ht = Table(header_data, colWidths=[24 * mm, 101 * mm, 35 * mm])
            ht.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E7F2EF")),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#A8C9C3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            block = [ht, Spacer(1, 2.5 * mm), Paragraph(esc(item["stem"]), question_style)]
            for key in "ABCD":
                text = item["options"].get(key, "")
                if key in set(answer):
                    line = f"<font color='#0B6B62'><b>{key}. {esc(text)}</b></font>"
                else:
                    line = f"{key}. {esc(text)}"
                block.append(Paragraph(line, option_style))
            block += [
                Spacer(1, 1.5 * mm),
                Paragraph(f"<b>讲义回扣</b> · {esc(lecture)} · p.{esc(lecture_page)}", label_style),
                Paragraph(esc(recap), body),
                Paragraph(f"<b>错因定位 / 复盘动作：</b>{esc(trap)}", small),
                Spacer(1, 5 * mm),
            ]
            story.append(KeepTogether(block))
        story.append(PageBreak())

    story += [
        Paragraph("使用说明", h1),
        Paragraph("计分假设：你列出的题号均为错题，其余题目均作答且正确；X 型题按多选、少选、错选均不得分处理。若仍有未作答或题号录入错误，总分需相应调整。", body),
        Paragraph("题目来源：用户提供的《【基础强化】摸底考试 天天师兄27考研 冲刺押题见！》PDF。原卷未附完整答案表；本错题本依据当前工作区中的 2027 天天师兄生理、生化、病理、内科和外科讲义数据逐项核对，并以讲义页码作为回看定位。", body),
        Paragraph("建议复测方法：第 1 轮遮住答案和讲义回扣，限时 70 分钟完成；第 2 轮只复习再错题；第 3 轮把错题改写为一句“触发词 -> 结论”。", body),
    ]

    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()
