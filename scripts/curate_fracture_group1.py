#!/usr/bin/env python3
"""Split and reshuffle the bundled facts in fracture overview group 1."""

from __future__ import annotations

import json
from pathlib import Path

from shuffle_fracture_options import reshuffle_group


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/data/surgery-fracture-data.json"


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    group = next(item for item in payload["groups"] if item["id"] == "fracture-g01")

    options = [
        ("A", "肱骨髁上骨折", "间接暴力：肱骨髁上骨折"),
        ("B", "好发于第2、3跖骨", "疲劳骨折：好发于第2、3跖骨"),
        ("C", "胫骨干骨折", "直接暴力：胫骨干骨折"),
        ("D", "骨骼本身存在骨髓炎、骨肿瘤等疾病，受轻微外力即发生骨折", "病理骨折：骨骼本身存在骨髓炎、骨肿瘤等疾病，受轻微外力即发生骨折"),
        ("E", "髂前上棘撕脱骨折", "间接暴力：髂前上棘撕脱骨折"),
        ("F", "早期诊断可用MRI、核素检查", "疲劳骨折：早期诊断可用MRI、核素检查"),
        ("G", "髌骨粉碎性骨折", "直接暴力：髌骨粉碎性骨折"),
        ("H", "好发于肋骨", "疲劳骨折：好发于肋骨"),
        ("I", "桡骨远端骨折", "间接暴力：桡骨远端骨折"),
        ("J", "反复轻微外力导致特定部位积累性劳损", "疲劳骨折：反复轻微外力导致特定部位积累性劳损"),
        ("K", "髌骨横形骨折", "间接暴力：髌骨横形骨折"),
        ("L", "好发于腓骨干下1/3", "疲劳骨折：好发于腓骨干下1/3"),
    ]
    group["options"] = [
        {"key": key, "label": label, "sourceText": source_text, "sourceKey": key, "ocrScore": 1.0}
        for key, label, source_text in options
    ]
    answers = {
        "直接暴力": ["C", "G"],
        "间接暴力（受伤部位远处）": ["A", "E", "I", "K"],
        "病理骨折": ["D"],
        "疲劳/应力/行军骨折": ["B", "F", "H", "J", "L"],
    }
    for stem in group["stems"]:
        stem["answer"] = answers[stem["text"]]
        stem["answerMode"] = "单选" if len(stem["answer"]) == 1 else "多选"
        stem["reviewMethod"] = "已按第29讲第1页拆分骨折类型与好发部位，固定乱序后同步重映射答案"

    group["sourceText"] = "；".join(label for _, label, _ in options) + "；" + "；".join(answers)
    group["optionOriginalOrder"] = [key for key, _, _ in options]
    group["optionShuffleVersion"] = 0
    group["lectureEvidence"]["description"] = "骨折原因、各暴力类型对应骨折及疲劳骨折好发部位已拆分并逐项复核。"
    reshuffle_group(group)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
