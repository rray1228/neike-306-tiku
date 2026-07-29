#!/usr/bin/env python3
"""Audit the integrated surgery payload and source-page assets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


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
