#!/usr/bin/env python3
"""Remove answer-revealing and redundant options from lectures 27 and 28."""

from __future__ import annotations

import json
import string
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "src/data" / name).read_text(encoding="utf-8"))


def save(name: str, payload: dict) -> None:
    path = ROOT / "src/data" / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def semantic_answers(group: dict) -> list[set[str]]:
    display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
    return [{display_to_source[key] for key in stem["answer"]} for stem in group["stems"]]


def rekey(group: dict, *, drop_sources: set[str] | None = None, version: int = 3) -> None:
    drop_sources = drop_sources or set()
    answers = semantic_answers(group)
    options = [option for option in group["options"] if option["sourceKey"] not in drop_sources]
    assert len(options) <= len(string.ascii_uppercase)
    for key, option in zip(string.ascii_uppercase, options):
        option["key"] = key
    group["options"] = options
    source_to_display = {option["sourceKey"]: option["key"] for option in options}
    for stem, sources in zip(group["stems"], answers):
        stem["answer"] = [option["key"] for option in options if option["sourceKey"] in sources]
    group["optionOriginalOrder"] = [
        source for source in group["optionOriginalOrder"] if source not in drop_sources
    ]
    group["sourceAnswer"] = [
        "".join(sorted(source for source in sources if source not in drop_sources)) for sources in answers
    ]
    group["sourceStemNumbers"] = [str(index) for index in range(1, len(group["stems"]) + 1)]
    group["optionShuffleVersion"] = version


def group(payload: dict, group_id: str) -> dict:
    return next(item for item in payload["groups"] if item["id"] == group_id)


def option_by_source(item: dict, source_key: str) -> dict:
    return next(option for option in item["options"] if option["sourceKey"] == source_key)


def curate_degenerative_spine() -> None:
    name = "surgery-degenerative-spine-data.json"
    payload = load(name)
    payload["meta"]["answerNote"] = (
        "保持Word原有9个题组；题干、选项及答案已按第27讲逐项校对。"
        "前8组共用选项池已固定打乱并同步重映射答案；影像学题组删除了提示答案的层级复述项，第9组保留为数字填空题。"
    )

    imaging = group(payload, "degenerative-spine-g01")
    # “包含X线所见内容”“包含CT所见内容”只提示层级关系，不检验具体知识。
    rekey(imaging, drop_sources={"A", "E"})
    for stem in imaging["stems"]:
        stem["reviewMethod"] = "已按第27讲第2页逐项校对；删除提示答案的层级复述项并同步重映射答案"

    save(name, payload)


def curate_limb_fractures() -> None:
    name = "surgery-limb-fracture-data.json"
    payload = load(name)
    payload["meta"]["answerNote"] = (
        "保持原题组结构并按第28讲逐项校对；删除重复总括项，合并三踝骨折重复题干，"
        "并改写直接复述题干条件的选项后同步重映射答案。第10组保留为数字填空题。"
    )

    forearm = group(payload, "limb-fracture-dislocation-g03")
    option_by_source(forearm, "K")["label"] = "先复位桡骨"
    option_by_source(forearm, "I")["label"] = "先复位尺骨"
    option_by_source(forearm, "J")["label"] = "需达到解剖复位"
    forearm["optionShuffleVersion"] = 3

    hip = group(payload, "limb-fracture-dislocation-g04")
    option_by_source(hip, "K")["label"] = "最常见的髋关节脱位类型"
    option_by_source(hip, "G")["label"] = "最凶险的髋关节脱位类型"
    option_by_source(hip, "A")["label"] = "大转子区压痛"
    option_by_source(hip, "F")["label"] = "跌倒等外伤或病理性骨折"
    intertrochanteric = next(stem for stem in hip["stems"] if stem["text"] == "股骨转子间骨折")
    hip_display_by_source = {option["sourceKey"]: option["key"] for option in hip["options"]}
    if hip_display_by_source["B"] not in intertrochanteric["answer"]:
        intertrochanteric["answer"].append(hip_display_by_source["B"])
    intertrochanteric["answer"].sort(key=lambda key: list(hip_display_by_source.values()).index(key))
    hip["sourceAnswer"][-1] = "ABEFN"
    hip["optionShuffleVersion"] = 3

    femoral_neck = group(payload, "limb-fracture-dislocation-g06")
    option_by_source(femoral_neck, "A")["label"] = "骨折线位于股骨头下方，预后最差"
    option_by_source(femoral_neck, "F")["label"] = "骨折线位于股骨颈中部"
    option_by_source(femoral_neck, "G")["label"] = "骨折线位于股骨颈基底部，预后最好"
    femoral_neck["optionShuffleVersion"] = 3

    treatment = group(payload, "limb-fracture-dislocation-g07")
    if len(treatment["stems"]) == 14:
        tri_malleolar = treatment["stems"][-2]
        posterior_malleolus = treatment["stems"][-1]
        tri_malleolar["text"] = "三踝骨折"
        tri_malleolar["sourceText"] = tri_malleolar["text"]
        tri_malleolar["answer"] = list(dict.fromkeys(tri_malleolar["answer"] + posterior_malleolus["answer"]))
        tri_malleolar["reviewMethod"] = "已按第28讲第12页逐项校对；后踝固定阈值由数字题单独考查，并删除重复总括选项"
        treatment["stems"].pop()
    else:
        assert treatment["stems"][-1]["text"] in {"三踝骨折", "三踝骨折（后踝累及胫骨1/4～1/3关节面）"}
        treatment["stems"][-1]["text"] = "三踝骨折"
        treatment["stems"][-1]["sourceText"] = "三踝骨折"
    # 内踝、外踝的固定方式已具体表达；后踝固定阈值由数字题单独考查。
    # 删除重复的“切开复位＋内固定”和在本题中直接暴露答案的“后踝内固定”。
    if any(option["sourceKey"] in {"D", "K"} for option in treatment["options"]):
        rekey(treatment, drop_sources={"D", "K"})
    else:
        treatment["optionShuffleVersion"] = 3
    option_by_source(treatment, "B")["label"] = "螺钉内固定"
    closed_reduction = next(
        stem for stem in treatment["stems"] if stem["text"] in {"股骨颈：闭合复位后", "股骨颈骨折：闭合复位后的固定方式"}
    )
    closed_reduction["text"] = "股骨颈骨折：闭合复位后的固定方式"
    closed_reduction["sourceText"] = closed_reduction["text"]

    complications = group(payload, "limb-fracture-dislocation-g08")
    clearer_labels = {
        "N": "下肢严重缺血坏死、骨筋膜室综合征",
        "I": "近折端向前、远折端向后",
        "E": "向外成角",
        "F": "螺旋形骨折常伴后踝骨折",
        "L": "远端血供减弱，易延迟愈合或不愈合",
        "B": "骨筋膜室综合征；远端血供减弱，易延迟愈合或不愈合",
        "C": "可损伤腘血管、胫神经、腓总神经，并发骨筋膜室综合征",
        "M": "粉碎性骨折",
        "H": "横形骨折",
    }
    for source_key, label in clearer_labels.items():
        option_by_source(complications, source_key)["label"] = label
    complications["optionShuffleVersion"] = 3

    save(name, payload)


def main() -> None:
    curate_degenerative_spine()
    curate_limb_fractures()


if __name__ == "__main__":
    main()
