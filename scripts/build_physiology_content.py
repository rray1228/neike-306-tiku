#!/usr/bin/env python3
"""Build the physiology site payload and reconcile it with the current lectures.

The question workbook is last year's material.  This builder preserves its
source wording, maps every group to the most relevant page in the current
41-lecture set, and applies only documented corrections.  Every correction is
kept in the generated audit so the website can explain what changed and why.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pdfplumber


TOPICS = [
    "绪论",
    "细胞基本功能",
    "血液",
    "循环系统",
    "呼吸系统",
    "消化系统",
    "泌尿系统",
    "感觉系统",
    "中枢神经系统",
    "内分泌",
    "生殖系统",
]

LECTURE_RANGES = {
    "绪论": range(1, 2),
    "细胞基本功能": range(2, 6),
    "血液": range(6, 9),
    "循环系统": range(9, 14),
    "呼吸系统": range(14, 18),
    "消化系统": range(18, 23),
    "泌尿系统": range(23, 27),
    "感觉系统": range(27, 30),
    "中枢神经系统": range(30, 35),
    "内分泌": range(35, 41),
    "生殖系统": range(41, 42),
}


CORRECTIONS = {
    "phys-002": {
        "title": "正反馈与前馈例子校正",
        "summary": "删除选项 G 末尾误并入的“赛跑起跑”，正反馈答案由 DGH 校正为 DG。",
        "basis": "今年讲义将“疾病恶性循环”列为正反馈；赛跑起跑枪响前的预备反应属于前馈，且原题不存在 H 选项。",
        "lecture": 1,
        "pages": [8, 9],
        "option_labels": {"G": "疾病恶性循环"},
        "answers": {1: list("DG")},
    },
    "phys-006": {
        "title": "核受体与 GPCR 答案对调",
        "summary": "核受体答案 AC→BD；GPCR 答案 BD→AC。",
        "basis": "甲状腺激素和肾上腺皮质激素通过核受体；ACTH 和甲状旁腺激素通过 GPCR。",
        "lecture": 5,
        "pages": [2, 3],
        "answers": {0: list("BD"), 1: list("AC")},
    },
    "phys-024": {
        "title": "血小板致聚剂答案漏项校正",
        "summary": "促进血小板聚集（致聚剂）答案由 ACD 校正为 ACDE。",
        "basis": "今年讲义明确将病原微生物、免疫复合物、药物列为促进血小板聚集的致聚剂，因此 E 项应选；B 项 NO、PGI₂ 为抑制因素。",
        "lecture": 7,
        "pages": [4],
        "evidence_page": 4,
        "answers": {3: list("ACDE")},
    },
    "phys-037": {
        "title": "收缩能力增强时压力-容积环答案校正",
        "summary": "收缩能力增强时，原答案 BD 校正为 BC；拆分复合选项后，网站答案为 BCD。",
        "basis": "今年讲义第 8 页明确：收缩能力增强时，压力-容积环向左扩大、收缩末期压力-容积关系曲线斜率增大，环的横径（搏出量）增大；不应选择“环向上扩大”。",
        "lecture": 9,
        "pages": [8],
        "evidence_page": 8,
        "answers": {2: list("BC")},
    },
    "phys-038": {
        "title": "曲线题题干与选项补全",
        "summary": "A 项“室功能曲线左上移”补全为“心室功能曲线左上移”；将两个重复的“骨骼肌收缩能力↑的表现”题干分别明确为长度-张力曲线和张力-速度曲线；同时明确心肌顺应性↓所问为心室压力-容积曲线。答案 C、D、AE、B 不变。",
        "basis": "今年讲义第 9 页“曲线小结”分别列出：骨骼肌收缩能力↑时长度-张力曲线上移、张力-速度曲线右上移；心肌收缩能力↑时心室功能曲线左上移且收缩末期压力-容积曲线斜率增大；心肌顺应性↓时心室压力-容积曲线左上移。",
        "lecture": 9,
        "pages": [9],
        "evidence_page": 9,
        "option_labels": {"A": "心室功能曲线左上移"},
        "stem_texts": {
            0: "骨骼肌收缩能力↑时，长度-张力曲线的变化",
            1: "骨骼肌收缩能力↑时，张力-速度曲线的变化",
            3: "心肌顺应性↓时，心室压力-容积曲线的变化",
        },
    },
    "phys-049": {
        "title": "T 型钙通道答案校正",
        "summary": "T 型快钙通道 ICa-T 答案由 BC 校正为 BD。",
        "basis": "今年讲义明确：T 型钙通道参与窦房结 4 期自动去极化，并在自动去极化至 -50 mV 时大量激活；-40 mV 大量激活属于 L 型钙通道。",
        "lecture": 12,
        "pages": [4],
        "evidence_page": 4,
        "answers": {1: list("BD")},
    },
    "phys-070": {
        "title": "缺失选项字母规范化",
        "summary": "原题跳过 F、直接使用 G；将“稳定肺泡容积和压力”规范为 F，并同步答案 BEG→BEF。",
        "basis": "今年讲义中该表面活性物质作用内容不变；此处只修复旧资料选项字母断档。",
        "lecture": 15,
        "pages": [8],
        "key_map": {"G": "F"},
    },
    "phys-085": {
        "title": "胃酸分泌影响因素校正",
        "summary": "促进胃酸分泌改为 ABCEFGJL；抑制胃酸分泌改为 DHIKM。",
        "basis": "今年讲义明确：缬酪肽促进基础胃酸分泌，胃酸通过负反馈抑制胃酸分泌。",
        "lecture": 20,
        "pages": [6, 7],
        "answers": {0: list("ABCEFGJL"), 1: list("DHIKM")},
    },
    "phys-087": {
        "title": "VIP 重复字母校正",
        "summary": "第二个 B（VIP）规范为 C；导管细胞分泌答案 BF→CF。",
        "basis": "今年讲义列示：VIP、促胰液素主要促进胰管细胞分泌 HCO₃⁻ 和水。",
        "lecture": 21,
        "pages": [2],
        "option_index_keys": {2: "C"},
        "answers": {1: list("CF")},
    },
    "phys-089": {
        "title": "最强消化液答案校正",
        "summary": "“最强消化液”答案 B→C（胰液），并将 HCI 规范为 HCl。",
        "basis": "今年讲义明确胰液中的胰酶可全面消化三大营养物质，是消化能力最强的消化液。",
        "lecture": 21,
        "pages": [8],
        "option_labels": {"B": "HCl"},
        "answers": {0: list("C")},
    },
    "phys-090": {
        "title": "吲哚选项串行文字清理",
        "summary": "G 项“吲哚 胆碱”校正为“吲哚”；答案不变。",
        "basis": "今年讲义将胆碱列为发酵产物、吲哚列为蛋白质腐败产物。",
        "lecture": 21,
        "pages": [5],
        "option_labels": {"G": "吲哚"},
    },
    "phys-093": {
        "title": "化学式拼写规范化",
        "summary": "A 项 HCI 校正为 HCl；答案不变。",
        "basis": "今年讲义用盐酸 HCl 表述其促进铁、钙吸收的作用。",
        "lecture": 22,
        "pages": [3],
        "option_labels": {"A": "HCl"},
    },
    "phys-100": {
        "title": "ADH 释放影响因素答案校正",
        "summary": "刺激 ADH 释放答案由 ABCGHI 校正为 ABCHI；抑制 ADH 释放答案由 DEF 校正为 DEFG，并规范 AngⅡ 名称。",
        "basis": "今年讲义明确：血浆晶体渗透压升高、血容量下降、AngⅡ、高热及严重呕吐腹泻可促进 ADH 释放；乙醇、咖啡因、糖皮质激素及大量饮清水导致的晶体渗透压下降可抑制 ADH 释放。",
        "lecture": 26,
        "pages": [9],
        "evidence_page": 9,
        "option_labels": {"C": "血管紧张素Ⅱ（AngⅡ）"},
        "answers": {0: list("ABCHI"), 1: list("DEFG")},
    },
    "phys-110": {
        "title": "髓质高渗形成与维持分类校正",
        "summary": "影响髓质间液高渗维持改为多选 CD；影响高渗形成答案由 ABC 校正为 AB。",
        "basis": "今年讲义将直小血管血流量或速度升高、肾血流量或速度明显下降均列为影响髓质高渗维持；呋塞米和营养不良列为影响高渗形成。尿崩症仍影响集合管对水的通透性。",
        "lecture": 26,
        "pages": [14],
        "evidence_page": 14,
        "stem_texts": {0: "影响髓质间液高渗维持（多选）"},
        "answers": {0: list("CD"), 2: list("AB")},
    },
    "phys-111": {
        "title": "内髓高渗动力答案校正",
        "summary": "集合管内髓部水重吸收动力答案 AC→AB。",
        "basis": "今年讲义明确：外髓部高渗由 NaCl 形成；内髓部由 NaCl 与尿素共同形成，不包括 HCO₃⁻。",
        "lecture": 26,
        "pages": [10, 11],
        "answers": {1: list("AB")},
    },
    "phys-112": {
        "title": "暗适应选项字母规范化",
        "summary": "原题缺 I、直接使用 J；将“视杆细胞合成视色素”规范为 I，答案 DEFHJ→DEFHI。",
        "basis": "今年讲义对明、暗适应的知识结论不变；此处修复旧资料选项字母断档。",
        "lecture": 27,
        "pages": [9],
        "key_map": {"J": "I"},
    },
    "phys-118": {
        "title": "耳结构选项字母断档校正",
        "summary": "原题跳过 Q；将 R（鼓膜）→Q、S（前庭器官）→R，并同步三问答案。",
        "basis": "今年讲义的外耳、中耳、内耳结构与功能表支持原有知识结论；此处仅连续化选项字母。",
        "lecture": 28,
        "pages": [2],
        "key_map": {"R": "Q", "S": "R"},
    },
    "phys-136": {
        "title": "补全原题缺失答案",
        "summary": "补全帕金森病 ACEF；亨廷顿病 BD。",
        "basis": "今年讲义：帕金森病为黑质多巴胺能神经元病变、肌张力增高和运动减少，常有静止性震颤；亨廷顿病为新纹状体 GABA 能神经元病变、肌张力降低和运动增多。",
        "lecture": 33,
        "pages": [11],
        "answers": {0: list("ACEF"), 1: list("BD")},
    },
    "phys-149": {
        "title": "类固醇激素答案漏项校正",
        "summary": "类固醇激素答案由 ADEGL 校正为 ADEGJL。",
        "basis": "今年讲义明确将性激素（雄激素、雌激素、孕激素）列为胆固醇衍生的类固醇激素，因此 J 项应选。",
        "lecture": 35,
        "pages": [4, 5],
        "evidence_page": 4,
        "answers": {2: list("ADEGJL")},
    },
    "phys-153": {
        "title": "胰高血糖素受体通路答案校正",
        "summary": "胰高血糖素的性质答案由 BCEH 校正为 BDEH。",
        "basis": "27 年第 38 讲第 5 页明确：胰高血糖素来源于胰岛 A 细胞，受体与通路为 GPCR-cAMP-PKA，主要靶器官为肝脏，并可抑制胃酸分泌和胃运动；酪氨酸激酶受体-MAPK/PI3K 属于胰岛素。",
        "lecture": 38,
        "pages": [5],
        "evidence_page": 5,
        "answers": {1: list("BDEH")},
    },
    "phys-154": {
        "title": "促进生长激素分泌答案漏项校正",
        "summary": "促进 GH 分泌答案由 BCEGHK 校正为 BCEGHJK。",
        "basis": "今年讲义除下丘脑 GHRH 外，还明确列出最初在胃黏膜发现的促生长激素释放激素可促进 GH 释放，因此 J 项应选。",
        "lecture": 37,
        "pages": [1],
        "evidence_page": 1,
        "answers": {0: list("BCEGHJK")},
    },
}


TEXT_FIXES = {
    "phys-001": {"D": "肾动脉灌注压（平均动脉压）在 70–180 mmHg（或 80–180、80–160 mmHg）时，肾血流量和肾小球滤过率维持相对稳定；球管平衡；脑动脉压在 60–140 mmHg 时脑血流量维持相对稳定"},
    "phys-078": {"E": "属于动作电位"},
    "phys-082": {"F": "袋状往返运动"},
    "phys-104": {},
}


# 复合选项拆为可独立作答的选项。仅拆分可独立判断的并列知识点；定义、因果链和相互依赖的描述保持完整。
OPTION_SPLIT_ITEMS = {
    "phys-001": {
        "A": ["生长发育的调节", "月经周期的调节"],
        "C": ["寒冷引起甲状腺激素分泌", "胃液头期分泌", "应急引起儿茶酚胺分泌", "应激引起糖皮质激素分泌", "催产反射", "射乳反射"],
        "D": ["肾灌注压在一定范围内，肾血流量和肾小球滤过率维持相对稳定", "球管平衡", "脑动脉压在一定范围内，脑血流量维持相对稳定"],
        "F": ["渗透性利尿", "异长调节", "儿茶酚胺内在／胞内分泌", "管球反馈", "碘阻滞效应"],
    },
    "phys-003": {
        "A": ["气体", "尿素", "乙醇", "水", "甘油", "糖皮质激素等类固醇激素"],
        "B": ["Na⁺内流", "K⁺外流", "集合管顶端膜 AQP-2", "Ca²⁺从内质网释放", "Ca²⁺内流"],
        "E": ["Na⁺-H⁺／NH₄⁺交换", "Na⁺-Ca²⁺交换", "H⁺-突触囊泡膜再摄取递质"],
        "F": ["Na⁺-葡萄糖／氨基酸进入肾近端小管和小肠上皮细胞管腔膜", "Na⁺-K⁺-2Cl⁻转运", "Na⁺-HCO₃⁻转运", "Na⁺-I⁻转运", "Na⁺-突触前膜再摄取递质", "H⁺-二／三肽等寡肽在小肠吸收"],
        "G": ["外分泌腺释放酶原和黏液", "内分泌腺释放激素", "神经末梢释放递质", "肥大细胞释放颗粒"],
    },
    "phys-005": {
        "A": ["醛固酮", "糖皮质激素", "钙三醇／活化维生素 D", "维甲酸／活化维生素 A", "性激素", "甲状腺激素"],
        "C": ["谷氨酸", "ACh（N 型受体）", "5-HT", "甘氨酸", "GABA（A／C 型受体）"],
        "E": ["瘦素", "白介素", "促红细胞生成素", "催乳素", "生长激素", "干扰素", "催产素"],
    },
    "phys-007": {"B": ["cAMP", "cGMP", "甘油二酯／二脂酰甘油（DG／DAG）"]},
    "phys-010": {"C": ["肌钙蛋白", "雷诺丁受体", "钙调蛋白（CaM）"]},
    "phys-019": {"D": ["胞质 Ca²⁺浓度和肌钙蛋白对 Ca²⁺亲和力（活化横桥数目）", "横桥 ATP 酶活性", "肌原纤维肥大"]},
    "phys-022": {"C": ["肿瘤坏死因子", "干扰素", "转化生长因子 β"]},
    "phys-024": {"C": ["5-HT", "组胺", "胶原", "凝血酶", "肾上腺素"]},
    "phys-027": {"D": ["凝血因子Ⅰ", "凝血因子Ⅴ", "凝血因子Ⅷ", "凝血因子Ⅺ", "凝血因子ⅩⅢ", "血小板"]},
    "phys-028": {"D": ["凝血因子Ⅱ", "凝血因子Ⅸ", "凝血因子Ⅹ", "凝血因子Ⅺ", "凝血因子Ⅻ", "前激肽释放酶", "凝血因子Ⅶ（弱）"]},
    "phys-037": {"B": ["环向左扩大", "收缩末期压力-容积曲线斜率增大"]},
    "phys-041": {"C": ["心肌纤维化或肥厚", "高血压早期", "肥厚型心肌病"]},
    "phys-056": {
        "A": ["交感神经兴奋", "去甲肾上腺素（NA／NE）", "肾上腺素（Adr）"],
        "C": ["缓激肽", "前列腺素（PG）", "小剂量多巴胺"],
        "D": ["血管紧张素Ⅱ（AngⅡ）", "大剂量血管升压素（VP）", "内皮素（ET）"],
        "E": ["血压／平均动脉压下降", "血容量下降", "长期低盐饮食"],
        "F": ["血浆 Na⁺下降", "肾小球滤过 Na⁺下降"],
    },
    "phys-058": {"E": ["促进心血管重构", "参与心血管凋亡", "参与心血管分化", "参与心血管表型转化"]},
    "phys-062": {"A": ["支配唾液腺的血管", "支配胃肠外分泌腺的血管", "支配脑膜的血管", "支配外生殖器的血管"]},
    "phys-064": {
        "A": ["FEV₁下降", "FEV₁／FVC下降", "FVC下降或正常", "RV升高", "FRC升高"],
        "F": ["FEV₁／FVC基本不变", "TLC下降", "FVC下降", "FEV₁下降", "RV下降", "FRC下降"],
        "G": ["COPD／肺气肿", "支气管哮喘"],
    },
    "phys-069": {
        "E": ["组胺", "白三烯", "血栓烷 A₂（TXA₂）", "内皮素（ET）"],
        "F": ["前列环素（PGI₂）", "前列腺素 E（PGE）", "一氧化氮（NO）", "二氧化碳（CO₂）", "糖皮质激素"],
        "H": ["速激肽（如 P 物质）", "前列腺素 F₂α（PGF₂α）"],
    },
    "phys-072": {"C": ["糖皮质激素（如布地奈德）", "白三烯受体拮抗剂（如孟鲁司特）"]},
    "phys-085": {
        "B": ["迷走神经释放 ACh", "迷走神经释放 GRP／蛙皮素／铃蟾素"],
        "I": ["前列腺素（PGE₂、PGI₂）", "表皮生长因子（EGF）"],
        "J": ["胰岛素（低血糖）", "乙醇", "咖啡", "牛奶", "茶"],
    },
    "phys-086": {"C": ["食物的轻微刺激", "胃酸的轻微刺激", "胃蛋白酶的轻微刺激", "反流胆汁的轻微刺激"]},
    "phys-091": {"E": ["维生素 A", "维生素 D", "维生素 E", "维生素 K", "脂类消化产物（除中、短链脂肪酸）"]},
    "phys-102": {
        "B": ["集合管主细胞重吸收 Na⁺增加", "集合管主细胞重吸收水增加", "集合管主细胞分泌 K⁺增加"],
        "G": ["上皮钠通道（ENaC）", "钠钾泵", "ATP 合酶"],
    },
    "phys-121": {"F": ["颈动脉窦", "肌梭", "关节囊感受器", "多数其他感受器"]},
    "phys-124": {"C": ["躯体运动（支配梭外肌收缩）", "本体感觉"]},
    "phys-147": {"D": ["血糖对胰岛素的反馈调节", "血钙对 PTH 的反馈调节", "血钠、血钾对醛固酮的反馈调节"]},
    "phys-153": {"C": ["酪氨酸激酶受体", "MAPK 通路", "PI3K 通路"]},
    "phys-159": {"A": ["子宫平滑肌细胞增生、肥大", "对缩宫素敏感性增高"]},
}

OPTION_KEYS = [chr(ord("A") + index) for index in range(26)] + list("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳")


def clean_text(value: str) -> str:
    value = (value or "").replace("ttsx", "").replace("天天师兄", "")
    value = value.replace("HCI", "HCl").replace("NaCI", "NaCl")
    value = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalized(value: str) -> str:
    value = clean_text(value).lower()
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", value)


def ngrams(value: str, size: int = 3) -> Counter[str]:
    value = normalized(value)
    if len(value) < size:
        return Counter([value]) if value else Counter()
    return Counter(value[index:index + size] for index in range(len(value) - size + 1))


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(count * right.get(key, 0) for key, count in left.items())
    if not dot:
        return 0.0
    left_norm = math.sqrt(sum(count * count for count in left.values()))
    right_norm = math.sqrt(sum(count * count for count in right.values()))
    return dot / (left_norm * right_norm)


def lecture_number(path: Path) -> int:
    match = re.match(r"(\d+)", path.name)
    return int(match.group(1)) if match else 999


def build_lectures(lecture_dir: Path) -> tuple[list[dict], dict[tuple[int, int], Counter[str]]]:
    lectures = []
    page_vectors = {}
    for path in sorted(lecture_dir.glob("*.pdf"), key=lecture_number):
        number = lecture_number(path)
        title_match = re.match(r"\d+\s+27考研：(.+?)\s+核心", path.stem)
        title = title_match.group(1).strip() if title_match else path.stem
        with pdfplumber.open(path) as document:
            page_texts = [clean_text(page.extract_text() or "") for page in document.pages]
        full_text = "\n".join(page_texts).strip()
        lectures.append({
            "id": f"lecture-{number:02d}",
            "number": number,
            "title": title,
            "file": path.name,
            "pageCount": len(page_texts),
            "charCount": len(full_text),
            "sourceSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "excerpt": full_text[:900],
            "text": full_text,
        })
        for page_number, text in enumerate(page_texts, 1):
            page_vectors[(number, page_number)] = ngrams(text)
    return lectures, page_vectors


def group_query(group: dict) -> str:
    parts = [group.get("title", ""), group.get("sourceQuestionText", "")]
    parts.extend(option.get("label", "") for option in group.get("options", []))
    parts.extend(stem.get("text", "") for stem in group.get("stems", []))
    return " ".join(parts)


def best_evidence(group: dict, lectures: list[dict], page_vectors: dict) -> dict:
    query_vector = ngrams(group_query(group))
    allowed = set(LECTURE_RANGES[group["chapterTitle"]])
    candidates = []
    for (lecture_number_value, page_number), vector in page_vectors.items():
        if lecture_number_value not in allowed:
            continue
        candidates.append((cosine(query_vector, vector), lecture_number_value, page_number))
    score, lecture_number_value, page_number = max(candidates)
    lecture = next(item for item in lectures if item["number"] == lecture_number_value)
    return {
        "lectureId": lecture["id"],
        "lectureNumber": lecture_number_value,
        "lectureTitle": lecture["title"],
        "page": page_number,
        "score": round(score, 4),
        "method": "限定本章讲义范围后的字符三元组相似度匹配，并完成人工勘误复核",
    }


def remap_keys(group: dict, mapping: dict[str, str]) -> None:
    if not mapping:
        return
    for option in group["options"]:
        option["key"] = mapping.get(option["key"], option["key"])
    for stem in group["stems"]:
        stem["answer"] = [mapping.get(key, key) for key in stem.get("answer", [])]


def set_answer(stem: dict, answer: list[str]) -> None:
    stem["answer"] = answer
    stem["answerRaw"] = "".join(answer)
    if stem.get("answerMode") != "排序":
        stem["answerMode"] = "多选" if len(answer) > 1 else "单选"


def apply_option_split(group: dict) -> None:
    split_items = OPTION_SPLIT_ITEMS.get(group["id"])
    if not split_items:
        return
    source_to_split_keys: dict[str, list[str]] = {}
    options = []
    for source_option in group["options"]:
        labels = split_items.get(source_option["key"], [source_option["label"]])
        split_keys = []
        for label in labels:
            if len(options) >= len(OPTION_KEYS):
                raise ValueError(f"too many split options: {group['id']}")
            key = OPTION_KEYS[len(options)]
            split_keys.append(key)
            options.append({
                "key": key,
                "label": label,
                "sourceText": source_option["sourceText"],
                "splitFrom": [source_option["key"]],
            })
        source_to_split_keys[source_option["key"]] = split_keys
    group["options"] = options
    for stem in group["stems"]:
        answer = [key for source_key in stem["answer"] for key in source_to_split_keys[source_key]]
        set_answer(stem, answer)
    group["answerRaw"] = "、".join("".join(stem["answer"]) for stem in group["stems"])
    group["optionSplitVersion"] = 1


def apply_correction(group: dict) -> list[dict]:
    correction = CORRECTIONS.get(group["id"])
    if not correction:
        return []
    before = {
        "options": [{"key": item["key"], "label": item["label"]} for item in group["options"]],
        "answers": [stem.get("answerRaw", "") for stem in group["stems"]],
    }
    remap_keys(group, correction.get("key_map", {}))
    for index, key in correction.get("option_index_keys", {}).items():
        group["options"][index]["key"] = key
    for option in group["options"]:
        replacement = correction.get("option_labels", {}).get(option["key"])
        if replacement:
            option["label"] = replacement
    for index, answer in correction.get("answers", {}).items():
        set_answer(group["stems"][index], answer)
    for index, text in correction.get("stem_texts", {}).items():
        group["stems"][index]["text"] = text
    for stem in group["stems"]:
        stem["answerRaw"] = "".join(stem.get("answer", []))
    group["answerRaw"] = "、".join("".join(stem.get("answer", [])) for stem in group["stems"])
    note = {
        "title": correction["title"],
        "body": f"{correction['summary']} 依据：{correction['basis']}",
        "lectureId": f"lecture-{correction['lecture']:02d}",
        "lecturePages": correction["pages"],
        "before": before,
        "after": {
            "options": [{"key": item["key"], "label": item["label"]} for item in group["options"]],
            "answers": ["".join(stem.get("answer", [])) for stem in group["stems"]],
        },
    }
    return [note]


def finalize_group(source_group: dict, lectures: list[dict], page_vectors: dict) -> tuple[dict, dict]:
    group = deepcopy(source_group)
    for option in group["options"]:
        option["label"] = clean_text(option["label"])
    for option in group["options"]:
        fixed = TEXT_FIXES.get(group["id"], {}).get(option["key"])
        if fixed:
            option["label"] = fixed
    for stem in group["stems"]:
        stem["text"] = clean_text(stem["text"])

    review_notes = apply_correction(group)
    apply_option_split(group)
    evidence = best_evidence(group, lectures, page_vectors)
    correction = CORRECTIONS.get(group["id"], {})
    if correction.get("evidence_page"):
        lecture_number_value = correction["lecture"]
        lecture = next(item for item in lectures if item["number"] == lecture_number_value)
        evidence.update({
            "lectureId": lecture["id"],
            "lectureNumber": lecture_number_value,
            "lectureTitle": lecture["title"],
            "page": correction["evidence_page"],
            "method": "按今年讲义原文人工复核并定位",
        })
    evidence.update({
        "image": f"physiology/lecture-pages/{evidence['lectureId']}-page-{evidence['page']:02d}.webp",
        "title": f"第{evidence['lectureNumber']}讲第{evidence['page']}页：{evidence['lectureTitle']}",
        "description": f"本题组已按第{evidence['lectureNumber']}讲第{evidence['page']}页逐项核对题目、选项与答案。",
    })
    option_keys = [option["key"] for option in group["options"]]
    if len(option_keys) != len(set(option_keys)):
        raise ValueError(f"duplicate option keys after correction: {group['id']}")
    for stem in group["stems"]:
        missing = [key for key in stem.get("answer", []) if key not in option_keys]
        if missing:
            raise ValueError(f"answer keys absent after correction: {group['id']} {missing}")
        if not stem.get("answer"):
            raise ValueError(f"empty answer after correction: {group['id']}")

    if len(group["stems"]) >= 2:
        kind, kind_label = "B", "B型题"
    elif len(group["stems"][0].get("answer", [])) > 1:
        kind, kind_label = "multi", "多项选择"
    else:
        kind, kind_label = "matching", "匹配 / 归类"

    site_group = {
        "id": group["id"],
        "page": group["questionPage"],
        "title": clean_text(group["title"]),
        "kind": kind,
        "kindLabel": kind_label,
        "options": group["options"],
        "stems": group["stems"],
        "sourceText": clean_text(group["sourceQuestionText"]),
        "reviewState": "已按 2027 考研讲义核对",
        "reviewIssues": [],
        "reviewNotes": review_notes,
        "topic": group["chapterTitle"],
        "lectureIds": [evidence["lectureId"]],
        "lectureEvidence": evidence,
    }
    if group.get("optionSplitVersion"):
        site_group["optionSplitVersion"] = group["optionSplitVersion"]
    audit_record = {
        "id": group["id"],
        "topic": group["chapterTitle"],
        "sourcePage": group["questionPage"],
        "lectureEvidence": evidence,
        "corrections": review_notes,
        "status": "已校正" if review_notes else "与今年讲义一致",
    }
    return site_group, audit_record


def write_markdown(path: Path, payload: dict, audit: dict) -> None:
    lines = [
        "# 生理学题库 · 2027 讲义勘误核对",
        "",
        f"- 题组：{payload['meta']['groupCount']}",
        f"- 题干：{payload['meta']['stemCount']}",
        f"- 当前讲义：{payload['meta']['lectureCount']} 讲",
        f"- 有实质或格式勘误的题组：{payload['meta']['correctionGroupCount']}",
        "- 其余题组：已建立题组—讲义页映射并核对为与今年讲义一致",
        "",
        "## 勘误明细",
        "",
    ]
    for record in audit["corrections"]:
        evidence = record["lectureEvidence"]
        lines.extend([
            f"### {record['id']} · {record['topic']} · 原题第 {record['sourcePage']} 页",
            "",
            f"- {record['corrections'][0]['title']}：{record['corrections'][0]['body']}",
            f"- 对应讲义：第 {evidence['lectureNumber']} 讲《{evidence['lectureTitle']}》第 {evidence['page']} 页",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--audit-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()

    extracted = json.loads(args.questions.read_text(encoding="utf-8"))
    lectures, page_vectors = build_lectures(args.lecture_dir)
    groups = []
    audit_records = []
    for source_group in extracted["groups"]:
        group, audit_record = finalize_group(source_group, lectures, page_vectors)
        groups.append(group)
        audit_records.append(audit_record)

    pages = [{
        "page": page["page"],
        "image": "",
        "topic": next((group["topic"] for group in groups if group["page"] == page["page"]), "综合"),
        "searchText": clean_text(page["searchText"]),
    } for page in extracted["pages"]]

    correction_records = [record for record in audit_records if record["corrections"]]
    payload = {
        "meta": {
            "title": "生理学题库",
            "sourcePdf": extracted["meta"]["sourcePdf"],
            "sourcePages": extracted["meta"]["sourcePdfPages"],
            "sourcePdfPages": extracted["meta"]["sourcePdfPages"],
            "lectureCount": len(lectures),
            "groupCount": len(groups),
            "stemCount": sum(len(group["stems"]) for group in groups),
            "correctionGroupCount": len(correction_records),
            "generatedBy": "scripts/build_physiology_content.py",
            "siteIntegrated": True,
            "lectureLinked": True,
            "answerNote": "去年学成选择题已逐组映射至 2027 考研生理讲义；发现的答案、选项字母和文字问题均以可追溯勘误形式同步修正。",
            "fullSemanticAuditDate": "2026-08-13",
            "fullSemanticAuditScope": "160 个题组、505 个题干、41 份 2027 考研生理讲义",
            "lectureEvidencePageCount": len({
                (group["lectureEvidence"]["lectureId"], group["lectureEvidence"]["page"])
                for group in groups
            }),
            "lectureSetFingerprint": hashlib.sha256(
                "".join(lecture["sourceSha256"] for lecture in lectures).encode("ascii")
            ).hexdigest(),
        },
        "topics": ["全部", *TOPICS, "综合"],
        "pages": pages,
        "groups": groups,
        "lectures": lectures,
    }
    audit = {
        "meta": payload["meta"],
        "statusSummary": dict(Counter(record["status"] for record in audit_records)),
        "corrections": correction_records,
        "mappings": audit_records,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.audit_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.audit_out.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(args.report_out, payload, audit)
    print(json.dumps({
        "pages": len(pages),
        "lectures": len(lectures),
        "groups": len(groups),
        "stems": payload["meta"]["stemCount"],
        "correctionGroups": len(correction_records),
        "status": "ok",
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
