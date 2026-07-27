#!/usr/bin/env python3
"""Fail-fast integrity checks for the internal-medicine question payload."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "src/data/med-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["lectures"]) == 57, "lecture count changed"
    assert payload["meta"]["sourcePages"] == 97, "source page count changed"

    invalid = []
    duplicate = []
    for group in payload["groups"]:
        keys = {option["key"] for option in group.get("options", [])}
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            if len(answer) != len(set(answer)):
                duplicate.append(f"{group['id']}:{index}")
            invalid_keys = [key for key in answer if key not in keys]
            if invalid_keys:
                invalid.append(f"{group['id']}:{index}={''.join(invalid_keys)}")

    assert not duplicate, f"duplicate answer keys: {duplicate}"
    assert not invalid, f"answer keys absent from option bank: {invalid}"

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
