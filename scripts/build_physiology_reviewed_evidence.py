#!/usr/bin/env python3
"""Compile the checked physiology stem/option locations; never infer pages at runtime."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["physiology-data", "physiology-teacher-supplement", "physiology-stage-exam-data", "physiology-endocrine-summary-data"]


def main():
    review = json.loads((ROOT / "physiology/lecture-evidence-review.json").read_text())
    datasets = [json.loads((ROOT / f"src/data/{name}.json").read_text()) for name in SOURCES]
    source_groups = {g["id"]: g for data in datasets for g in data["groups"]}
    assert set(review["groups"]) == set(source_groups)
    # The full collection inserts mind-map/divider pages between split lectures.
    starts = [2,14,27,46,61,83,88,99,111,123,130,138,153,169,174,186,200,207,213,217,230,240,245,257,267,275,297,314,326,337,345,356,365,384,392,398,403,406,412,418,426]
    lectures = datasets[0]["lectures"]
    page_locations = {}
    for lecture, start in zip(lectures, starts, strict=True):
        for local in range(1, lecture["pageCount"] + 1):
            page_locations[start + local - 1] = (lecture, local)
    page_id = lambda n: f"physiology-collection-{n:03}"
    pages = {}
    groups = {}
    empty_notices = {
        "phys-teacher-17-09": "合集未单独展开精液前列腺素的作用；已附其余选项涉及的激素作用原页。",
        "phys-teacher-17-10": "合集未单独展开本题所问的妊娠母体生理变化，请对照课后巩固原题。",
    }
    for gid, location in review["groups"].items():
        group = source_groups[gid]
        assert len(location["stemPages"]) == len(group["stems"]), gid
        assert set(location["optionPages"]) == {o["key"] for o in group["options"]}, gid
        all_numbers = list(dict.fromkeys(n for seq in location["stemPages"] + list(location["optionPages"].values()) for n in seq))
        for number in all_numbers:
            lecture, local = page_locations[number]
            pages[page_id(number)] = {
                "sourceSubject": "physiology", "sourceFile": review["sourceFile"],
                "page": number, "collectionPage": number, "chapterPage": local,
                "lectureId": lecture["id"], "lectureNumber": lecture["number"],
                "pageLabel": f"合集PDF第{number}页 · 第{lecture['number']}讲第{local}页",
                "title": f"{lecture['title']} · 合集第{number}页",
                "image": f"physiology/lecture-pages/collection-{review['sourceSha256'][:8]}-page-{number:03}.webp",
            }
        record = {
            "pages": [page_id(n) for n in all_numbers],
            "stemPages": [[page_id(n) for n in seq] for seq in location["stemPages"]],
            "optionPages": {key: [page_id(n) for n in seq] for key, seq in location["optionPages"].items()},
            "pageQuestions": {
                page_id(n): [s["number"] for s, seq in zip(group["stems"], location["stemPages"], strict=True) if n in seq]
                for n in all_numbers
            },
        }
        if gid in empty_notices:
            record["notice"] = empty_notices[gid]
        groups[gid] = record
    result = {
        "sourceFile": review["sourceFile"], "sourceSha256": review["sourceSha256"],
        "sourcePageCount": review["sourcePageCount"], "reviewDate": review["reviewDate"],
        "scope": ["生理基础题", "教师课后巩固", "阶段考试", "内分泌小结"],
        "groupCount": len(groups), "stemCount": sum(len(g["stems"]) for g in source_groups.values()),
        "renderDpi": 180, "webpQuality": 85,
        "pages": dict(sorted(pages.items())), "groups": groups,
    }
    (ROOT / "src/data/physiology-reviewed-lecture-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print({"groups": len(groups), "stems": result["stemCount"], "pages": len(pages)})


if __name__ == "__main__":
    main()
