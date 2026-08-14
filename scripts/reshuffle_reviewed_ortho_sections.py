#!/usr/bin/env python3
"""Deterministically reshuffle the three reviewed orthopaedic question banks."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = (
    ROOT / "src/data/surgery-nonpurulent-arthritis-data.json",
    ROOT / "src/data/surgery-bone-tumor-data.json",
    ROOT / "src/data/surgery-trunk-spine-data.json",
)
VERSION = 3


def dump_payload(payload: dict) -> str:
    """Keep these curated banks in their established compact, reviewable layout."""
    lines = ["{", '  "meta": {']
    meta_items = list(payload["meta"].items())
    for index, (key, value) in enumerate(meta_items):
        comma = "," if index < len(meta_items) - 1 else ""
        lines.append(f"    {json.dumps(key, ensure_ascii=False)}: {json.dumps(value, ensure_ascii=False)}{comma}")
    lines.extend(['  },', '  "groups": ['])
    for group_index, group in enumerate(payload["groups"]):
        lines.append("    {")
        items = list(group.items())
        for index, (key, value) in enumerate(items):
            comma = "," if index < len(items) - 1 else ""
            encoded_key = json.dumps(key, ensure_ascii=False)
            if key in {"options", "stems"} and value:
                lines.append(f"      {encoded_key}: [")
                for item_index, item in enumerate(value):
                    item_comma = "," if item_index < len(value) - 1 else ""
                    lines.append(f"        {json.dumps(item, ensure_ascii=False)}{item_comma}")
                lines.append(f"      ]{comma}")
            else:
                lines.append(f"      {encoded_key}: {json.dumps(value, ensure_ascii=False)}{comma}")
        group_comma = "," if group_index < len(payload["groups"]) - 1 else ""
        lines.append(f"    }}{group_comma}")
    lines.extend(["  ]", "}"])
    return "\n".join(lines) + "\n"


def shuffled(options: list[dict], seed_name: str) -> list[dict]:
    """Return a stable shuffle with at most one option left in its old position."""
    if len(options) < 2:
        return options[:]
    seed = int.from_bytes(hashlib.sha256(seed_name.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    for _ in range(1_000):
        candidate = options[:]
        rng.shuffle(candidate)
        fixed = sum(a["sourceKey"] == b["sourceKey"] for a, b in zip(options, candidate))
        if candidate != options and fixed <= 1:
            return candidate
    raise RuntimeError(f"Could not produce a suitably mixed order for {seed_name}")


def reshuffle_group(group: dict) -> None:
    options = group["options"]
    if not options:
        return

    # Preserve the deliberately categorized layout of bone-tumor group 3, but
    # randomize the choices inside each category.
    if all("category" in option for option in options):
        categories = list(dict.fromkeys(option["category"] for option in options))
        reordered = []
        for category in categories:
            block = [option for option in options if option["category"] == category]
            reordered.extend(shuffled(block, f"v{VERSION}:{group['id']}:{category}"))
    else:
        reordered = shuffled(options, f"v{VERSION}:{group['id']}")

    answer_sources = [
        {next(option["sourceKey"] for option in options if option["key"] == key) for key in stem["answer"]}
        for stem in group["stems"]
    ]
    display_keys = [option["key"] for option in options]
    for key, option in zip(display_keys, reordered):
        option["key"] = key
    group["options"] = reordered

    source_to_display = {option["sourceKey"]: option["key"] for option in reordered}
    for stem, source_answers in zip(group["stems"], answer_sources):
        stem["answer"] = [
            source_to_display[option["sourceKey"]]
            for option in reordered
            if option["sourceKey"] in source_answers
        ]
    group["optionShuffleVersion"] = VERSION


def main() -> None:
    for path in DATA_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for group in payload["groups"]:
            if group.get("options") and group.get("optionShuffleVersion") != VERSION:
                reshuffle_group(group)

        if path.name == "surgery-bone-tumor-data.json":
            group = next(group for group in payload["groups"] if group["id"] == "bone-tumor-g02")
            biopsy = next(option for option in group["options"] if option["sourceKey"] == "C")
            biopsy["label"] = "活检"
            biopsy["sourceText"] = "C. 活检"

        path.write_text(dump_payload(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
