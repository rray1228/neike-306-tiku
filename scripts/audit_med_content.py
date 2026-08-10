#!/usr/bin/env python3
"""Fail-fast integrity checks for the internal-medicine question payload."""

from __future__ import annotations

import json
from pathlib import Path


def expected_topic(page: int) -> str:
    if page == 1:
        return "综合"
    if 2 <= page <= 19:
        return "呼吸"
    if 20 <= page <= 34:
        return "消化"
    if 35 <= page <= 41:
        return "肾脏"
    if 42 <= page <= 60:
        return "血液"
    if 61 <= page <= 68:
        return "内分泌"
    if 69 <= page <= 71:
        return "风湿"
    if 72 <= page <= 74:
        return "中毒"
    return "循环"


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "src/data/med-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["lectures"]) == 57, "lecture count changed"
    assert payload["meta"]["sourcePages"] == 97, "source page count changed"

    invalid = []
    duplicate = []
    topic_errors = []
    empty_groups = []
    mode_errors = []
    ids = []
    for group in payload["groups"]:
        ids.append(group["id"])
        if group.get("topic") != expected_topic(group["page"]):
            topic_errors.append(f"{group['id']}={group.get('topic')}")
        if group["page"] != 1 and not group.get("stems"):
            empty_groups.append(group["id"])
        keys = {option["key"] for option in group.get("options", [])}
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            if len(answer) != len(set(answer)):
                duplicate.append(f"{group['id']}:{index}")
            invalid_keys = [key for key in answer if key not in keys]
            if invalid_keys:
                invalid.append(f"{group['id']}:{index}={''.join(invalid_keys)}")
            if answer and stem.get("answerMode") != ("多选" if len(answer) > 1 else "单选") and stem.get("answerMode") != "待核对":
                mode_errors.append(f"{group['id']}:{index}")

    assert not duplicate, f"duplicate answer keys: {duplicate}"
    assert not invalid, f"answer keys absent from option bank: {invalid}"
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert not topic_errors, f"wrong page topic mapping: {topic_errors}"
    assert not empty_groups, f"empty question groups: {empty_groups}"
    assert not mode_errors, f"answer mode mismatch: {mode_errors}"

    by_id = {group["id"]: group for group in payload["groups"]}
    assert [item["label"] for item in by_id["p07-g1"]["options"]] == ["多无咯血", "长期咳痰", "大量脓痰", "多有咯血和杵状指"]
    assert [stem["text"] for stem in by_id["p07-g1"]["stems"]] == ["支气管扩张症", "COPD"]
    assert len(by_id["p19-g1"]["stems"]) == 7, "p19 comparison bank was merged or truncated"
    assert [group["id"] for group in payload["groups"] if group["page"] == 22] == ["p22-g1", "p22-g2"], "page 22 question banks were merged"
    assert [stem["answer"] for stem in by_id["p22-g1"]["stems"]] == [list("BCEFGIJMP"), list("ADHKLNOQ")]
    assert [option["key"] for option in by_id["p22-g2"]["options"]] == list("ABCDEFGH")
    assert [stem["answer"] for stem in by_id["p22-g2"]["stems"]] == [list("BF"), list("D"), list("AE"), list("CG"), list("H")]
    assert [group["id"] for group in payload["groups"] if group["page"] == 46] == ["p46-g1", "p46-g2", "p46-g3"]
    assert [group["id"] for group in payload["groups"] if group["page"] == 49] == ["p49-g1", "p49-g2", "p49-g3"]
    assert [group["id"] for group in payload["groups"] if group["page"] == 52] == ["p52-g1", "p52-g2", "p52-g3", "p52-g4"]
    assert [group["id"] for group in payload["groups"] if group["page"] == 53] == ["p53-g1", "p53-g2", "p53-g3", "p53-g4"]
    assert [group["id"] for group in payload["groups"] if group["page"] == 69] == ["p69-g1", "p69-g2", "p69-g3"]
    assert by_id["p46-g3"]["stems"][-1]["answer"] == list("FHI")
    assert by_id["p53-g1"]["stems"][1]["answer"] == list("ACGJ")
    assert by_id["p69-g1"]["options"][1]["label"] == "杵状指"
    assert len([group for group in payload["groups"] if group["page"] == 61]) == 3
    assert len([group for group in payload["groups"] if group["page"] == 64]) == 2
    assert by_id["p64-g1"]["topic"] == "内分泌"
    assert len([group for group in payload["groups"] if group["page"] == 80]) == 3
    assert len([group for group in payload["groups"] if group["page"] == 94]) == 4
    assert by_id["p13-g1"]["stems"][0]["text"] == "可有杵状指"
    assert by_id["p13-g1"]["stems"][4]["text"] == "5-HT"
    assert by_id["p14-g1"]["title"] == "肺癌TNM分期"
    assert [stem["text"] for stem in by_id["p14-g1"]["stems"]] == ["T1", "T2", "T3", "T4", "N0", "N1", "N2", "N3", "M0", "远处转移（M1）"]
    assert by_id["p16-g1"]["options"][13]["label"] == "细胞计数多<100×10^6/L"
    assert by_id["p16-g2"]["options"][2]["label"] == "膈神经麻痹"
    assert [option["key"] for option in by_id["p11-g1"]["options"]] == list("ABCDEFGHIJKLM")
    assert by_id["p11-g1"]["options"][-1]["label"] == "抗IL-4R抗体/抗TSLP抗体"
    assert by_id["p20-g1"]["topic"] == "消化" and by_id["p20-g2"]["topic"] == "消化"
    assert by_id["p85-g1"]["stems"][1]["answer"] == list("ABDFJLNSUaegikmqrv①")
    assert by_id["p85-g1"]["options"][26]["label"] == "有相对性二尖瓣狭窄"
    assert by_id["p85-g1"]["options"][27]["label"] == "有相对性主动脉瓣狭窄"
    assert by_id["p85-g1"]["options"][11]["label"] == "左室：慢性后期离心性肥厚；急性早期正常或轻度扩大"
    assert by_id["p85-g1"]["options"][49]["label"] == "成人：置换术，若老龄重度不耐受TAVR"
    assert by_id["p38-g1"]["topic"] == "血液"
    assert by_id["p38-g1"]["lectureIds"] == ["lecture-28"]
    assert by_id["p87-g3"]["options"][3]["label"] == "明显诱因胸痛，多持续3～5分钟"
    assert [option["key"] for option in by_id["p88-g1"]["options"]] == list("ABCDEFGHIJKL")

    all_text = " ".join(stem.get("text", "") for group in payload["groups"] for stem in group.get("stems", []))
    for garble in ("结节病分期：；IC；I", "皮肤发钳", "黄痘", "I川"):
        assert garble not in all_text, f"known OCR garble remains: {garble}"

    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group.get("stems", [])) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
