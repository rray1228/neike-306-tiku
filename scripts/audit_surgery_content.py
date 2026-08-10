#!/usr/bin/env python3
"""Audit the integrated surgery payload and source-page assets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


VERIFIED_GROUPS = {
    "p11-g1": {
        "title": "急性阑尾炎分型",
        "options": {
            "A": "症状轻、无肌紧张", "B": "切口麦氏点",
            "C": "切口右下腹经腹直肌",
            "D": "局限性腹膜炎（局部压痛/反跳痛/肌紧张），阑尾腔内积脓",
            "E": "生理盐水不冲腹腔", "F": "生理盐水冲腹腔",
            "G": "围术期用抗生素", "H": "看情况放引流", "I": "不放引流",
            "J": "生理盐水冲腹腔看情况",
            "K": "阑尾呈暗紫色，腹痛可暂时减轻、但随即弥漫性腹膜炎（全腹压痛/反跳痛/肌紧张），体温进一步升高、肠鸣音、甚至休克",
            "L": "切口偏高",
        },
        "stems": {
            "单纯性": "ABEGI", "化脓性": "BDG", "脓液少": "EI",
            "脓液多": "FH", "坏疽穿孔性": "CFGHK", "妊娠期": "GIJL",
        },
    },
    "p14-g2": {
        "title": "腹股沟管结构",
        "options": {
            "A": "腹股沟镰（腹内斜肌和腹横肌腱膜构成的联合腱）",
            "B": "腹外斜肌腱膜（主要）", "C": "腹横筋膜", "D": "腹内斜肌",
            "F": "腹股沟韧带（腹外斜肌腱膜卷曲形成）", "G": "腹膜",
            "H": "腹横肌", "I": "腔隙韧带",
        },
        "stems": {"前": "BD", "后": "ACG", "上": "DH", "下": "FI"},
    },
    "p28-g1": {
        "title": "泌尿系结石成分与特点",
        "options": {
            "A": "易碎", "B": "硬", "C": "光滑", "D": "蜡样", "E": "鹿角样",
            "F": "桑葚样", "G": "颗粒状", "H": "灰白色", "I": "棕褐色",
            "J": "红色", "K": "黄色", "L": "糙", "M": "最常见",
            "N": "酸化尿液+抗感染", "O": "X线高密度", "P": "X线不显影",
        },
        "stems": {
            "草酸钙": "BFILMO", "磷酸钙": "AEHLNO",
            "尿酸盐": "BCGJP", "胱氨酸": "BCDKP",
        },
    },
    "p29-g4": {
        "title": "尿失禁类型",
        "options": {
            "A": "尿液不连续从尿道口不自主流出、呈滴沥样、夜间多见",
            "B": "假性尿失禁",
            "C": "完全失去控制排尿的能力，任何时间、体位下尿液均会持续不自主从尿道口流出",
            "D": "患者每次排尿时尿液都难以排尽、膀胱内残余尿逐渐增多、膀胱过度充盈导致膀胱内压超过尿道阻力",
            "E": "多见于膀胱炎、神经源性膀胱、重度膀胱出口梗阻引起的膀胱不稳定收缩",
            "F": "平常控制排尿能力正常，但咳嗽、起立等腹内压增加时少量尿液不自主从尿道口流出",
            "G": "多见于外伤、手术、先天性疾病引起的膀胱颈和尿道括约肌损伤",
            "H": "多见于前列腺增生、肿瘤、尿道狭窄等下尿路慢性梗阻或神经系统疾病导致膀胱逼尿肌收缩无力",
            "I": "严重的尿频、尿急而膀胱不受意识控制就开始排尿",
            "J": "真性尿失禁",
            "K": "多见于多产妇、绝经后引起的阴道前壁支撑力下降和盆腔组织功能障碍或前列腺手术后引起的尿道外括约肌损伤",
        },
        "stems": {
            "持续性尿失禁": "CGJ", "充溢性尿失禁": "ABDH",
            "急迫性尿失禁": "EI", "压力性尿失禁": "FK",
        },
    },
}

VERIFIED_HERNIA_GROUPS = {
    "p14-g1": ("股管结构", "ABCD", {"前": "C", "后": "B", "内": "A", "外": "D"}),
    "p14-g2": ("腹股沟管结构", "ABCDFGHI", {"前": "BD", "后": "ACG", "上": "DH", "下": "FI"}),
    "p14-g3": ("直疝三角/海氏三角/Hesselbach 三角", "ABC", {"内侧": "B", "底部": "C", "外侧": "A"}),
    "p14-g4": ("疝的组成", "AB", {"疝内容物": "B", "疝囊": "A"}),
    "p14-g5": ("腹外疝临床分型", "ABCDEFGH", {"易复疝": "ACD", "难复疝": "ADE", "嵌顿疝": "ABEGH", "绞窄疝": "BEF"}),
    "p14-g6": ("腹外疝类型与常见内容物", "ABCDEF", {"易复疝": "B", "难复疝": "D", "特殊的难复疝-滑动性疝": "ACEF"}),
    "p15-g1": ("特殊类型嵌顿疝", "ABCDE", {"Richter疝（肠管壁疝）": "B", "Littre疝": "A", "Maydl疝（逆行性嵌顿疝）": "EC", "Amyand疝": "D"}),
    "p15-g2": ("腹外疝治疗方式", "ABCDE", {"保守": "BCE", "单纯疝囊高位结扎": "AD"}),
    "p15-g3": ("腹股沟疝修补术式", "ABCDEFGH", {"单纯疝修补/无张力疝修补": "CEG", "疝囊高位结扎+修补加强前壁": "A", "加强后壁": "BDFH"}),
    "p15-g4": ("传统疝修补术特点", "ABCDEF", {"Bassini": "B", "McVay": "ADF", "Shouldice": "CE"}),
    "p16-g1": ("股疝、斜疝与直疝鉴别", "ABCDEFGHIJKLMNOPQRSTUV", {"股疝": "ADHIKNT", "斜疝": "CFJLMOQSU", "直疝": "BCEGIKPRV"}),
    "p16-g2": ("隐睾（阴囊空虚感）治疗", "ABCDE", {"1岁内": "D", "1岁后": "A", "2岁前": "E", "睾丸萎缩且对侧睾丸正常": "B", "双侧睾丸不能下降": "C"}),
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["sourcePdfPages"] == 29
    assert payload["meta"]["sourcePages"] == 29
    assert payload["meta"]["lectureCount"] == 38

    ids = [group["id"] for group in payload["groups"]]
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert all(group.get("stems") for group in payload["groups"]), "empty question group"

    invalid_answers = []
    duplicate_answers = []
    duplicate_option_keys = []
    empty_answers = []
    text_issues = []
    missing_images = []
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        option_keys = [option["key"] for option in group.get("options", [])]
        keys = set(option_keys)
        if len(option_keys) != len(keys):
            duplicate_option_keys.append(group["id"])
        if group.get("reviewState") == "待原题页核对" or group.get("reviewIssues"):
            text_issues.append(f"{group['id']}:review")
        values = [group.get("title", "")]
        values.extend(option.get("label", "") for option in group.get("options", []))
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            values.append(stem.get("text", ""))
            if stem.get("answerState") or not answer:
                empty_answers.append(f"{group['id']}:{index}")
            if len(answer) != len(set(answer)):
                duplicate_answers.append(f"{group['id']}:{index}")
            absent = [key for key in answer if key not in keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{index}={''.join(absent)}")
        for value in values:
            if (
                not value.strip()
                or any(char in value for char in "|°•“”‘’")
                or "请结合原题页" in value
                or value.count("（") != value.count("）")
                or value.count("(") != value.count(")")
                or re.search(r"\s{2,}", value)
            ):
                text_issues.append(f"{group['id']}:{value}")

    assert not missing_images, f"missing source images: {missing_images}"
    assert not duplicate_option_keys, f"duplicate option keys: {duplicate_option_keys}"
    assert not empty_answers, f"empty or unresolved answers: {empty_answers}"
    assert not duplicate_answers, f"duplicate answer keys: {duplicate_answers}"
    assert not invalid_answers, f"answers missing from option bank: {invalid_answers}"
    assert not text_issues, f"text/review issues: {text_issues}"

    groups_by_id = {group["id"]: group for group in payload["groups"]}
    for group_id, expected in VERIFIED_GROUPS.items():
        group = groups_by_id[group_id]
        assert group["title"] == expected["title"], f"{group_id}: title drift"
        assert {item["key"]: item["label"] for item in group["options"]} == expected["options"], \
            f"{group_id}: option drift"
        assert {item["text"]: "".join(item["answer"]) for item in group["stems"]} == expected["stems"], \
            f"{group_id}: stem/answer drift"

    hernia_ids = {group["id"] for group in payload["groups"] if group["topic"] == "腹外疝"}
    assert hernia_ids == set(VERIFIED_HERNIA_GROUPS), f"hernia group drift: {sorted(hernia_ids)}"
    for group_id, (title, option_keys, stems) in VERIFIED_HERNIA_GROUPS.items():
        group = groups_by_id[group_id]
        assert group["title"] == title, f"{group_id}: title drift"
        assert "".join(item["key"] for item in group["options"]) == option_keys, f"{group_id}: option-key drift"
        assert {item["text"]: "".join(item["answer"]) for item in group["stems"]} == stems, \
            f"{group_id}: hernia stem/answer drift"
        assert group["reviewState"] == "已按原题页人工复核", f"{group_id}: review state drift"

    phosphate_evidence = groups_by_id["p28-g1"]["lectureEvidence"]
    assert phosphate_evidence == {
        "lectureId": "lecture-19",
        "page": 1,
        "image": "surgery/lecture-pages/lecture-19-page-01.png",
        "title": "第19讲第1页 · 泌尿系结石",
        "description": "讲义在“磷酸钙”条目下明确列出“酸化尿液+抗感染”，因此本题答案包含 N。",
    }, "p28-g1: lecture evidence drift"
    lecture_image = root / "public" / phosphate_evidence["image"]
    assert lecture_image.exists(), f"missing lecture evidence image: {lecture_image}"

    unresolved = [
        f"{group['id']}:{index}"
        for group in payload["groups"]
        for index, stem in enumerate(group["stems"])
        if stem.get("answerState")
    ]
    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group["stems"]) for group in payload["groups"]),
        "resolved": sum(
            1 for group in payload["groups"] for stem in group["stems"]
            if not stem.get("answerState")
        ),
        "unresolved": len(unresolved),
        "reviewStates": dict(Counter(group["reviewState"] for group in payload["groups"])),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
