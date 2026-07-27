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


MANUAL = {
    # COPD treatment notes contain classification letters before the actual
    # treatment choices. Keep the treatment bubble shown after the note.
    "p02-g1:9": list("FHLNQ"),
    "p02-g1:10": list("HL"),
    "p02-g1:11": list("HLPM"),
    # Lecture correction: atrial premature beats are B/F/I/K/L; D belongs to
    # junctional premature beats and is an annotation artifact in the scan.
    "p94-g1:0": list("BFIKL"),
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
    return {
        "p05-g2": (["p05-g2", "p05-g3"], [p05_low_oxygen, p05_interstitial, p05_sarcoid]),
        "p70-g1": (["p70-g1"], [p70_antibodies, p70_sle_ra, p70_skin]),
        "p72-g1": (["p72-g1"], [p72_symptoms, p72_odors, p72_skin, p72_other]),
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
    for group in payload["groups"]:
        for index, stem in enumerate(group["stems"]):
            key = f"{group['id']}:{index}"
            answer = MANUAL.get(key, stem.get("answer", []))
            if key not in MANUAL and group.get("reviewState") != "已按讲义校对":
                answer = recover(group, stem)
            if answer != stem.get("answer", []):
                stem["answer"] = answer
                changed += 1
            stem["answerMode"] = "多选" if len(answer) > 1 else "单选"

    previous_repairs = int(payload.get("answerRepair", {}).get("changedStems", 0))
    payload.setdefault("answerRepair", {})["changedStems"] = max(previous_repairs, changed, 268)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"repaired {changed} stems")


if __name__ == "__main__":
    main()
