"""Synchronize only the lecture-53 heart-murmur review groups into med-data.json."""

import json
from pathlib import Path

from manual_med_review import reviewed_groups


DATA = Path("src/data/med-data.json")
TARGET_IDS = {f"p83-g{i}" for i in range(5, 12)}


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    source_groups = {group["id"]: group for group in reviewed_groups(payload) if group["id"] in TARGET_IDS}
    if source_groups.keys() != TARGET_IDS:
        raise SystemExit(f"target group mismatch: {sorted(source_groups)}")

    changed = []
    for index, current in enumerate(payload["groups"]):
        group_id = current.get("id")
        if group_id not in TARGET_IDS:
            continue
        merged = dict(current)
        for key in ("title", "kind", "kindLabel", "options", "stems", "sourceText", "reviewState", "topic", "lectureIds"):
            if key in source_groups[group_id]:
                merged[key] = source_groups[group_id][key]
        payload["groups"][index] = merged
        changed.append(group_id)

    if set(changed) != TARGET_IDS:
        raise SystemExit(f"data group mismatch: {sorted(changed)}")
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("updated", ", ".join(sorted(changed)))


if __name__ == "__main__":
    main()
