#!/usr/bin/env python3
"""Audit the integrated surgery payload and source-page assets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


VERIFIED_GROUPS = {
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
