#!/usr/bin/env python3
"""Build the pathology question payload used by the integrated study site."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import build_med_content as shared


# Pathology pages were rendered at 150 dpi (767 px wide), while the internal
# medicine source was OCR'd at roughly 300 dpi.
shared.RIGHT_X = 350

TOPIC_RULES = [
    ("消化系统", ["胃炎", "消化性溃疡", "胃癌", "大肠癌", "肝硬化", "肝癌", "肠结核", "肠伤寒", "痢疾", "阿米巴", "溃疡好发"]),
    ("心血管系统", ["感染性心内膜炎", "风湿病", "动脉粥样硬化", "心肌疾病", "心肌病"]),
    ("呼吸系统", ["肺气肿", "慢支炎", "肺炎", "肺癌", "肺硅", "支扩"]),
    ("内分泌系统", ["甲状腺", "内分泌"]),
    ("免疫性疾病", ["免疫缺陷", "排斥反应", "变态反应", "Bruton", "DiGeorge"]),
    ("生殖系统", ["宫颈", "滋养层", "葡萄胎", "卵巢", "畸胎瘤", "内胚窦瘤", "粒层细胞"]),
    ("乳腺疾病", ["乳腺"]),
    ("传染病", ["结核", "流行性乙型脑炎", "流行性脑脊髓膜炎", "传染病", "血吸虫", "伤寒"]),
    ("损伤与修复", ["损伤的修复", "骨折愈合", "肉芽组织", "创伤愈合", "适应和损伤", "萎缩", "肥大", "增生", "化生", "钙化", "变性", "坏死", "凋亡", "坏疽"]),
    ("局部血液循环障碍", ["淤血", "血栓", "栓塞", "梗死", "水肿"]),
    ("炎症", ["炎症", "巨细胞", "炎症介质", "肉芽肿"]),
    ("肿瘤", ["肿瘤", "癌基因", "抑癌基因", "原癌基因", "癌胚抗原", "肿瘤标志"]),
]

PAGE_FALLBACK = {
    3: "消化系统", 4: "消化系统", 5: "消化系统", 6: "消化系统",
    7: "心血管系统", 8: "心血管系统", 9: "呼吸系统", 10: "呼吸系统",
    11: "内分泌系统", 12: "内分泌系统", 13: "免疫性疾病",
    14: "生殖系统", 15: "生殖系统", 16: "生殖系统", 17: "生殖系统",
    18: "乳腺疾病", 19: "传染病", 20: "传染病", 21: "传染病",
    22: "传染病", 23: "传染病", 24: "损伤与修复", 25: "损伤与修复",
    26: "损伤与修复", 27: "损伤与修复", 28: "损伤与修复",
    29: "损伤与修复", 30: "局部血液循环障碍", 31: "炎症", 32: "炎症",
    33: "肿瘤", 34: "肿瘤", 35: "肿瘤", 36: "肿瘤", 37: "肿瘤",
}

LECTURE_KEYWORDS = {
    "消化系统": ["胃", "消化", "肝", "肠", "胰腺"],
    "心血管系统": ["心", "高血压", "动脉粥样硬化", "风湿病"],
    "呼吸系统": ["肺", "支扩", "呼吸"],
    "内分泌系统": ["内分泌", "甲状腺"],
    "免疫性疾病": ["免疫"],
    "生殖系统": ["生殖"],
    "乳腺疾病": ["乳腺"],
    "传染病": ["结核", "传染病", "肝炎"],
    "损伤与修复": ["适应和损伤", "损伤的修复"],
    "局部血液循环障碍": ["局部血液循环障碍"],
    "炎症": ["炎症"],
    "肿瘤": ["肿瘤"],
}

GROUP_TOPIC_OVERRIDES = {
    "p04-g1": "消化系统", "p06-g2": "心血管系统", "p07-g1": "心血管系统",
    "p08-g1": "心血管系统", "p08-g2": "心血管系统", "p08-g3": "心血管系统",
    "p09-g2": "呼吸系统", "p10-g3": "呼吸系统",
    "p12-g1": "内分泌系统", "p12-g2": "内分泌系统",
    "p14-g2": "生殖系统", "p17-g1": "生殖系统", "p17-g3": "生殖系统",
    "p18-g1": "乳腺疾病", "p21-g1": "传染病", "p22-g1": "传染病",
    "p22-g2": "传染病", "p23-g1": "传染病",
    "p30-g1": "局部血液循环障碍", "p31-g1": "炎症", "p32-g2": "炎症",
    "p35-g1": "肿瘤", "p35-g2": "肿瘤",
}

GROUP_LECTURE_OVERRIDES = {
    "p03-g1": ["lecture-01"], "p03-g2": ["lecture-01"], "p04-g1": ["lecture-03"],
    "p05-g1": ["lecture-05"], "p06-g1": ["lecture-01", "lecture-05"],
    "p06-g2": ["lecture-06"], "p07-g1": ["lecture-07"], "p08-g1": ["lecture-07"],
    "p08-g2": ["lecture-09"], "p08-g3": ["lecture-10"],
    "p09-g1": ["lecture-11"], "p09-g2": ["lecture-11"], "p09-g3": ["lecture-11"],
    "p10-g1": ["lecture-11"], "p10-g2": ["lecture-14"], "p10-g3": ["lecture-14"],
    "p11-g1": ["lecture-16"], "p12-g1": ["lecture-16"], "p12-g2": ["lecture-16"],
}

TITLE_OVERRIDES = {
    "p04-g1": "肝硬化的临床表现与腹水机制",
    "p05-g1": "大肠癌癌前病变与相关基因",
    "p06-g2": "急性与亚急性感染性心内膜炎",
    "p07-g1": "风湿病的基本病变与Aschoff小体",
    "p08-g2": "动脉粥样硬化斑块的形成",
    "p09-g2": "慢性支气管炎与肺气肿的机制",
    "p10-g3": "病毒包涵体的位置",
    "p13-g1": "原发性免疫缺陷病",
    "p14-g2": "宫颈鳞状上皮内病变分级",
    "p18-g1": "乳腺癌的分类与病理特征",
    "p19-g1": "结核杆菌成分与原发、继发性肺结核",
    "p21-g1": "常见传染病的病理类型",
    "p31-g1": "炎症的基本类型",
    "p32-g1": "炎症介质",
    "p32-g2": "常考肉芽肿",
    "p34-g1": "肿瘤标志物与免疫组化",
    "p35-g1": "化学、物理与生物致癌因素",
}


def topic_for(text: str, page: int) -> str:
    normalized = text.lower()
    scores = []
    for topic, keys in TOPIC_RULES:
        score = sum(normalized.count(key.lower()) for key in keys)
        scores.append((score, topic))
    score, topic = max(scores)
    return topic if score else PAGE_FALLBACK.get(page, "综合")


def related_lectures(topic: str, lectures: list[dict]) -> list[str]:
    keys = LECTURE_KEYWORDS.get(topic, [])
    matches = [
        lecture["id"] for lecture in lectures
        if any(key.lower() in lecture["title"].lower() for key in keys)
    ]
    return matches[:6]


CONTINUATION_STEMS = {
    15: [
        ("良性葡萄胎（完全性、部分性）", "ABDHLQRS"),
        ("恶性葡萄胎（侵袭性葡萄胎）", "BCGHMOVW"),
        ("绒毛膜癌/绒癌", "EFIJKNPTUW"),
    ],
    20: [
        ("局灶型肺结核", "AC"),
        ("浸润型肺结核", "EHJM"),
        ("干酪样肺炎", "BK"),
        ("慢性纤维空洞型肺结核", "DILNP"),
        ("结核球/结核瘤", "F"),
        ("结核性胸膜炎", "GO"),
    ],
}


def repair_continuation_group(group: dict) -> dict:
    stems = CONTINUATION_STEMS.get(group["page"])
    if group.get("stems") or not stems:
        return group
    group["title"] = stems[0][0] if group["page"] == 15 else "继发性肺结核的类型"
    group["kind"] = "B"
    group["kindLabel"] = "B型题"
    group["stems"] = [
        {
            "text": text,
            "answer": list(answer),
            "answerMode": "多选" if len(answer) > 1 else "单选",
            "sourceText": f"{text}（{answer}）",
            "sourceY": None,
        }
        for text, answer in stems
    ]
    group["reviewState"] = "已按原题页人工恢复，待讲义复核"
    return group


def option(key: str, label: str) -> dict:
    return {"key": key, "label": label, "sourceText": f"{key}.{label}"}


def set_stems(group: dict, rows: list[tuple[str, str]]) -> None:
    group["stems"] = [
        {
            "text": text,
            "answer": list(answer),
            "answerMode": "多选" if len(answer) > 1 else "单选",
            "sourceText": f"{text}（{answer}）",
            "sourceY": None,
        }
        for text, answer in rows
    ]


def apply_known_repairs(group: dict) -> dict:
    """Repair deterministic OCR/split errors confirmed against source-page PNGs."""
    group_id = group["id"]
    if group_id == "p03-g1":
        for item in group["options"]:
            if item["key"] == "L" and item["label"] == "常伴消化性溃疡":
                item["key"] = "I"
        if not any(item["key"] == "L" for item in group["options"]):
            group["options"].append(option("L", "血胃泌素升高"))
        set_stems(group, [("A型胃炎", "ADEHKLN"), ("B型胃炎", "BCFGIJM")])
    elif group_id == "p04-g1":
        # The right-hand answer column spans three stems, while the final six
        # numbered options continue below the A-Z bank. Restore the complete
        # source structure and fix OCR glyph substitutions confirmed against
        # both the page scan and lecture 03.
        group["options"] = [
            option("A", "腹水"), option("B", "白蛋白合成障碍"),
            option("C", "侧支循环形成"), option("D", "凝血因子合成减少"),
            option("E", "静水压和通透性↑"), option("F", "肝肾综合征（区别内科学）"),
            option("G", "胃肠瘀血和水肿"), option("H", "肝性脑病/肝昏迷"),
            option("I", "雌激素灭活障碍"), option("J", "肝处理胆红素障碍"),
            option("K", "直肠静脉曲张"), option("L", "（最早）瘀血性脾大"),
            option("M", "蜘蛛痣，肝掌"), option("N", "氨中毒"),
            option("O", "脾亢致血小板减少"), option("P", "腹壁静脉曲张"),
            option("Q", "脾亢"), option("R", "低蛋白血症"),
            option("S", "小叶结构改变致淤胆"), option("T", "食管胃底静脉曲张"),
            option("U", "睾丸萎缩"), option("V", "淋巴液外溢"),
            option("W", "血浆胶渗压降低"), option("X", "黄疸"),
            option("Z", "出血倾向"), option("①", "门-腔侧支循环分流"),
            option("②", "乳房发育"), option("③", "醛固酮和ADH灭活障碍"),
            option("④", "白/球蛋白↓或倒置"), option("⑤", "月经不调"),
            option("⑥", "有效循环血量↓"),
        ]
        set_stems(group, [
            ("肝功能障碍临床表现", "BDFHIJMNRSUWXZ②③④⑤"),
            ("门脉高压的临床表现", "ACEGKLOPQTV①"),
            ("腹水形成的机制", "EVW③⑥"),
        ])
        group["sourceText"] = (
            group.get("sourceText", "")
            .replace("E.静水压和通透性个", "E.静水压和通透性↑")
            .replace("1.雌激素灭活障碍", "I.雌激素灭活障碍")
            .replace("U.睾丸菱缩", "U.睾丸萎缩")
            .replace("④白/球蛋白 或倒置", "④白/球蛋白↓或倒置")
            .replace("⑥有效循环血量！", "⑥有效循环血量↓")
        )
        group["reviewState"] = "已按题册原图与讲义复核"
    elif group_id == "p05-g1":
        set_stems(group, [
            ("大肠癌的癌前病变", "ABCDEFHIJLMNO"),
            ("腺瘤中最常见的是", "D"),
            ("腺瘤中易癌变的是", "O"),
        ])
    elif group_id == "p07-g1":
        set_stems(group, [
            ("变质渗出期", "ACE"), ("增生期", "B"),
            ("纤维化期", "D"), ("风湿病最有诊断意义的是", "B"),
        ])
    elif group_id == "p08-g1":
        # The OCR flattened the Roman numeral III in option B to II. Both the
        # source-page scan and lecture 07 distinguish rheumatoid arthritis
        # (type III) from rheumatic disease (type II).
        for item in group["options"]:
            if item["key"] == "B":
                item.update(option("B", "变态反应为III型"))
            elif item["key"] == "J":
                item.update(option("J", "变态反应为II型"))
        set_stems(group, [("风湿", "ACDFJKL"), ("类风湿", "BEGHILM")])
        group["sourceText"] = group.get("sourceText", "").replace(
            "B.变态反应为II型", "B.变态反应为III型", 1
        )
        group["reviewState"] = "已按题册原图与讲义复核"
    elif group_id == "p11-g1":
        set_stems(group, [("结节性甲状腺肿", "ACFHI"), ("甲状腺腺瘤", "BDEG")])
    elif group_id == "p12-g1":
        group["options"] = [
            option("A", "乳头中心砂粒体（钙化小体）"), option("B", "早期易血道转移"),
            option("C", "由未分化细胞构成，异型性显著、恶性度极高、预后最差"),
            option("D", "来源于甲状腺滤泡旁/C细胞"), option("E", "毛玻璃样核"),
            option("F", "依靠生物学行为鉴别"), option("G", "核沟、核重叠、核内假包涵体"),
            option("H", "淀粉样变性"), option("I", "早期易局部和远处转移"),
            option("J", "包膜侵犯和血管侵犯"), option("K", "分泌降钙素和5-HT等"),
            option("L", "多中心病灶，局部淋巴结转移早但预后最好"),
            option("M", "小细胞、梭形细胞、巨细胞、混合细胞型"), option("N", "TTF（+）"),
            option("O", "TTF（-）"), option("P", "TG（+）"), option("Q", "TG（-）"),
            option("R", "CT（+）"), option("S", "Syn（+）"), option("T", "最常见，好发于青少年女性"),
        ]
        set_stems(group, [
            ("乳头状癌", "AEGLNPT"), ("滤泡状癌", "BFJNP"),
            ("未分化癌", "CIMOQ"), ("髓样癌", "DHKNQRS"),
        ])
    elif group_id == "p12-g2":
        group["options"] = [
            option("A", "甲状腺不对称、结节状肿大"), option("B", "甲状腺双侧弥漫性肿大（对称）"),
            option("C", "结节大小不等、常无完整包膜"), option("D", "滤泡上皮增生呈高柱状"),
            option("E", "切面常有囊性变、出血、坏死、钙化、瘢痕等继发改变"),
            option("F", "滤泡腔内胶质稀薄，周边胶质有吸收空泡"),
            option("G", "部分滤泡上皮增生、复旧或萎缩不一致"),
            option("H", "间质血管丰富、淋巴组织增生"), option("I", "基底膜上有IgG沉着"),
        ]
        set_stems(group, [("结节性甲状腺肿", "ACEG"), ("弥漫性毒性甲状腺肿（Graves病）", "BDFHI")])
    elif group_id == "p13-g1":
        group["options"] = group["options"][:4]
        set_stems(group, [
            ("T细胞缺陷", "C"), ("B细胞和γ球蛋白缺陷", "A"),
            ("T、B细胞缺陷", "B"), ("粒细胞功能缺陷（过氧化氢产生障碍）", "D"),
        ])
    elif group_id == "p14-g2":
        set_stems(group, [("低级别鳞状上皮内病变（LSIL）", "ABEJ"), ("高级别鳞状上皮内病变（HSIL）", "CDFGHI")])
    elif group_id == "p14-g3":
        set_stems(group, [
            ("宫颈癌0期", "H"), ("宫颈癌I期", "AD"), ("宫颈癌II期", "BF"),
            ("宫颈癌III期", "CG"), ("宫颈癌IV期", "E"),
            ("早期/微小浸润癌", "A"), ("浸润癌", "ABCDEFGI"), ("原位癌", "H"),
        ])
    elif group_id == "p17-g2":
        set_stems(group, [("畸胎瘤", "ACEHJ"), ("内胚窦瘤/卵黄囊瘤", "BDFGI")])
    elif group_id == "p18-g1":
        set_stems(group, [
            ("非浸润癌", "FJL"), ("浸润癌", "ABCDEGHIKMN"),
            ("浸润癌特殊型", "BCDEHIKMN"), ("浸润癌特殊型预后较好的类型", "BDEHM"),
            ("浸润癌特殊型预后较差的类型", "CIKN"),
            ("最常见的乳腺癌类型", "A"), ("预后最差的乳腺癌类型", "C"),
        ])
    elif group_id == "p20-g1":
        for item in group["options"]:
            if item["key"] == "L" and item["label"].startswith("好发于上叶"):
                item["key"] = "I"
        if not any(item["key"] == "L" for item in group["options"]):
            group["options"].append(option("L", "传染性强的开放性肺结核"))
        set_stems(group, CONTINUATION_STEMS[20])
    elif group_id == "p22-g1":
        set_stems(group, [
            ("肠结核", "ADGH"), ("肠伤寒", "CEIJ"),
            ("急性细菌性痢疾", "FKLM"), ("肠阿米巴", "BGNO"),
        ])
    elif group_id == "p33-g2":
        group["options"] = [
            option("A", "来源于上皮组织"), option("B", "发病率低，骨肉瘤等多见于儿童和青少年"),
            option("C", "一般质硬、色灰白、干燥"), option("D", "肿瘤细胞多弥散分布，实质与间质分界不清"),
            option("E", "网状纤维围绕癌巢，癌细胞间多无网状纤维"),
            option("F", "间叶标记（波形蛋白Vimentin波+）"), option("G", "多数癌早期淋巴转移"),
            option("H", "来源于间叶组织"), option("I", "发病率高，多见于40岁以上"),
            option("J", "一般质软、色灰红、湿润、鱼肉状"),
            option("K", "癌细胞多形成癌巢，实质与间质分界清楚"),
            option("L", "肉瘤细胞间多有网状纤维"), option("M", "上皮标记角蛋白CK、EMA"),
            option("N", "血道转移"),
        ]
        set_stems(group, [("癌", "ACEGIKM"), ("肉瘤", "BDFHJLN")])
    elif group_id == "p34-g1":
        set_stems(group, [
            ("癌", "AC"), ("淋巴瘤", "DF"), ("黑色素瘤", "GI"), ("肌细胞肿瘤", "J"),
            ("肝细胞癌", "B"), ("卵巢癌", "K"), ("乳腺癌", "MQ"),
            ("卵黄囊瘤/内胚窦瘤", "B"), ("鼻咽癌", "S"), ("胰腺癌", "QP"),
            ("经典型霍奇金淋巴瘤", "S"), ("胆管癌", "PQ"), ("Burkitt淋巴瘤", "SW"),
            ("成骨性病变", "T"), ("胆囊癌", "PQ"), ("无性细胞瘤", "T"),
            ("多数腺癌", "Q"), ("肺癌尤其鳞癌", "E"), ("肺癌", "R"),
            ("NK/T细胞淋巴瘤", "S"), ("前列腺癌", "HL"),
            ("造成胆道梗阻或肝癌", "T"), ("神经内分泌肿瘤", "NV"),
            ("滋养细胞肿瘤", "U"), ("甲状腺髓样癌", "NOV"),
            ("神经元肿瘤", "V"), ("绒癌", "UW"),
        ])
    elif group_id == "p35-g1":
        set_stems(group, [
            ("多环芳烃", "AL"), ("华支睾吸虫", "H"), ("芳香胺类", "J"),
            ("日本血吸虫", "K"), ("埃及血吸虫", "M"), ("黄曲霉素", "B"),
            ("HPV", "CN"), ("亚硝胺类——结构对称者", "O"),
            ("亚硝胺类——结构不对称者", "Q"), ("EBV", "GPRT"),
            ("烷化剂", "D"), ("HBV、HCV", "B"), ("紫外线", "IS"), ("Hp", "FL"),
        ])
    return group


def extra_groups_for_page(page_number: int) -> list[dict]:
    if page_number != 18:
        return []
    group = {
        "id": "p18-g2", "page": 18, "title": "乳腺癌主要类型的病理特征",
        "kind": "B", "kindLabel": "B型题",
        "options": [
            option("A", "高级别者核分裂象常见、粉刺样坏死"),
            option("B", "以前称为浸润性导管癌，癌巢边界不清、间质纤维组织多"),
            option("C", "核分裂象罕见，癌变间期长，多累及双侧乳房多个象限"),
            option("D", "常转移至脑脊液、浆膜表面、卵巢、子宫、骨髓"),
            option("E", "巢状等结构、边界清楚、癌细胞大、间质少"),
            option("F", "癌细胞大小一致，核分裂象少，呈单行串珠状、列兵样或牛眼样排列"),
        ],
        "stems": [], "sourceText": "第18页下半部分",
        "reviewState": "已按原题页人工恢复，待讲义复核",
    }
    set_stems(group, [
        ("导管原位癌/导管内癌", "A"), ("浸润癌非特殊型", "B"),
        ("浸润性小叶癌", "DF"), ("大量淋巴细胞浸润的髓样癌", "E"),
        ("小叶原位癌", "C"),
    ])
    return [group]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    pages = shared.load_ocr(args.ocr)
    lectures = shared.build_lectures(args.lecture_dir)
    page_records = []
    groups = []
    for page_number in sorted(pages):
        if page_number < 3:
            continue
        rows = pages[page_number]
        page_text = " ".join(row["text"] for row in rows)
        if page_number == 4:
            page_text = (
                page_text
                .replace("E.静水压和通透性个", "E.静水压和通透性↑")
                .replace("1.雌激素灭活障碍", "I.雌激素灭活障碍")
                .replace("U.睾丸菱缩", "U.睾丸萎缩")
                .replace("④白/球蛋白 或倒置", "④白/球蛋白↓或倒置")
                .replace("⑥有效循环血量！", "⑥有效循环血量↓")
            )
        if page_number == 8:
            page_text = page_text.replace(
                "B.变态反应为II型", "B.变态反应为III型", 1
            )
        page_topic = topic_for(page_text, page_number)
        page_records.append({
            "page": page_number,
            "image": f"pathology/source-pages/page-{page_number:02d}.png",
            "topic": page_topic,
            "searchText": shared.clean_text(page_text)[:7000],
        })
        extracted_groups = shared.extract_groups(page_number, rows) + extra_groups_for_page(page_number)
        for raw_group in extracted_groups:
            group = repair_continuation_group(raw_group)
            group = apply_known_repairs(group)
            for stem in group.get("stems", []):
                stem["answer"] = list(dict.fromkeys(stem.get("answer", [])))
                stem["answerMode"] = "多选" if len(stem["answer"]) > 1 else "单选"
            group_text = " ".join([
                group.get("title", ""),
                group.get("sourceText", ""),
                *(option.get("label", "") for option in group.get("options", [])),
                *(stem.get("text", "") for stem in group.get("stems", [])),
            ])
            group["topic"] = topic_for(group_text, page_number)
            group["topic"] = GROUP_TOPIC_OVERRIDES.get(group["id"], group["topic"])
            group["title"] = TITLE_OVERRIDES.get(group["id"], group["title"])
            if group["id"] in GROUP_LECTURE_OVERRIDES:
                group["lectureIds"] = GROUP_LECTURE_OVERRIDES[group["id"]]
            elif 13 <= page_number <= 14 and group["id"] == "p14-g1":
                group["lectureIds"] = ["lecture-17"]
            elif 14 <= page_number <= 17:
                group["lectureIds"] = ["lecture-18"]
            elif page_number == 18:
                group["lectureIds"] = ["lecture-19"]
            elif 19 <= page_number <= 20:
                group["lectureIds"] = ["lecture-20"]
            elif 21 <= page_number <= 23:
                group["lectureIds"] = ["lecture-21"]
            elif page_number == 24:
                group["lectureIds"] = ["lecture-22"]
            elif 25 <= page_number <= 29:
                group["lectureIds"] = ["lecture-23"]
            elif page_number == 30:
                group["lectureIds"] = ["lecture-24"]
            elif 31 <= page_number <= 32:
                group["lectureIds"] = ["lecture-25"]
            elif 33 <= page_number <= 37:
                group["lectureIds"] = ["lecture-26"]
            else:
                group["lectureIds"] = related_lectures(group["topic"], lectures)
            groups.append(group)

    topics = ["全部"] + list(dict.fromkeys(PAGE_FALLBACK.values())) + ["综合"]
    payload = {
        "meta": {
            "title": "病理学题库",
            "sourcePdf": "病理学西综-学成选择题(去胶带版).pdf",
            "sourcePages": len(page_records),
            "sourcePdfPages": len(pages),
            "lectureCount": len(lectures),
            "generatedBy": "scripts/build_pathology_content.py",
            "siteIntegrated": True,
            "answerNote": "题册答案按原图保留，并对连续表格、OCR 字母混淆和缺失题组进行了人工修复。",
        },
        "topics": topics,
        "pages": page_records,
        "groups": groups,
        "lectures": lectures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pages": len(page_records),
        "lectures": len(lectures),
        "groups": len(groups),
        "stems": sum(len(group.get("stems", [])) for group in groups),
        "types": dict(Counter(group["kind"] for group in groups)),
        "topics": dict(Counter(group["topic"] for group in groups)),
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
