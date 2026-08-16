#!/usr/bin/env python3
"""Deterministically shuffle every fracture-overview option pool."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/data/surgery-fracture-data.json"
VERSION = 2


def stable_shuffle(options: list[dict], group_id: str) -> list[dict]:
    if len(options) < 2:
        return options[:]
    seed = int.from_bytes(hashlib.sha256(f"fracture-v{VERSION}:{group_id}".encode()).digest()[:8], "big")
    rng = random.Random(seed)
    for _ in range(1_000):
        candidate = options[:]
        rng.shuffle(candidate)
        fixed = sum(left["sourceKey"] == right["sourceKey"] for left, right in zip(options, candidate))
        if candidate != options and fixed <= 1:
            return candidate
    raise RuntimeError(f"Could not sufficiently shuffle {group_id}")


def reshuffle_group(group: dict) -> None:
    options = group["options"]
    if not options:
        return
    for option in options:
        option.setdefault("sourceKey", option["key"])
    original_order = group.setdefault("optionOriginalOrder", [option["sourceKey"] for option in options])
    source_to_option = {option["sourceKey"]: option for option in options}
    assert len(source_to_option) == len(options)
    base_options = [source_to_option[source_key] for source_key in original_order]

    display_to_source = {option["key"]: option["sourceKey"] for option in options}
    semantic_answers = [
        {display_to_source[key] for key in stem["answer"]}
        for stem in group["stems"]
    ]
    reordered = stable_shuffle(base_options, group["id"])
    display_keys = list(original_order)
    for display_key, option in zip(display_keys, reordered):
        option["key"] = display_key
    group["options"] = reordered

    for stem, answers in zip(group["stems"], semantic_answers):
        stem["answer"] = [
            option["key"] for option in reordered if option["sourceKey"] in answers
        ]
    group["optionShuffleVersion"] = VERSION


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    for group in payload["groups"]:
        reshuffle_group(group)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
