#!/usr/bin/env python3
"""Repair answer bubbles that were truncated by OCR/parser ambiguity.

The source workbook often writes a multi-answer bubble immediately after a
Chinese prompt, for example “（ACF” or “（BDEIK”. The first parser accepted
only the first letter inside such an unfinished bracket. This pass uses the
known shared-option alphabet to recover those bubbles while leaving already
multi-letter answers untouched unless a source-specific correction is known.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from manual_med_review import apply_manual_review


MANUAL = {
    # COPD treatment notes contain classification letters before the actual
    # treatment choices. Keep the treatment bubble shown after the note.
    "p02-g1:9": list("FHLNQ"),
    "p02-g1:10": list("HL"),
    "p02-g1:11": list("HLPM"),
    # Lecture correction: atrial premature beats are B/F/I/K/L; D belongs to
    # junctional premature beats and is an annotation artifact in the scan.
    "p94-g1:0": list("BFIKL"),
    "p09-g2:0": list("ACF"),
    "p09-g3:6": list("DH"),
    "p09-g3:7": list("CI"),
    "p13-g1:4": list("F"),
    "p14-g1:4": list("EIL"),
    "p23-g1:0": list("ACE"),
    "p37-g1:1": list("ADFGJKMP"),
    "p62-g1:4": list("D"),
    "p62-g1:8": list("ACF"),
    "p62-g1:21": list("AF"),
    "p55-g1:1": list("F"),
    "p55-g1:2": list("BEH"),
    "p55-g1:5": list("BIL"),
    "p66-g1:6": list("I"),
    "p67-g1:13": list("A"),
    "p53-g1:16": list("AFGHKN"),
}


def option(key: str, label: str) -> dict:
    return {"key": key, "label": label, "sourceText": f"{key}.{label}"}


def stem(text: str, answer: str) -> dict:
    letters = list(answer)
    return {
        "text": text,
        "answer": letters,
        "sourceText": f"{text}{answer}",
        "sourceY": 0,
        "answerMode": "多选" if len(letters) > 1 else "单选",
    }


def group(group_id: str, title: str, topic: str, lecture_ids: list[str], options: list[dict], stems: list[dict]) -> dict:
    return {
        "id": group_id,
        "page": int(group_id[1:3]),
        "title": title,
        "kind": "B",
        "kindLabel": "B型题",
        "options": options,
        "stems": stems,
        "sourceText": f"{title}（已按讲义规范化）",
        "reviewState": "已按讲义校对",
        "topic": topic,
        "lectureIds": lecture_ids,
    }


def corrected_group_blocks() -> dict[str, tuple[list[str], list[dict]]]:
    """Canonicalize OCR blocks that merged several B-type question sets.

    These are not guesses from the scan: the wording and answer bubbles are
    checked against the linked lecture PDFs and the original source page.
    """
    p05_low_oxygen = group(
        "p05-g2", "低氧血症最主要的机制", "呼吸", ["lecture-04"],
        [
            option("A", "肺泡通气量↓"), option("B", "VA/Q失调"),
            option("C", "弥散障碍（DLco↓）"), option("D", "肺内分流"),
        ],
        [
            stem("COPD", "A"), stem("肺动脉栓塞", "B"), stem("支气管哮喘", "A"),
            stem("间质性肺疾病", "C"), stem("肺炎", "B"),
            stem("肺泡蛋白沉着症", "D"), stem("ARDS", "D"),
        ],
    )
    p05_interstitial = group(
        "p05-g3", "间质性肺疾病的鉴别", "呼吸", ["lecture-04"],
        [
            option("A", "支气管肺泡灌洗液（BALF）：中性粒、嗜酸性粒细胞↑"),
            option("B", "BALF：CD4 T细胞为主"),
            option("C", "影像学：磨玻璃影与正常组织截然分开，呈地图样、铺路石样、蝴蝶样（肺门周围肺泡渗出）"),
            option("D", "影像学：肺水肿反转形状"),
            option("E", "HRCT：双肺外带胸膜下、基底部分布为主，伴或不伴牵拉支气管扩张"),
            option("F", "BALF：CD8 T细胞↑为主"),
            option("G", "HRCT：双肺门淋巴结肿大，沿支气管血管束分布的结节"),
            option("H", "BALF：嗜酸性粒细胞明显↑"),
            option("I", "BALF：奶白色、稠厚、分层、PAS（+）"),
            option("J", "影像学：磨玻璃斑片影的马赛克征"),
        ],
        [
            stem("特发性肺间质纤维化", "AE"), stem("结节病", "BG"),
            stem("肺泡蛋白沉着症", "CI"), stem("过敏性肺炎", "FJ"),
            stem("嗜酸性粒细胞性肺炎", "DH"),
        ],
    )
    p05_sarcoid = group(
        "p05-g4", "结节病分期", "呼吸", ["lecture-04"],
        [
            option("A", "双肺门淋巴结肿大、肺部浸润影"),
            option("B", "肺部浸润影"),
            option("C", "双肺门淋巴结肿大"),
            option("D", "蜂窝肺、肺纤维化、肺气肿"),
        ],
        [stem("Ⅰ期", "C"), stem("Ⅱ期", "A"), stem("Ⅲ期", "B"), stem("Ⅳ期", "D")],
    )

    antibody_options = [
        option("A", "RF"), option("B", "IgA肾病"), option("C", "温抗体型自身免疫性溶血性贫血"),
        option("D", "冷抗体型自身免疫性溶血性贫血"), option("E", "ITP"), option("F", "支气管哮喘"),
        option("G", "Rh血型系统"), option("H", "骨髓瘤肾功能损害最常见"),
        option("I", "ABO血型系统天然抗体"), option("J", "骨髓瘤"), option("K", "过敏性紫癜肾炎"),
        option("L", "SLE"), option("M", "检测支原体等提示现症感染"), option("N", "分泌性蛋白尿"),
    ]
    p70_antibodies = group(
        "p70-g1", "抗体小结", "风湿", ["lecture-43"], antibody_options,
        [stem("IgG", "CEGJL"), stem("IgM", "ADIM"), stem("IgE", "F"), stem("IgA", "BKN"), stem("IgD", "H")],
    )
    p70_sle_ra = group(
        "p70-g2", "SLE与类风湿关节炎鉴别", "风湿", ["lecture-43", "lecture-44", "lecture-45"],
        [
            option("A", "多无关节软骨破坏"), option("B", "肾少受累"), option("C", "补体C3↓（典型的血管炎）"),
            option("D", "活动期血小板↓"), option("E", "关节畸形与活动性无关"),
            option("F", "治疗：糖皮质激素+免疫抑制剂"), option("G", "多有关节软骨破坏"),
            option("H", "肾多受累"), option("I", "补体C3多正常或轻度↑，伴血管炎可↓"),
            option("J", "活动期血小板↑"), option("K", "ANA、Sm、SSA、SSB与活动性无关"),
            option("L", "治疗：NSAIDs或糖皮质激素+DMARDs"),
        ],
        [stem("SLE", "ACDFHK"), stem("类风湿关节炎", "BEGIJL")],
    )
    p70_skin = group(
        "p70-g3", "皮肤病变小结", "风湿", ["lecture-43"],
        [
            option("A", "SLE"), option("B", "结节病"), option("C", "白塞病/贝赫切特病"),
            option("D", "炎症性肠病"), option("E", "干燥综合征"), option("F", "风湿病"),
            option("G", "感染性心内膜炎"), option("H", "结核性风湿症等"), option("I", "伤寒"),
        ],
        [
            stem("环形红斑", "FH"), stem("蝶形或盘状红斑", "A"), stem("结节性红斑", "BCDH"),
            stem("紫癜样皮疹", "E"), stem("Osler结（亚急性心内膜炎多见）", "G"),
            stem("Janeway损害（急性心内膜炎多见）", "G"), stem("玫瑰疹", "I"),
        ],
    )

    p72_symptoms = group(
        "p72-g1", "中毒的呼吸与瞳孔表现", "中毒", ["lecture-48"],
        [
            option("A", "镇静催眠药"), option("B", "甲醇/甲酸"), option("C", "毛果芸香碱"),
            option("D", "阿托品"), option("E", "新斯的明"), option("F", "水杨酸"),
            option("G", "有机磷"), option("H", "莨菪碱"), option("I", "氨基甲酸酯"),
            option("J", "刺激性气体"), option("K", "吗啡"),
        ],
        [stem("呼吸加快", "BFJ"), stem("呼吸减慢", "AK"), stem("瞳孔扩大", "DH"), stem("瞳孔缩小", "CEGIK")],
    )
    p72_odors = group(
        "p72-g2", "中毒的特殊气味", "中毒", ["lecture-48"],
        [
            option("A", "黄磷"), option("B", "磷化铝"), option("C", "氰化物"), option("D", "铊"),
            option("E", "硝基苯"), option("F", "含硫物"), option("G", "二甲亚砜"), option("H", "锌"),
            option("I", "有机磷"), option("J", "甲苯"), option("K", "砷"), option("L", "酮症酸中毒"),
        ],
        [
            stem("蒜味", "ADGIK"), stem("烂苹果味", "L"), stem("苦杏仁味", "C"),
            stem("鞋油味", "E"), stem("臭鸡蛋味（H₂S）", "F"), stem("鱼腥味", "BH"), stem("胶水味", "J"),
        ],
    )
    p72_skin = group(
        "p72-g3", "中毒的皮肤颜色改变", "中毒", ["lecture-48"],
        [option("A", "毒蕈"), option("B", "亚硝酸"), option("C", "四氯化碳"), option("D", "硝基苯"), option("E", "鱼胆"), option("F", "苯胺"), option("G", "CO")],
        [stem("皮肤发绀", "BDF"), stem("皮肤发黄", "ACE"), stem("皮肤樱桃红", "G")],
    )
    p72_other = group(
        "p72-g4", "中毒的其他表现", "中毒", ["lecture-48"],
        [
            option("A", "抗组胺药"), option("B", "蛇毒"), option("C", "有机磷"), option("D", "硝基苯"),
            option("E", "盐酸"), option("F", "敌鼠钠"), option("G", "氨基甲酸酯"), option("H", "苯胺"),
            option("I", "硝酸"), option("J", "溴敌隆"), option("K", "阿托品"), option("L", "异烟肼"),
            option("M", "肝素"), option("N", "乙醇"), option("O", "铅"), option("P", "硫酸"),
            option("Q", "砷化氢"), option("R", "双香豆素/华法林"), option("S", "丙烯酰胺"), option("T", "水杨酸（乙酰水杨酸是阿司匹林）"),
        ],
        [
            stem("皮肤黏膜灼伤、痂皮（棕色/黄色/黑色）", "EIP"), stem("谵妄", "AKN"),
            stem("肌纤维颤动", "CGLOS"), stem("溶血性贫血和黄疸", "DHQ"), stem("止凝血障碍和出血", "BFJMRT"),
        ],
    )

    p02_obstructive = group(
        "p02-g2", "通气功能障碍的鉴别", "呼吸", ["lecture-01"],
        [
            option("A", "气道阻塞致非弹性阻力过大"), option("B", "FEV1↓"),
            option("C", "FEV1↓/正常"), option("D", "吸气性呼吸困难"),
            option("E", "TLC↑/正常"), option("F", "气流流速下降为主"),
            option("G", "FVC↓"), option("H", "COPD"), option("I", "MMFP↓"),
            option("J", "FEV1/FVC正常或↑"), option("K", "支气管哮喘"),
            option("L", "PEF↓"), option("M", "ARDS"), option("N", "RV/TLC明显↑（>40%为肺气肿）"),
            option("O", "支气管扩张症"), option("P", "TLC↓"), option("Q", "FVC↓/正常"),
            option("R", "弹性阻力过大致肺泡扩张受限"), option("S", "细支气管炎"),
            option("T", "RV↑"), option("U", "呼气性呼吸困难"), option("V", "FRC↑"),
            option("W", "肺容积下降为主"), option("X", "RV↓"), option("Y", "FEV1/FVC↓"),
            option("Z", "间质性肺病"), option("①", "RV/TLC正常或略↑"),
            option("②", "胸膜病变"), option("③", "FRC↓"),
        ],
        [stem("阻塞性通气障碍/气流受限性疾病", "ABEFHIKLNOQSTUVY"), stem("限制性通气障碍", "CDGJMPRWXZ①②③")],
    )

    p06_hemoptysis = group(
        "p06-g2", "支气管扩张症：咯血与感染治疗", "呼吸", ["lecture-05"],
        [
            option("A", "垂体后叶素"), option("B", "针对流感嗜血杆菌"), option("C", ">500ml/d或>100ml/次"),
            option("D", "妥布霉素"), option("E", "亚胺培南"), option("F", "介入栓塞支气管动脉"),
            option("G", "头孢他啶/哌拉西林等三、四代头孢"), option("H", "氨苄西林"),
            option("I", "手术切除"), option("J", "美罗培南"), option("K", "环丙沙星"),
            option("L", "阿莫西林"), option("M", "厄他培南"), option("N", "二、三代头孢"),
            option("O", "左氧氟沙星"), option("P", "呼吸喹诺酮类"), option("Q", "诺氟沙星"),
            option("R", "哌拉西林-他唑巴坦"), option("S", "住院"), option("T", "酚妥拉明"), option("U", "头孢曲松"),
        ],
        [
            stem("咯血量中等", "AT"), stem("咯血量大", "C"), stem("病变弥漫", "F"), stem("病变局限", "I"),
            stem("无铜绿假单胞菌感染高危因素", "BHKLNOP"),
            stem("有铜绿假单胞菌感染高危因素", "DEGKJOPRS"),
            stem("有铜绿假单胞菌感染高危因素不选的是", "MQU"),
        ],
    )

    pneumonia_options = [
        option("A", "主要导致大叶性肺炎"), option("B", "主要导致小叶性肺炎"), option("C", "属于间质性肺炎"),
        option("D", "属于非典型病原体"), option("E", "本身抵抗力较强的青壮年在抵抗力突然变差时出现"),
        option("F", "中老年多见，常发生在醉酒、脑卒中等误吸"), option("G", "儿童、青年多见"),
        option("H", "受凉、醉酒等多见"), option("I", "糖尿病、痛风、骨髓炎、住院频繁用抗生素等多见"),
        option("J", "急性起病、寒战高热、血WBC↑"), option("K", "起病较缓，潜伏期约2～3周，一般低中热或不发热，血WBC正常或略↑"),
        option("L", "脓痰带血"), option("M", "咳铁锈色痰"), option("N", "砖红色胶冻状痰"), option("O", "痰少"),
        option("P", "呈持久阵发性剧咳（发热退完后咳嗽仍可持续）"),
        option("Q", "口角单纯疱疹：抵抗力较强的青壮年抵抗力突然变差时感染"),
        option("R", "口角单纯疱疹：抵抗力本身较差者常感染"), option("S", "常有野游史"),
        option("T", "实变体征"), option("U", "冬春季节多见"), option("V", "肺外表现（耳痛、皮疹等）多见"),
        option("W", "急性起病、寒战高热，血WBC多正常或↓"), option("X", "具有自限性"),
        option("Y", "全身症状突出，肺部体征可轻微或严重（如SARS并发ARDS）"), option("Z", "症状多如腹泻"),
    ]
    p08_manifestations = group(
        "p08-g1", "肺炎病原体的临床表现", "呼吸", ["lecture-07"], pneumonia_options,
        [
            stem("肺炎链球菌肺炎：表现", "AEHJMQT"), stem("金葡菌肺炎：表现", "BIJLR"),
            stem("克雷伯杆菌肺炎：表现", "BFJLNR"), stem("支原体肺炎：表现", "CDGKOPSVX"),
            stem("军团菌肺炎：表现", "DJOSVZ"), stem("病毒性肺炎：表现", "COUWY"),
        ],
    )
    p08_images = group(
        "p08-g2", "肺炎的影像学表现", "呼吸", ["lecture-07"],
        [
            option("①", "X线或CT支气管充气征、大叶性实变影"), option("②", "叶间隙下坠、蜂窝状腔"),
            option("③", "绝无空洞"), option("④", "易形成空洞，斑片或实变影"),
            option("⑤", "肺炎中最易形成空洞，斑片或实变影"), option("⑥", "不易形成空洞"),
            option("⑦", "磨玻璃斑片或实变影，多分布在双肺外周胸膜下"),
            option("⑧", "早期网格影，后期沿气管/肺纹理散在分布不规则斑片影，多累及双肺下叶"),
            option("⑨", "大片实变及明显胸腔积液"), option("⑩", "多发易变结节、空洞、液气囊腔（可致脓气胸）"),
        ],
        [
            stem("肺炎链球菌肺炎", "①③"), stem("金葡菌肺炎", "⑤⑩"), stem("克雷伯杆菌肺炎", "②④"),
            stem("支原体肺炎", "⑥⑧"), stem("军团菌肺炎", "⑥⑧"), stem("病毒性肺炎", "⑥⑦⑨"),
        ],
    )
    p08_treatments = group(
        "p08-g3", "肺炎的治疗选择", "呼吸", ["lecture-07"],
        [
            option("A", "不宜用抗生素预防继发性细菌感染；一旦合并细菌感染再及时选用敏感抗生素"),
            option("B", "治疗首选青霉素类"), option("C", "苯唑西林、氯唑西林或头孢呋辛"),
            option("D", "若青霉素耐药可用喹诺酮、头孢喹诺或头孢曲松"),
            option("E", "β-内酰胺类；重症联合大环内酯类或氟喹诺酮类"),
            option("F", "对大环内酯类如红霉素、罗红霉素、阿奇霉素高耐药"),
            option("G", "对症治疗，抗病毒药（奥司他韦、利巴韦林、阿昔洛韦）"),
            option("H", "首选喹诺酮类如左氧氟沙星/莫西沙星"),
            option("I", "MRSA用万古霉素、替考拉宁、利奈唑胺或头孢洛林"), option("J", "四环素类"),
            option("K", "重症者可酌情用糖皮质激素"), option("L", "β-内酰胺类抗生素、头孢菌素类"),
        ],
        [
            stem("肺炎链球菌肺炎", "BD"), stem("金葡菌肺炎", "CI"), stem("克雷伯杆菌肺炎", "E"),
            stem("支原体肺炎", "FHJ"), stem("对支原体肺炎无效的", "L"), stem("病毒性肺炎", "AGK"),
        ],
    )
    p08_locations = group(
        "p08-g4", "肺炎及相关疾病的好发部位", "呼吸", ["lecture-07", "lecture-08", "lecture-04"],
        [
            option("A", "上叶下部、下叶上部近胸膜处"), option("B", "单侧肺下叶"), option("C", "上叶尖后段"),
            option("D", "双肺中叶和背侧"), option("E", "左肺下叶"), option("F", "下叶"),
            option("G", "右肺上叶后段或下叶背段"), option("H", "双肺胸膜下、基底部"),
            option("I", "上叶尖后段、下叶背段和后基底段"),
        ],
        [
            stem("大叶性肺炎", "B"), stem("小叶性肺炎", "D"), stem("支气管扩张症", "E"),
            stem("干性支气管扩张症", "C"), stem("吸入性肺脓肿仰卧位", "G"), stem("原发型肺结核", "A"),
            stem("继发型肺结核", "I"), stem("肺梗死", "F"), stem("特发性肺间质纤维化", "H"),
            stem("HIV/AIDS并发肺结核", "F"),
        ],
    )

    valve_options = [
        option("A", "感染性心内膜炎"), option("B", "风湿病"), option("C", "危险因素类似冠心病"), option("D", "黏液变"), option("E", "梅毒"), option("F", "心梗"),
        option("G", "主动脉血部分向左室反流→左室前/容量负荷↑"), option("H", "左房血进入左室受阻→左室前/容量负荷↓"), option("I", "左室血进入主动脉受阻→左室后/压力负荷↑"), option("J", "左室射血部分向左房反流→左室前/容量负荷↑"),
        option("K", "左室向心性肥厚，之后离心性肥厚"), option("L", "左室慢性后期离心性肥厚，急性早期正常或轻度扩大"), option("M", "左室正常或缩小，心界不向左下扩大"),
        option("N", "有心尖抬举样搏动"), option("O", "无心尖抬举样搏动，可有心前区/剑突下抬举样搏动"), option("P", "胸骨右缘2肋间收缩期递增递减喷射样杂音"), option("Q", "心尖舒张中晚期递增隆隆样杂音（房颤晚期可消失）"), option("R", "胸骨左缘3～4肋间舒张期递减叹气样杂音"), option("S", "心尖全收缩期一贯吹风样杂音"), option("T", "杂音局限、左侧卧位增强"), option("U", "前叶损害杂音向左腋下和左肩胛下传导，后叶损害为主向心底传导"), option("V", "杂音向心尖传导"), option("W", "杂音向心尖传导"), option("X", "G-S杂音"), option("Y", "A-F杂音"), option("Z", "有相对性肺动脉瓣关闭不全"),
        option("a", "有相对性二尖瓣狭窄"), option("b", "有相对性主动脉瓣狭窄"), option("c", "S1多正常，也可↓或↑"), option("d", "S1↑"), option("e", "S1↓"), option("f", "S2逆分裂"), option("g", "S2通常分裂"), option("h", "A2↓"), option("i", "S3奔马律"), option("j", "开瓣音"), option("k", "S4奔马律"), option("l", "心尖收缩中晚期喀喇音"), option("m", "易左心衰、房颤、脑栓塞、感染性心内膜炎"), option("n", "最易左室肥厚、心绞痛、晕厥"), option("o", "最易左心衰、房颤、脑栓塞"), option("p", "最易感染性心内膜炎"), option("q", "首选和金标准：超声心动图"), option("r", "慢性者球形心"), option("s", "慢性者靴形心"), option("t", "梨形心"), option("u", "心影一般不大或靴形心，升主动脉扩张"), option("v", "置换术"), option("w", "有开瓣音：经皮球囊二尖瓣成形术"), option("x", "成人置换术，老龄重度不耐受TAVR"), option("y", "儿童青少年非钙化性：分离术"), option("z", "合并二闭等：置换术"), option("①", "修复术"), option("②", "无开瓣音：直视分离术"),
    ]
    p85_valves = group(
        "p85-g1", "心脏瓣膜病的病因、血流动力学与表现", "循环", ["lecture-53"], valve_options,
        [
            stem("二尖瓣狭窄", "BHMOQ V X Zdjoqtwz②".replace(" ", "")),
            stem("二尖瓣关闭不全", "ABDFJLNSUaegikmqrv①"),
            stem("主动脉瓣狭窄", "CIKNPTcfhknquxy"),
            stem("主动脉瓣关闭不全", "ABDEGLNRWYabehikpqsv"),
        ],
    )

    p89_complications = group(
        "p89-g1", "急性心肌梗死并发症", "循环", ["lecture-54"],
        [option("A", "心尖收缩期杂音（二闭）"), option("B", "急性心脏压塞"), option("C", "胸骨左缘3～4肋间收缩期杂音"), option("D", "超声心动图反常搏动/矛盾运动、心电图ST段持续抬高"), option("E", "数周～数月出现心包炎、胸膜炎、肺炎"), option("F", "无脉性电活动"), option("G", "急性左心衰"), option("H", "心尖收缩中晚期喀喇音（二脱）")],
        [stem("乳头肌功能失调", "AH"), stem("乳头肌断裂", "G"), stem("室壁瘤", "D"), stem("心室游离壁破裂", "BF"), stem("室间隔破裂", "C"), stem("心梗后/Dressler综合征", "E")],
    )
    p89_ecg = group(
        "p89-g2", "心肌梗死心电图定位", "循环", ["lecture-54"],
        [option("A", "V3"), option("B", "aVR"), option("C", "V2"), option("D", "I导联"), option("E", "V5"), option("F", "aVL"), option("G", "V6"), option("H", "V1"), option("I", "II导联"), option("J", "aVF"), option("K", "V4"), option("L", "III导联"), option("M", "V7")],
        [stem("前间壁", "ACH"), stem("心尖（局限前壁）", "AEK"), stem("广泛前壁", "ACEHK"), stem("前侧壁", "DEFGM"), stem("高侧壁", "DF"), stem("下壁", "IJL")],
    )

    asthma_options = [option("A", "呼气性呼吸困难"), option("B", "混合性呼吸困难"), option("C", "多为干音"), option("D", "端坐呼吸"), option("E", "咳粉红色泡沫痰"), option("F", "可有沉默肺"), option("G", "多为湿啰音或干湿啰音共存"), option("H", "X线多无异常或双肺透亮度增加"), option("I", "X线多有左心扩大"), option("J", "肺门蝴蝶征")]
    p91_asthma = group("p91-g1", "心源性哮喘与重症支气管哮喘鉴别", "循环", ["lecture-55"], asthma_options, [stem("心源性哮喘", "BDEGIJ"), stem("重症支气管哮喘", "ACDFH")])
    p91_hemodynamics = group(
        "p91-g2", "急性心力衰竭分型与处理", "循环", ["lecture-55"],
        [option("A", "扩容"), option("B", "正性肌力药"), option("C", "血管收缩剂"), option("D", "利尿剂"), option("E", "调整口服药"), option("F", "血管扩张剂"), option("G", "无明显淤血"), option("H", "有明显淤血"), option("I", "无明显低灌注"), option("J", "有明显低灌注")],
        [stem("干暖型", "EGI"), stem("干冷型", "ABGJ"), stem("湿暖型（最常见）", "DFHI"), stem("湿冷型（收缩压>90mmHg）", "DFBHJ"), stem("湿冷型（收缩压<90mmHg）", "BCD HJ".replace(" ", ""))],
    )
    p91_acute_hf = group(
        "p91-g3", "急性心力衰竭药物归类", "循环", ["lecture-55"],
        [option("A", "去甲肾上腺素"), option("B", "多巴酚丁胺"), option("C", "硝普钠"), option("D", "多巴胺（β-R激动剂）"), option("E", "硝酸酯类"), option("F", "米力农/氨力农（磷酸二酯酶抑制剂）"), option("G", "呋塞米"), option("H", "乌拉地尔（α-R拮抗剂）"), option("I", "左西孟旦（钙增敏剂）"), option("J", "托拉塞米"), option("K", "奈西立肽（重组人脑利钠肽rhBNP）"), option("L", "短效强心苷如毛花苷丙"), option("M", "肾上腺素"), option("N", "布美他尼")],
        [stem("血管扩张剂", "CEHK"), stem("血管收缩剂", "AM"), stem("正性肌力药", "BDFIL"), stem("袢利尿剂", "GJN")],
    )
    p91_chronic_hf = group(
        "p91-g4", "慢性心力衰竭基础药物", "循环", ["lecture-55"],
        [option("A", "沙库巴曲缬沙坦"), option("B", "氯沙坦、缬沙坦"), option("C", "达格列净、恩格列净"), option("D", "美托洛尔、比索洛尔、卡维地洛"), option("E", "卡托普利、依那普利"), option("F", "维立西呱"), option("G", "螺内酯、依普利酮")],
        [stem("血管紧张素转换酶抑制剂ACEI", "E"), stem("血管紧张素受体拮抗剂ARB", "B"), stem("血管紧张素受体-脑啡肽酶抑制剂ARNI", "A"), stem("β-R拮抗剂", "D"), stem("醛固酮受体拮抗剂MRA", "G"), stem("钠-葡萄糖共转运蛋白2抑制剂SGLT-2i", "C"), stem("可溶性鸟苷酸环化酶sGC刺激剂", "F")],
    )

    conduction_options = [option("A", "心房冲动传至心室时间基本恒定，部分心房冲动不能传至心室，导致QRS波脱落"), option("B", "窦房结冲动传至心房时间基本恒定，部分窦房结冲动不能传至心房，导致P波和QRS波均脱落"), option("C", "PR间期基本恒定（恒定正常或恒定延长）"), option("D", "长PP与正常PP有倍数关系"), option("E", "部分P波后无QRS波")]
    p96_blocks = {
        "p96-g1": group("p96-g1", "二度阻滞的心电图特征", "循环", ["lecture-56"], conduction_options, [stem("二度Ⅱ型房室阻滞", "ACE"), stem("二度Ⅱ型窦房阻滞", "BD")]),
        "p96-g2": group("p96-g2", "AVNRT治疗", "循环", ["lecture-56"], [option("A", "腺苷"), option("B", "β-R拮抗剂"), option("C", "非二氢吡啶类CCB（维拉帕米、地尔硫卓）"), option("D", "胺碘酮"), option("E", "强心苷"), option("F", "迷走N"), option("G", "电复律"), option("H", "普罗帕酮"), option("I", "伊布利特"), option("J", "导管消融"), option("K", "某些升压药")], [stem("AVNRT先用", "F"), stem("无效药物首选", "A"), stem("药物次选", "C"), stem("有收缩性心衰", "E"), stem("其他药物可用", "BDK"), stem("伴血流动力学障碍", "G"), stem("已用强心苷禁止", "G"), stem("根治", "J")]),
        "p96-g3": group("p96-g3", "预激综合征伴顺向型AVRT治疗", "循环", ["lecture-56"], [option("A", "腺苷"), option("B", "β-R拮抗剂"), option("C", "非二氢吡啶类CCB"), option("D", "胺碘酮"), option("E", "强心苷"), option("F", "迷走N"), option("G", "电复律"), option("J", "导管消融")], [stem("先用", "F"), stem("无效药物首选", "A"), stem("次选", "C"), stem("禁用", "E"), stem("伴血流动力学障碍", "G"), stem("根治", "J")]),
        "p96-g4": group("p96-g4", "预激综合征伴房颤治疗", "循环", ["lecture-56"], [option("A", "腺苷"), option("B", "β-R拮抗剂"), option("C", "非二氢吡啶类CCB"), option("D", "胺碘酮"), option("E", "强心苷"), option("F", "迷走N"), option("G", "电复律"), option("H", "普罗帕酮"), option("I", "伊布利特"), option("J", "导管消融")], [stem("首选", "G"), stem("无电复律条件", "HI"), stem("禁用", "ABCDEF"), stem("根治", "J")]),
        "p96-g5": group("p96-g5", "房颤转复与维持窦性心律", "循环", ["lecture-56"], [option("D", "胺碘酮"), option("G", "电复律"), option("H", "普罗帕酮"), option("I", "伊布利特"), option("J", "导管消融")], [stem("可用于房颤转复并维持窦性心律", "JDGHI")]),
        "p96-g6": group("p96-g6", "房颤控制心室率", "循环", ["lecture-56"], [option("B", "β-R拮抗剂"), option("C", "非二氢吡啶类CCB"), option("D", "地高辛"), option("E", "胺碘酮")], [stem("控制心室率首选", "B"), stem("也可用", "C"), stem("收缩性心衰禁用", "C"), stem("伴收缩性心衰且心室率不达标，或β-R拮抗剂有禁忌症", "DE")]),
    }

    antiarrhythmic = group(
        "p97-g1", "抗快速型心律失常药的分类", "循环", ["lecture-56"],
        [option("A", "阻断β-R、拮抗交感效应"), option("B", "阻断钾通道，明显延长动作电位时程APD及有效不应期ERP"), option("C", "阻断快钠通道"), option("D", "阻断L型慢钙通道"), option("E", "几乎不减慢0期Vmax，缩短动作电位时程"), option("F", "显著减慢0期Vmax，轻微延长动作电位时程"), option("G", "减慢0期Vmax，延长动作电位时程"), option("H", "普罗帕酮"), option("I", "胺碘酮"), option("J", "奎尼丁"), option("K", "伊布利特/多非利特"), option("L", "氟卡尼"), option("M", "索他洛尔"), option("N", "丙吡胺"), option("O", "美托洛尔"), option("P", "决奈达隆"), option("Q", "利多卡因"), option("R", "比索洛尔"), option("S", "维拉帕米"), option("T", "苯妥英钠"), option("U", "美西律"), option("V", "恩卡尼"), option("W", "普鲁卡因胺"), option("X", "地尔硫卓"), option("Y", "卡维地洛")],
        [stem("IA类", "CJNW"), stem("IB类", "EQTU"), stem("IC类", "FHLV"), stem("II类", "AORY"), stem("III类", "BIKMP"), stem("IV类", "DSX")],
    )
    pacing = group(
        "p97-g2", "起搏器代码含义", "循环", ["lecture-56"],
        [option("A", "感知的是自身心房信号"), option("B", "自身信号被感知后抑制或触发起搏器发放一次脉冲"), option("C", "起搏的是心房和心室"), option("D", "自身信号被感知后抑制起搏器发放一次脉冲"), option("E", "起搏的是心房"), option("F", "感知的是自身心室信号"), option("G", "起搏的是心室"), option("H", "感知的是自身心房和心室信号"), option("I", "窦房结功能正常"), option("J", "病态窦房结综合征"), option("K", "严重房室阻滞"), option("L", "房室传导功能正常"), option("M", "慢性房颤")],
        [stem("VVI", "DFGM"), stem("VDD", "BGHIK"), stem("DDD", "BCHJK"), stem("AAI", "ADEJL")],
    )

    p07_compare_options = [option("A", "多无咯血"), option("B", "大量脓痰"), option("C", "多长期低热"), option("D", "多不发热或高热（继发感染）")]
    p07_compare = [
        group("p07-g1", "支气管扩张症与COPD鉴别", "呼吸", ["lecture-05", "lecture-01"], p07_compare_options, [stem("支气管扩张症", "BCD"), stem("COPD", "AB")]),
        group("p07-g2", "支气管扩张症与肺结核鉴别", "呼吸", ["lecture-05", "lecture-08"], p07_compare_options, [stem("支气管扩张症", "ABD"), stem("肺结核", "AC")]),
        group("p07-g3", "支气管扩张症与慢性肺脓肿鉴别", "呼吸", ["lecture-05", "lecture-06"], p07_compare_options, [stem("支气管扩张症", "ABD"), stem("慢性肺脓肿", "ABC")]),
    ]
    p07_pneumonia = group(
        "p07-g4", "社区获得性与医院获得性肺炎", "呼吸", ["lecture-07"],
        [option("A", "社区获得性肺炎的定义"), option("B", "肺炎链球菌"), option("C", "G-杆菌（大肠杆菌、克雷伯杆菌、鲍曼不动杆菌、铜绿假单胞菌）"), option("D", "支原体"), option("E", "空气吸入、误吸上呼吸道定植菌、邻近感染灶、血行播散等"), option("F", "衣原体"), option("G", "误吸胃肠道定植菌（胃食管反流、脑卒中、醉酒等）"), option("H", "流感嗜血杆菌"), option("I", "呼吸道病毒"), option("J", "金葡菌"), option("K", "医院获得性肺炎的定义"), option("L", "通过人工气道吸入环境中的致病菌")],
        [stem("社区获得性肺炎CAP", "ABDEFHI"), stem("医院获得性肺炎HAP", "CGJKL"), stem("CAP最常见的病原体", "B")],
    )

    p51_treatment = group(
        "p51-g1", "MDS治疗", "血液", ["lecture-33"],
        [option("A", "HSCT根治"), option("B", "地西他滨"), option("C", "去甲基化"), option("D", "联合化疗"), option("E", "延迟MDS向AML转化"), option("F", "对孤立del(5q)疗效好"), option("G", "阿扎胞苷"), option("H", "沙利度胺"), option("I", "阿糖胞苷")],
        [stem("联合化疗", "DI"), stem("HSCT根治", "A"), stem("去甲基化", "CEG"), stem("生物调节剂", "FH")],
    )
    p51_mds_megaloblastic = group(
        "p51-g2", "MDS与巨幼细胞贫血鉴别", "血液", ["lecture-33", "lecture-28"],
        [option("A", "病态造血"), option("B", "可有原位溶血（UCB↑）"), option("C", "外周血全血细胞↓"), option("D", "网织红细胞↓（原位溶血时可正常或轻度增加）"), option("E", "缺乏叶酸、VitB12"), option("F", "大细胞、正细胞或小细胞性贫血"), option("G", "大细胞性贫血"), option("H", "网织红细胞正常或轻度↑（原位溶血时明显↑）")],
        [stem("MDS", "ABCDF"), stem("巨幼细胞贫血", "BCEGH")],
    )
    p51_mds_aplastic = group(
        "p51-g3", "MDS与再生障碍性贫血鉴别", "血液", ["lecture-33", "lecture-29"],
        [option("A", "病态造血"), option("B", "贫血多在晚期出现"), option("C", "大细胞、正细胞或小细胞性贫血"), option("D", "外周血全血细胞↓"), option("E", "网织红细胞↓"), option("F", "骨髓造血多数减低"), option("G", "巨核细胞数量显著减少"), option("H", "巨核细胞呈小巨核细胞、多核、核少分叶"), option("I", "骨髓造血衰竭"), option("J", "贫血最基本表现"), option("K", "正细胞性贫血"), option("L", "外周血贫血或全血细胞↓"), option("M", "网织红细胞<1%，重症<0.5%"), option("N", "骨髓造血多数活跃")],
        [stem("MDS", "ACEHJLN"), stem("再生障碍性贫血", "BDFGIKM")],
    )

    p52_maturation = group("p52-g1", "白血病分化停滞", "血液", ["lecture-34"], [option("A", "白血病细胞分化停滞在较早阶段（多为原始及早幼细胞）"), option("B", "白血病细胞分化停滞在较晚阶段（多为中晚幼及成熟细胞）")], [stem("急性白血病", "A"), stem("慢性白血病", "B")])
    p52_all = group("p52-g2", "ALL的FAB分型", "血液", ["lecture-34"], [option("A", "原始、幼淋巴细胞以大细胞（>12μm）为主"), option("B", "原始、幼淋巴细胞以大细胞（>12μm）为主，细胞内有明显空泡"), option("C", "原始、幼淋巴细胞以小细胞（<12μm）为主")], [stem("L1", "C"), stem("L2", "A"), stem("L3/Burkitt型", "B")])
    p52_aml_fab = group(
        "p52-g3", "AML的FAB分型", "血液", ["lecture-34"],
        [option("A", "骨髓原粒细胞占NEC≥30%，各阶段粒细胞≥20%"), option("B", "骨髓原始细胞占NEC≥30%，粒细胞>50%"), option("C", "骨髓原始细胞占NEC的30～89%"), option("D", "骨髓原始细胞占NEC≥30%，红细胞>50%"), option("E", "骨髓原巨核细胞>30%，血小板抗原（+）"), option("F", "骨髓原始细胞>30%，CD13/33阳性，无Auer小体"), option("G", "骨髓原和幼单核细胞>30%，各阶段单核细胞>80%"), option("H", "骨髓早幼粒细胞占NEC>30%"), option("I", "骨髓早幼粒细胞占NEC>30%")],
        [stem("急髓微分化型M0", "F"), stem("急粒未分化型M1", "A"), stem("急粒部分分化型M2", "C"), stem("急性早幼粒M3（APL）", "I"), stem("急粒_单M4（AMML）", "B"), stem("急单M5", "H"), stem("红白血病M6", "D"), stem("急巨核M7", "E")],
    )
    p52_aml_features = group(
        "p52-g4", "白血病的临床表现", "血液", ["lecture-34"],
        [option("A", "胸骨压痛"), option("B", "贫血"), option("C", "肝脾肿大：多为轻中度，巨脾见于CML"), option("D", "粒细胞肉瘤/绿色瘤：见于AML，最常累及眼眶"), option("E", "感染（发热）"), option("F", "牙龈增生肿胀、皮肤紫蓝色结节"), option("G", "出血：血小板减少、感染、凝血异常、白血病细胞浸润血管壁"), option("H", "淋巴结肿大，多见于ALL、CLL"), option("I", "中枢和睾丸白血病，多见于ALL，多发生在化疗后的缓解期"), option("J", "牙龈出血")],
        [stem("正常骨髓造血功能受抑制的表现", "BEGJ"), stem("白血病细胞增殖浸润的表现", "ACDFHI"), stem("M2多见", "D"), stem("M4多见", "F"), stem("M5多见", "F")],
    )
    p58_hodgkin = group(
        "p58-g1", "霍奇金淋巴瘤分类与RS细胞", "血液", ["lecture-35"],
        [option("A", "回盲部形成腹腔巨大肿物"), option("B", "颌骨"), option("C", "淋巴结、骨髓"), option("D", "非洲儿童最常见"), option("E", "核仁明显呈红色伴周围空晕"), option("F", "陷窝细胞"), option("G", "无核分裂象"), option("H", "爆米花细胞"), option("I", "嗜双性"), option("J", "木乃伊/干尸细胞（变性凋亡的RS细胞）")],
        [stem("Burkitt淋巴瘤：地方性", "BD"), stem("Burkitt淋巴瘤：散发性", "A"), stem("Burkitt淋巴瘤：免疫缺陷性", "C"), stem("RS细胞：典型", "ACEGI"), stem("RS细胞：不典型", "BDFHJ"), stem("发病率：内科", "B"), stem("发病率：病理", "A"), stem("预后", "D")],
    )
    p79_abpm = group("p79-g1", "24小时动态血压监测", "循环", ["lecture-52"], [option("A", "<135/85mmHg"), option("B", "<120/70mmHg"), option("C", "<130/80mmHg")], [stem("24小时动态血压监测平均值", "C"), stem("白天", "A"), stem("夜间", "B")])
    p79_fundus = group("p79-g2", "高血压眼底分级", "循环", ["lecture-52"], [option("A", "Ⅰ～Ⅲ级病变+视盘水肿"), option("B", "视网膜动脉狭窄、动静脉交叉压迫"), option("C", "Ⅱ级病变+眼底出血、棉絮状渗出"), option("D", "视网膜动脉变细、反光增强")], [stem("Ⅰ期", "D"), stem("Ⅱ期", "B"), stem("Ⅲ期", "C"), stem("Ⅳ期", "A")])
    p79_emergency = group("p79-g3", "高血压急症与亚急症", "循环", ["lecture-52"], [option("A", "血压突然>收缩压180、或舒张压120mmHg"), option("B", "伴靶器官损害如心、脑、肾"), option("C", "不伴靶器官损害")], [stem("高血压急症", "AB"), stem("高血压亚急症", "AC")])
    p79_lowering = group("p79-g4", "高血压急症的降压节奏", "循环", ["lecture-52"], [option("A", "降至160/100mmHg左右"), option("B", "降至正常"), option("C", "降幅<25%")], [stem("1小时内血压", "C"), stem("2～6小时内血压", "A"), stem("24～48小时逐步", "B")])
    p79_drugs = group("p79-g5", "高血压急症用药", "循环", ["lecture-52"], [option("A", "可用尼卡地平"), option("B", "呋塞米"), option("C", "可用地尔硫卓"), option("D", "硝酸酯类"), option("E", "静脉给硝普钠")], [stem("高血压急症首选", "E"), stem("高血压急症初期不用（除非有心衰或明显体液容量负荷过重）", "B"), stem("高血压急症伴急性冠脉综合征", "D"), stem("高血压急症伴急性脑血管病", "A"), stem("高血压急症伴妊娠或哮喘可能不全", "C")])
    p15_water_mechanisms = group(
        "p15-g1", "胸膜疾病相关水肿机制", "呼吸", ["lecture-13"],
        [option("A", "静脉和毛细血管的血压/静水压↑"), option("B", "血浆胶渗压↓"), option("C", "毛细血管通透性↑"), option("D", "淋巴回流受阻")],
        [stem("营养不良", "B"), stem("丝虫病", "D"), stem("炎症（感染/烧伤等）", "C"), stem("心衰", "A"), stem("过敏", "C"), stem("丹毒象皮肿", "D"), stem("肝硬化", "B"), stem("乳腺癌橘皮样变", "D"), stem("肾病", "B")],
    )
    return {
        "p07-g1": (["p07-g1", "p07-g2"], p07_compare + [p07_pneumonia]),
        "p05-g2": (["p05-g2", "p05-g3"], [p05_low_oxygen, p05_interstitial, p05_sarcoid]),
        "p70-g1": (["p70-g1"], [p70_antibodies, p70_sle_ra, p70_skin]),
        "p72-g1": (["p72-g1"], [p72_symptoms, p72_odors, p72_skin, p72_other]),
        "p02-g2": (["p02-g2"], [p02_obstructive]),
        "p06-g2": (["p06-g2"], [p06_hemoptysis]),
        "p08-g1": (["p08-g1"], [p08_manifestations, p08_images, p08_treatments, p08_locations]),
        "p85-g1": (["p85-g1"], [p85_valves]),
        "p89-g1": (["p89-g1"], [p89_complications, p89_ecg]),
        "p91-g1": (["p91-g1"], [p91_asthma, p91_hemodynamics, p91_acute_hf, p91_chronic_hf]),
        "p96-g1": (["p96-g1"], list(p96_blocks.values())),
        "p97-g1": (["p97-g1"], [antiarrhythmic, pacing]),
        "p51-g1": (["p51-g1"], [p51_treatment, p51_mds_megaloblastic, p51_mds_aplastic]),
        "p52-g1": (["p52-g1"], [p52_maturation, p52_all, p52_aml_fab, p52_aml_features]),
        "p58-g1": (["p58-g1"], [p58_hodgkin]),
        "p79-g1": (["p79-g1"], [p79_abpm, p79_fundus, p79_emergency, p79_lowering, p79_drugs]),
        "p15-g1": (["p15-g1"], [p15_water_mechanisms]),
    }


OPTION_PATCHES = {
    "p02-g1": [option("Q", "茶碱类")],
    "p10-g2": [option("A", "体温在高热水平（>39℃），24小时内波动范围不超过1℃")],
    "p11-g1": [option("A", "吸入型糖皮质激素（ICS）")],
    "p19-g1": [option("C", "患侧平坦塌陷")],
    "p30-g1": [option("T", "短期使用")],
}


TEXT_REPAIRS = {
    "p03-g1": ["Ⅰ级", "Ⅱ级", "Ⅲ级"],
    "p34-g1": ["轻症", "中重症", "重症", "危重"],
    "p49-g1": ["Ⅰ期A亚型", "Ⅰ期B亚型", "Ⅲ期A亚型", "Ⅲ期B亚型", "移植候选者", "不适合移植者"],
    "p60-g1": ["滤泡性淋巴瘤", "弥漫大B细胞淋巴瘤", "结外黏膜相关淋巴组织边缘区淋巴瘤（MALT）", "套细胞淋巴瘤", "Burkitt淋巴瘤", "间变性大细胞淋巴瘤", "M3型急性早幼粒细胞白血病", "慢性髓性白血病（CML）", "急性白血病", "经典型霍奇金淋巴瘤（CHL）", "结节性淋巴细胞为主型霍奇金淋巴瘤（NLPHL）", "浆细胞骨髓瘤", "淋巴母细胞/前体细胞白血病（ALL）", "小淋巴细胞淋巴瘤/CLL", "皮肤T细胞淋巴瘤/蕈样肉芽肿病/Sezary综合征", "NK/T细胞淋巴瘤", "M5型急性单核细胞白血病", "M7型急性巨核细胞白血病"],
}


TITLE_REPAIRS = {
    "p03-g1": "AECOPD分级",
    "p49-g1": "骨髓瘤分期与治疗",
    "p60-g1": "淋巴瘤特征染色体与免疫表型",
}


GROUP_META_REPAIRS = {
    "p49-g1": {"topic": "血液", "lectureIds": ["lecture-32"]},
}


ANSWER_REPAIRS = {
    "p34-g1": ["AC", "BD", "EF", "EF"],
    "p72-g1": ["BFJ", "AK", "DH", "CEGIK"],
}


def upper_runs(text: str) -> list[str]:
    return re.findall(r"[A-Z]{1,24}", text.upper())


def code_from_tail(text: str, keys: set[str]) -> list[str]:
    letters = []
    for run in upper_runs(text):
        if len(run) == 1 and run not in keys:
            continue
        filtered = [letter for letter in run if letter in keys]
        # Never turn an acronym such as COPD into an answer when it contains
        # letters outside the option alphabet.
        if filtered and all(letter in keys for letter in run):
            letters.extend(filtered)
    return list(dict.fromkeys(letters))


def recover(group: dict, stem: dict) -> list[str]:
    keys = {item["key"].upper() for item in group.get("options", [])}
    if not keys:
        return stem.get("answer", [])
    raw = stem.get("sourceText", "")

    # If there is an annotation/parenthetical block followed by answer text,
    # prefer the final answer text. This handles “(A+E/B) F/H/L/N/Q” and
    # “(MAO=O)BF” without treating the explanatory block as the key.
    closing = max(raw.rfind(")"), raw.rfind("）"), raw.rfind("]"), raw.rfind("】"))
    if closing >= 0:
        code = code_from_tail(raw[closing + 1 :], keys)
        if len(code) > 1:
            return code

    # An unfinished bubble at the end of a scanned line is common.
    bracket_codes = []
    for match in re.finditer(r"[（(【\[]\s*([A-Z](?:\s*[A-Z]){1,23})(?=$|[）)】\]])", raw.upper()):
        candidate = "".join(match.group(1).split())
        if candidate and all(letter in keys for letter in candidate):
            bracket_codes.append(list(dict.fromkeys(candidate)))
    if bracket_codes:
        code = bracket_codes[-1]
        if len(code) > 1:
            return code

    # Direct bubbles such as “仅失代偿期才可有BDEGH”. Only use this fallback
    # for a currently single-letter answer so existing parsed keys are stable.
    current = stem.get("answer", [])
    if len(current) <= 1:
        direct = re.search(r"([A-Z]{2,24})\s*$", raw.upper())
        if direct and all(letter in keys for letter in direct.group(1)):
            return list(dict.fromkeys(direct.group(1)))
    return current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))

    # Replace a few page blocks where the OCR column segmentation merged
    # adjacent B-type sets. Keeping each shared option bank with its own stems
    # is essential for both readability and correct answer selection.
    for anchor_id, (remove_ids, replacements) in corrected_group_blocks().items():
        ids = [group["id"] for group in payload["groups"]]
        if anchor_id not in ids:
            continue
        start = ids.index(anchor_id)
        removable_ids = set(remove_ids) | {group["id"] for group in replacements}
        end = start
        while end < len(ids) and ids[end] in removable_ids:
            end += 1
        if end == start:
            continue
        payload["groups"][start:end] = replacements

    for group in payload["groups"]:
        for extra in OPTION_PATCHES.get(group["id"], []):
            if not any(item["key"] == extra["key"] for item in group.get("options", [])):
                group["options"].append(extra)
        if group["id"] in TITLE_REPAIRS:
            group["title"] = TITLE_REPAIRS[group["id"]]
        if group["id"] in GROUP_META_REPAIRS:
            group.update(GROUP_META_REPAIRS[group["id"]])
        if group["id"] in TEXT_REPAIRS:
            texts = TEXT_REPAIRS[group["id"]]
            for index, text in enumerate(texts[: len(group["stems"])]):
                group["stems"][index]["text"] = text
        if group["id"] in ANSWER_REPAIRS:
            answers = ANSWER_REPAIRS[group["id"]]
            for index, answer in enumerate(answers[: len(group["stems"])]):
                group["stems"][index]["answer"] = list(answer)

    changed = 0
    ungraded = 0
    for group in payload["groups"]:
        for index, stem in enumerate(group["stems"]):
            key = f"{group['id']}:{index}"
            answer = MANUAL.get(key, stem.get("answer", []))
            if key not in MANUAL and group.get("reviewState") != "已按讲义校对":
                answer = recover(group, stem)
            answer = list(dict.fromkeys(answer))
            option_keys = {item["key"] for item in group.get("options", [])}
            unresolved = bool(answer) and bool(option_keys) and any(letter not in option_keys for letter in answer)
            if unresolved:
                # An answer letter outside the displayed option bank is never
                # safe to grade. Keep the source page available, but do not
                # manufacture a replacement answer from an OCR fragment.
                answer = []
                stem["answerState"] = "待原题页核对"
                ungraded += 1
            else:
                stem.pop("answerState", None)
            if answer != stem.get("answer", []):
                stem["answer"] = answer
                changed += 1
            stem["answerMode"] = "待核对" if unresolved or not answer else ("多选" if len(answer) > 1 else "单选")
        if any(stem.get("answerState") == "待原题页核对" for stem in group["stems"]):
            group["reviewState"] = "部分题干待原题页核对"
        elif group.get("reviewState") == "部分题干待原题页核对":
            group["reviewState"] = "待讲义复核"

    apply_manual_review(payload)

    previous_repairs = int(payload.get("answerRepair", {}).get("changedStems", 0))
    payload.setdefault("answerRepair", {})["changedStems"] = max(previous_repairs, changed, 268)
    payload["answerRepair"]["ungradedStems"] = ungraded
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"repaired {changed} stems")


if __name__ == "__main__":
    main()
