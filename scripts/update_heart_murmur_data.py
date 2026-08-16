"""Synchronize only the lecture-53 heart-murmur review groups into med-data.json."""

import json
from pathlib import Path

from manual_med_review import reviewed_groups


DATA = Path("src/data/med-data.json")
TARGET_ID = "p83-g5"
OLD_SPLIT_IDS = {f"p83-g{i}" for i in range(6, 12)}


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    source_groups = {group["id"]: group for group in reviewed_groups(payload) if group["id"] == TARGET_ID}
    if set(source_groups) != {TARGET_ID}:
        raise SystemExit(f"target group mismatch: {sorted(source_groups)}")

    existing = next((group for group in payload["groups"] if group.get("id") == TARGET_ID), None)
    if existing is None:
        raise SystemExit(f"missing existing group: {TARGET_ID}")
    merged = dict(existing)
    for key in ("title", "kind", "kindLabel", "options", "stems", "sourceText", "reviewState", "topic", "lectureIds"):
        if key in source_groups[TARGET_ID]:
            merged[key] = source_groups[TARGET_ID][key]

    payload["groups"] = [group for group in payload["groups"] if group.get("id") not in OLD_SPLIT_IDS and group.get("id") != TARGET_ID]
    insert_at = next((index for index, group in enumerate(payload["groups"]) if group.get("id") == "p83-g4"), len(payload["groups"])) + 1
    payload["groups"].insert(insert_at, merged)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("merged p83-g5 through p83-g11 into p83-g5")


if __name__ == "__main__":
    main()
