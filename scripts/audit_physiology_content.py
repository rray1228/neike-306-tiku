#!/usr/bin/env python3
"""Validate the reconciled physiology payload and source-page assets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


EXPECTED_CORRECTIONS = {
    "phys-002", "phys-006", "phys-024", "phys-049", "phys-070", "phys-085", "phys-087", "phys-089",
    "phys-090", "phys-093", "phys-100", "phys-110", "phys-111", "phys-112", "phys-118", "phys-136",
    "phys-149", "phys-153", "phys-154",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/physiology-data.json").read_text(encoding="utf-8"))
    reconciliation = json.loads((root / "physiology/lecture-reconciliation.json").read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["lectureLinked"] is True
    assert payload["meta"]["sourcePages"] == 126
    assert payload["meta"]["lectureCount"] == 41
    assert payload["meta"]["fullSemanticAuditDate"] == "2026-08-13"
    assert payload["meta"]["fullSemanticAuditScope"] == "160 个题组、505 个题干、41 份 2027 考研生理讲义"
    assert payload["meta"]["lectureEvidencePageCount"] == 136
    assert re.fullmatch(r"[0-9a-f]{64}", payload["meta"]["lectureSetFingerprint"])
    assert len(payload["groups"]) == 160
    assert sum(len(group["stems"]) for group in payload["groups"]) == 505

    group_ids = [group["id"] for group in payload["groups"]]
    assert len(group_ids) == len(set(group_ids)), "duplicate group ids"

    corrected_ids = {record["id"] for record in reconciliation["corrections"]}
    assert corrected_ids == EXPECTED_CORRECTIONS, (corrected_ids, EXPECTED_CORRECTIONS)
    assert reconciliation["statusSummary"] == {"与今年讲义一致": 141, "已校正": 19}

    platelet_group = next(group for group in payload["groups"] if group["id"] == "phys-024")
    assert platelet_group["stems"][3]["answer"] == list("ACDE")
    assert platelet_group["stems"][3]["answerRaw"] == "ACDE"
    assert platelet_group["lectureEvidence"]["lectureNumber"] == 7
    assert platelet_group["lectureEvidence"]["page"] == 4

    adh_group = next(group for group in payload["groups"] if group["id"] == "phys-100")
    assert adh_group["options"][2]["label"] == "血管紧张素Ⅱ（AngⅡ）"
    assert adh_group["stems"][0]["answer"] == list("ABCHI")
    assert adh_group["stems"][1]["answer"] == list("DEFG")
    assert adh_group["lectureEvidence"]["page"] == 9

    medulla_group = next(group for group in payload["groups"] if group["id"] == "phys-110")
    assert medulla_group["stems"][0]["text"] == "影响髓质间液高渗维持（多选）"
    assert medulla_group["stems"][0]["answer"] == list("CD")
    assert medulla_group["stems"][1]["answer"] == list("E")
    assert medulla_group["stems"][2]["answer"] == list("AB")
    assert medulla_group["lectureEvidence"]["page"] == 14

    calcium_group = next(group for group in payload["groups"] if group["id"] == "phys-049")
    assert calcium_group["stems"][1]["answer"] == list("BD")
    assert calcium_group["lectureEvidence"]["page"] == 4

    hormone_group = next(group for group in payload["groups"] if group["id"] == "phys-149")
    assert hormone_group["stems"][2]["answer"] == list("ADEGJL")
    assert hormone_group["lectureEvidence"]["page"] == 4

    glucagon_group = next(group for group in payload["groups"] if group["id"] == "phys-153")
    assert glucagon_group["stems"][0]["answer"] == list("ACFG")
    assert glucagon_group["stems"][1]["answer"] == list("BDEH")
    assert glucagon_group["stems"][1]["answerRaw"] == "BDEH"
    assert glucagon_group["lectureEvidence"]["lectureNumber"] == 38
    assert glucagon_group["lectureEvidence"]["page"] == 5

    growth_group = next(group for group in payload["groups"] if group["id"] == "phys-154")
    assert growth_group["stems"][0]["answer"] == list("BCEGHJK")
    assert growth_group["lectureEvidence"]["page"] == 1

    missing_images = []
    duplicate_option_keys = []
    invalid_answers = []
    empty_answers = []
    answer_raw_mismatches = []
    missing_lectures = []
    missing_lecture_images = []
    lecture_ids = {lecture["id"] for lecture in payload["lectures"]}
    assert all(re.fullmatch(r"[0-9a-f]{64}", lecture.get("sourceSha256", "")) for lecture in payload["lectures"])
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        option_keys = [option["key"] for option in group["options"]]
        if len(option_keys) != len(set(option_keys)):
            duplicate_option_keys.append(group["id"])
        for stem_index, stem in enumerate(group["stems"]):
            if not stem.get("answer"):
                empty_answers.append(f"{group['id']}:{stem_index}")
            absent = [key for key in stem.get("answer", []) if key not in option_keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{stem_index}={absent}")
            if stem.get("answerMode") != "排序" and stem.get("answerRaw") != "".join(stem.get("answer", [])):
                answer_raw_mismatches.append(f"{group['id']}:{stem_index}")
        if not group.get("lectureIds") or any(item not in lecture_ids for item in group["lectureIds"]):
            missing_lectures.append(group["id"])
        evidence = group.get("lectureEvidence", {})
        assert evidence.get("lectureId") in lecture_ids, f"missing evidence for {group['id']}"
        assert evidence.get("page", 0) > 0, f"missing lecture page for {group['id']}"
        assert evidence.get("title"), f"missing evidence title for {group['id']}"
        assert evidence.get("description"), f"missing evidence description for {group['id']}"
        lecture_image = root / "public" / evidence.get("image", "")
        if not lecture_image.exists():
            missing_lecture_images.append(str(lecture_image))

    assert not missing_images, f"missing source images: {missing_images[:5]}"
    assert not duplicate_option_keys, f"duplicate option keys: {duplicate_option_keys}"
    assert not invalid_answers, f"answers outside option bank: {invalid_answers}"
    assert not empty_answers, f"empty answers: {empty_answers}"
    assert not answer_raw_mismatches, f"answerRaw differs from answer: {answer_raw_mismatches}"
    assert not missing_lectures, f"missing lecture links: {missing_lectures}"
    assert not missing_lecture_images, f"missing lecture images: {missing_lecture_images[:5]}"

    print({
        "pages": len(payload["pages"]),
        "groups": len(payload["groups"]),
        "stems": sum(len(group["stems"]) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "corrections": len(corrected_ids),
        "reviewStates": dict(Counter(group["reviewState"] for group in payload["groups"])),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
