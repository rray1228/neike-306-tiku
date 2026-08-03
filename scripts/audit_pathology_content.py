#!/usr/bin/env python3
"""Structural checks for the standalone pathology payload."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/pathology-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["sourcePdfPages"] == 37
    assert payload["meta"]["sourcePages"] == 35
    assert payload["meta"]["lectureCount"] == 26

    ids = [group["id"] for group in payload["groups"]]
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert all(group["page"] >= 3 for group in payload["groups"])
    assert all(group.get("stems") for group in payload["groups"]), "empty question group"

    invalid_answers = []
    duplicate_answers = []
    missing_images = []
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        keys = {option["key"] for option in group.get("options", [])}
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            if len(answer) != len(set(answer)):
                duplicate_answers.append(f"{group['id']}:{index}")
            absent = [key for key in answer if key not in keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{index}={''.join(absent)}")

    assert not missing_images, f"missing source images: {missing_images}"
    assert not duplicate_answers, f"duplicate answer keys: {duplicate_answers}"
    assert not invalid_answers, f"answers missing from option bank: {invalid_answers}"

    cirrhosis = next(group for group in payload["groups"] if group["id"] == "p04-g1")
    cirrhosis_options = {
        option["key"]: option["label"] for option in cirrhosis["options"]
    }
    cirrhosis_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in cirrhosis["stems"]
    }
    assert cirrhosis_options["E"] == "静水压和通透性↑"
    assert cirrhosis_options["I"] == "雌激素灭活障碍"
    assert cirrhosis_options["U"] == "睾丸萎缩"
    assert cirrhosis_options["④"] == "白/球蛋白↓或倒置"
    assert cirrhosis_options["⑥"] == "有效循环血量↓"
    assert set("①②③④⑤⑥").issubset(cirrhosis_options)
    assert cirrhosis_answers == {
        "肝功能障碍临床表现": "BDFHIJMNRSUWXZ②③④⑤",
        "门脉高压的临床表现": "ACEGKLOPQTV①",
        "腹水形成的机制": "EVW③⑥",
    }
    assert cirrhosis["reviewState"] == "已按题册原图与讲义复核"

    rheumatism = next(group for group in payload["groups"] if group["id"] == "p08-g1")
    rheumatism_options = {
        option["key"]: option["label"] for option in rheumatism["options"]
    }
    rheumatism_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in rheumatism["stems"]
    }
    assert rheumatism_options["B"] == "变态反应为III型"
    assert rheumatism_options["J"] == "变态反应为II型"
    assert rheumatism_answers == {
        "风湿": "ACDFJKL",
        "类风湿": "BEGHILM",
    }
    assert rheumatism["reviewState"] == "已按题册原图与讲义复核"

    groups_by_id = {group["id"]: group for group in payload["groups"]}

    def assert_group(
        group_id: str,
        expected_options: list[tuple[str, str]],
        expected_answers: list[tuple[str, str]],
    ) -> None:
        group = groups_by_id[group_id]
        actual_options = [(item["key"], item["label"]) for item in group["options"]]
        actual_answers = [
            (stem["text"], "".join(stem["answer"])) for stem in group["stems"]
        ]
        assert actual_options == expected_options, f"{group_id} option mismatch"
        assert actual_answers == expected_answers, f"{group_id} answer mismatch"
        assert group["reviewState"] == "已按题册原图与讲义复核"

    thyroid = groups_by_id["p11-g1"]
    thyroid_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in thyroid["stems"]
    }
    assert thyroid_answers["甲状腺腺瘤"] == "BDEGI"
    assert "I" in thyroid_answers["甲状腺腺瘤"]
    assert thyroid["reviewState"] == "已按题册原图与讲义复核"

    respiratory_ids = [
        group["id"] for group in payload["groups"] if group["topic"] == "呼吸系统"
    ]
    assert respiratory_ids == [
        "p09-g1", "p09-g2", "p09-g3",
        "p10-g1", "p10-g2", "p10-g3", "p10-g4",
    ]

    assert_group(
        "p09-g2",
        [
            ("A", "中性粒细胞活跃导致内源性弹性蛋白酶增多"),
            ("B", "破坏终末细支气管、一级呼吸性细支气管的管壁结构，导致管壁纤维化和管腔狭窄"),
            ("C", "纤毛柱状上皮受损和鳞化导致黏液潴留"),
            ("D", "氧自由基增多导致α1-抗胰蛋白酶减少"),
            ("E", "柱状细胞增多、腺体增生肥大、黏液腺化生，导致呼吸道黏液增多"),
        ],
        [("与细支气管不完全阻塞有关", "BCE"), ("与末梢肺组织弹性减弱有关", "AD")],
    )
    assert_group(
        "p09-g3",
        [
            ("A", "肋骨骨折"), ("B", "腺泡中央型"),
            ("C", "代偿性肺气肿"), ("D", "胸部穿透伤"),
            ("E", "老年性肺气肿"), ("F", "腺泡周围型"),
            ("G", "剧烈咳嗽"), ("H", "全腺泡型"),
            ("I", "瘢痕旁肺气肿（不规则肺气肿）"),
            ("J", "串珠状气泡"), ("K", "皮下气肿"),
        ],
        [("肺泡性/阻塞性肺气肿", "BFH"), ("间质性肺气肿", "ADGJK"), ("其他类型肺气肿", "CEI")],
    )
    assert "I" in "".join(groups_by_id["p09-g3"]["stems"][2]["answer"])
    assert_group(
        "p10-g1",
        [
            ("A", "属于肺泡性/阻塞性肺气肿"), ("B", "瘢痕牵拉"),
            ("C", "累及肺腺泡的结构不定，主要累及肺泡"),
            ("D", "属于其他类型肺气肿"),
            ("E", "累及腺泡远端的所有结构（肺泡管/肺泡囊），即腺泡远端肺气肿"),
        ],
        [("瘢痕旁/不规则肺气肿", "BCD"), ("腺泡周围型/间隔旁型肺气肿", "ABE")],
    )
    assert_group(
        "p10-g2",
        [
            ("A", "军团菌肺炎"), ("B", "病毒性肺炎"),
            ("C", "大叶性肺炎"), ("D", "支原体肺炎"),
            ("E", "小叶性/支气管肺炎"), ("F", "衣原体肺炎"),
        ],
        [("细菌性肺炎", "ACE"), ("间质性肺炎", "BDF")],
    )
    assert_group(
        "p10-g3",
        [
            ("A", "肺泡的纤维素性炎"),
            ("B", "细支气管及末梢肺组织的化脓性炎"),
            ("C", "可呈小叶、大叶等分布"),
            ("D", "以细支气管为中心"),
            ("E", "纤维素性化脓性炎"),
        ],
        [("大叶性肺炎", "A"), ("小叶性/支气管肺炎", "BD"), ("军团菌肺炎", "CE")],
    )
    assert_group(
        "p10-g4",
        [("A", "胞核+胞质"), ("B", "胞质（嗜酸性）"), ("C", "胞核（嗜碱性）")],
        [
            ("单纯疱疹病毒", "C"), ("呼吸道合胞病毒", "B"),
            ("麻疹病毒", "A"), ("腺病毒", "C"), ("巨细胞病毒", "C"),
        ],
    )

    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group.get("stems", [])) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
