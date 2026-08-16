#!/usr/bin/env python3
"""Validate the lecture-28 limb fracture and dislocation question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_SOURCE_ANSWERS = {
    "limb-fracture-dislocation-g01": [set(x) for x in ["A", "D", "G", "I", "K", "A", "J", "E", "C", "B", "H", "L", "F"]],
    "limb-fracture-dislocation-g02": [set(x) for x in ["FHL", "ABGNR", "EIK", "S", "CDJO", "BPT", "MQ"]],
    "limb-fracture-dislocation-g03": [set(x) for x in ["E", "GM", "HJ", "K", "I", "BCD", "F", "AL"]],
    "limb-fracture-dislocation-g04": [
        set(x) for x in ["DJKLPQU", "DJRST", "DGHJ", "BCIMOU", "ABEFNUV"]
    ],
    "limb-fracture-dislocation-g05": [set(x) for x in ["A", "E", "D", "B", "C"]],
    "limb-fracture-dislocation-g06": [set(x) for x in ["A", "F", "G", "B", "J", "D", "I", "K", "H", "E", "C"]],
    "limb-fracture-dislocation-g07": [set(x) for x in ["E", "A", "L", "J", "B", "H", "G", "H", "O", "F", "N", "I", "CM"]],
    "limb-fracture-dislocation-g08": [set(x) for x in ["EGI", "C", "A", "D", "JK", "N", "B", "FL", "M", "H"]],
    "limb-fracture-dislocation-g09": [set(x) for x in ["BCD", "AE", "F"]],
}

EXPECTED_FILL = [
    ["1", "45"], ["30", "50"], ["10"], ["5"], ["3"], ["2", "4", "8", "10"],
    ["45", "60", "90"], ["12", "15"], ["3", "3"], ["0.5"], ["1/4", "1/3"],
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-limb-fracture-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 10
    assert sum(len(group["stems"]) for group in groups) == 86
    assert sum(len(group["options"]) for group in groups) == 116
    assert payload["meta"]["lecturePagesReviewed"] == list(range(1, 16))
    assert [group["id"] for group in groups[:9]] == list(EXPECTED_SOURCE_ANSWERS)

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-28"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True and group["parseWarnings"] == []
        assert group["sourcePdf"] is None and group["sourceImage"] is None
        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-28"
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"
        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    for group in groups[:9]:
        expected_version = 3 if group["id"] in {
            "limb-fracture-dislocation-g03",
            "limb-fracture-dislocation-g06",
            "limb-fracture-dislocation-g07",
            "limb-fracture-dislocation-g08",
        } else 2
        if group["id"] == "limb-fracture-dislocation-g04":
            expected_version = 4
        assert group["kindLabel"] == "B型题" and group["optionShuffleVersion"] == expected_version
        option_keys = [option["key"] for option in group["options"]]
        option_labels = [option["label"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        used_keys = {key for stem in group["stems"] for key in stem["answer"]}
        assert len(option_labels) == len(set(option_labels)), f"{group['id']}: duplicate option labels"
        assert used_keys == set(option_keys), f"{group['id']}: unused or unreachable options"
        assert source_keys != group["optionOriginalOrder"]
        assert set(source_keys) == set(group["optionOriginalOrder"])
        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [{display_to_source[key] for key in stem["answer"]} for stem in group["stems"]]
        assert semantic_answers == EXPECTED_SOURCE_ANSWERS[group["id"]], f"{group['id']}: answer remapping drift"
        assert all(stem["answer"] and set(stem["answer"]) <= set(option_keys) for stem in group["stems"])

    fill = groups[9]
    assert fill["kind"] == "FILL" and fill["kindLabel"] == "填空题"
    assert fill["options"] == [] and fill["optionOriginalOrder"] == []
    assert [stem["answer"] for stem in fill["stems"]] == EXPECTED_FILL
    assert all(len(stem["answer"]) == len(stem["blankLabels"]) for stem in fill["stems"])

    forearm, hip, femoral_neck, treatment, complications = (groups[index] for index in (2, 3, 5, 6, 7))
    assert option_label(forearm, "K") == "先复位桡骨"
    assert option_label(forearm, "I") == "先复位尺骨"
    assert option_label(forearm, "J") == "需达到解剖复位"
    assert option_label(hip, "K") == "最常见的髋关节脱位类型"
    assert option_label(hip, "G") == "最凶险的髋关节脱位类型"
    assert option_label(hip, "F") == "跌倒等外伤或病理性骨折"
    assert len(hip["options"]) == 22
    assert [stem["text"] for stem in hip["stems"]] == [
        "髋关节后脱位", "髋关节前脱位", "髋关节中心脱位", "股骨颈骨折", "股骨转子间骨折"
    ]
    assert option_label(hip, "R") == "屈曲、外展、外旋畸形"
    assert option_label(hip, "S") == "腹股沟可触及股骨头"
    assert option_label(hip, "T") == "下肢长度不定"
    assert option_label(hip, "P") == "臀部可触及股骨头"
    assert option_label(hip, "Q") == "可损伤坐骨神经"
    assert option_label(hip, "U") == "下肢缩短"
    assert option_label(hip, "V") == "囊外骨折"
    assert option_label(femoral_neck, "A") == "骨折线位于股骨头下方，预后最差"
    assert option_label(femoral_neck, "F") == "骨折线位于股骨颈中部"
    assert option_label(femoral_neck, "G") == "骨折线位于股骨颈基底部，预后最好"
    assert len(treatment["stems"]) == 13 and all(option["sourceKey"] not in {"D", "K"} for option in treatment["options"])
    assert option_label(treatment, "B") == "螺钉内固定"
    assert treatment["stems"][-1]["text"] == "三踝骨折"
    assert any(stem["text"] == "股骨颈骨折：闭合复位后的固定方式" for stem in treatment["stems"])
    forbidden_prefixes = ("上1/3：", "中1/3：", "下1/3：", "股骨干中1/3", "股骨干下1/3")
    assert not any(option["label"].startswith(forbidden_prefixes) for option in complications["options"])
    assert option_label(complications, "M") == "粉碎性骨折"
    assert option_label(complications, "H") == "横形骨折"

    print({"groups": 10, "stems": 86, "options": 116, "shuffled": 9, "fill": 1, "status": "ok"})


def option_label(group: dict, source_key: str) -> str:
    return next(option["label"] for option in group["options"] if option["sourceKey"] == source_key)


if __name__ == "__main__":
    main()
