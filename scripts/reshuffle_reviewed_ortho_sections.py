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
PINNED_ORDERS = {
    # Clinical manifestations are deliberately spaced at A/D/G/J; the other
    # dimensions are interleaved so paired facts do not sit next to each other.
    "nonpurulent-arthritis-g01": ["J", "I", "C", "F", "G", "L", "A", "B", "D", "K", "E", "H"],
    # Keep display H as the shared "rest worse, activity better" feature. The
    # RA-specific morning-stiffness option remains separate at display C.
    "nonpurulent-arthritis-g02": ["F", "B", "M", "L", "D", "I", "K", "E", "G", "C", "H", "A", "J"],
}
PINNED_VERSIONS = {
    "nonpurulent-arthritis-g01": 4,
    "nonpurulent-arthritis-g02": 5,
}


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


def reorder_group_by_source(group: dict, source_order: list[str], version: int) -> None:
    options = group["options"]
    display_to_source = {option["key"]: option["sourceKey"] for option in options}
    source_answers = [
        {display_to_source[key] for key in stem["answer"]}
        for stem in group["stems"]
    ]
    source_to_option = {option["sourceKey"]: option for option in options}
    assert set(source_order) == set(source_to_option)

    display_keys = [option["key"] for option in options]
    reordered = [source_to_option[source_key] for source_key in source_order]
    for display_key, option in zip(display_keys, reordered):
        option["key"] = display_key
    group["options"] = reordered

    source_to_display = {option["sourceKey"]: option["key"] for option in reordered}
    for stem, answers in zip(group["stems"], source_answers):
        stem["answer"] = [
            source_to_display[option["sourceKey"]]
            for option in reordered
            if option["sourceKey"] in answers
        ]
    group["optionShuffleVersion"] = version


def deduplicate_bone_tumor_options(group: dict) -> None:
    """Merge exact duplicate labels while preserving all source-answer links."""
    options = group["options"]
    display_to_source = {option["key"]: option["sourceKey"] for option in options}
    source_answers = [
        {display_to_source[key] for key in stem["answer"]}
        for stem in group["stems"]
    ]

    kept_by_label: dict[str, dict] = {}
    source_aliases: dict[str, str] = {}
    deduplicated = []
    for option in options:
        keeper = kept_by_label.get(option["label"])
        if keeper is None:
            kept_by_label[option["label"]] = option
            option["sourceAliases"] = [option["sourceKey"]]
            deduplicated.append(option)
        else:
            keeper["sourceAliases"].append(option["sourceKey"])
            source_aliases[option["sourceKey"]] = keeper["sourceKey"]

    display_keys = [option["key"] for option in options[: len(deduplicated)]]
    for display_key, option in zip(display_keys, deduplicated):
        option["key"] = display_key
    group["options"] = deduplicated

    source_to_display = {option["sourceKey"]: option["key"] for option in deduplicated}
    for stem, answers in zip(group["stems"], source_answers):
        normalized = {source_aliases.get(source, source) for source in answers}
        stem["answer"] = [
            source_to_display[option["sourceKey"]]
            for option in deduplicated
            if option["sourceKey"] in normalized
        ]

    # Keep alias metadata only where a merge actually occurred.
    for option in deduplicated:
        if len(option["sourceAliases"]) == 1:
            option.pop("sourceAliases")


def merge_bone_tumor_location_variants(group: dict) -> None:
    """Merge the same adolescent-metaphysis fact with/without examples."""
    options = group["options"]
    keeper = next((option for option in options if option["sourceKey"] == "㉓"), None)
    duplicate = next((option for option in options if option["sourceKey"] == "Y"), None)
    if keeper is None or duplicate is None:
        return

    display_to_source = {option["key"]: option["sourceKey"] for option in options}
    source_answers = [
        {display_to_source[key] for key in stem["answer"]}
        for stem in group["stems"]
    ]
    keeper["label"] = "青少年多见，好发于长骨干骺端（股骨下端、胫骨上端等）"
    keeper.setdefault("sourceAliases", [keeper["sourceKey"]]).append("Y")
    merged = [option for option in options if option["sourceKey"] != "Y"]
    display_keys = [option["key"] for option in options[: len(merged)]]
    for display_key, option in zip(display_keys, merged):
        option["key"] = display_key
    group["options"] = merged

    source_to_display = {option["sourceKey"]: option["key"] for option in merged}
    for stem, answers in zip(group["stems"], source_answers):
        normalized = {"㉓" if source == "Y" else source for source in answers}
        stem["answer"] = [
            source_to_display[option["sourceKey"]]
            for option in merged
            if option["sourceKey"] in normalized
        ]


def main() -> None:
    for path in DATA_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for group in payload["groups"]:
            if group["id"] in PINNED_ORDERS and group.get("optionShuffleVersion") != PINNED_VERSIONS[group["id"]]:
                reorder_group_by_source(group, PINNED_ORDERS[group["id"]], PINNED_VERSIONS[group["id"]])
            elif group.get("options") and group.get("optionShuffleVersion", 0) < VERSION:
                reshuffle_group(group)

        if path.name == "surgery-nonpurulent-arthritis-data.json":
            group2 = next(group for group in payload["groups"] if group["id"] == "nonpurulent-arthritis-g02")
            morning_stiffness = next(option for option in group2["options"] if option["sourceKey"] == "M")
            morning_stiffness["label"] = "晨僵明显而持久"
            shared_activity_feature = next(option for option in group2["options"] if option["sourceKey"] == "E")
            option_order = {option["key"]: index for index, option in enumerate(group2["options"])}
            for stem_name in ("强直性脊柱炎", "类风湿关节炎"):
                stem = next(stem for stem in group2["stems"] if stem["text"] == stem_name)
                if shared_activity_feature["key"] not in stem["answer"]:
                    stem["answer"].append(shared_activity_feature["key"])
                stem["answer"].sort(key=option_order.__getitem__)

        if path.name == "surgery-bone-tumor-data.json":
            group = next(group for group in payload["groups"] if group["id"] == "bone-tumor-g02")
            biopsy = next(option for option in group["options"] if option["sourceKey"] == "C")
            biopsy["label"] = "活检"
            biopsy["sourceText"] = "C. 活检"
            group3 = next(group for group in payload["groups"] if group["id"] == "bone-tumor-g03")
            labels = [option["label"] for option in group3["options"]]
            if len(labels) != len(set(labels)):
                deduplicate_bone_tumor_options(group3)
            merge_bone_tumor_location_variants(group3)

        path.write_text(dump_payload(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
