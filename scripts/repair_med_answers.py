#!/usr/bin/env python3
"""Repair answer bubbles that were truncated by OCR/parser ambiguity.

The source workbook often writes a multi-answer bubble immediately after a
Chinese prompt, for example “（ACF” or “（BDEIK”. The first parser accepted
only the first letter inside such an unfinished bracket. This pass uses the
known shared-option alphabet to recover those bubbles while leaving already
multi-letter answers untouched unless a source-specific correction is known.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MANUAL = {
    # COPD treatment notes contain classification letters before the actual
    # treatment choices. Keep the treatment bubble shown after the note.
    "p02-g1:9": list("FHLNQ"),
    "p02-g1:10": list("HL"),
    "p02-g1:11": list("HLPM"),
    # Lecture correction: atrial premature beats are B/F/I/K/L; D belongs to
    # junctional premature beats and is an annotation artifact in the scan.
    "p94-g1:0": list("BFIKL"),
}


def upper_runs(text: str) -> list[str]:
    return re.findall(r"[A-Z]{1,24}", text.upper())


def code_from_tail(text: str, keys: set[str]) -> list[str]:
    letters = []
    for run in upper_runs(text):
        if len(run) == 1 and run not in keys:
            continue
        filtered = [letter for letter in run if letter in keys]
        # Never turn an acronym such as COPD into an answer when it contains
        # letters outside the option alphabet.
        if filtered and all(letter in keys for letter in run):
            letters.extend(filtered)
    return list(dict.fromkeys(letters))


def recover(group: dict, stem: dict) -> list[str]:
    keys = {item["key"].upper() for item in group.get("options", [])}
    if not keys:
        return stem.get("answer", [])
    raw = stem.get("sourceText", "")

    # If there is an annotation/parenthetical block followed by answer text,
    # prefer the final answer text. This handles “(A+E/B) F/H/L/N/Q” and
    # “(MAO=O)BF” without treating the explanatory block as the key.
    closing = max(raw.rfind(")"), raw.rfind("）"), raw.rfind("]"), raw.rfind("】"))
    if closing >= 0:
        code = code_from_tail(raw[closing + 1 :], keys)
        if len(code) > 1:
            return code

    # An unfinished bubble at the end of a scanned line is common.
    bracket_codes = []
    for match in re.finditer(r"[（(【\[]\s*([A-Z](?:\s*[A-Z]){1,23})(?=$|[）)】\]])", raw.upper()):
        candidate = "".join(match.group(1).split())
        if candidate and all(letter in keys for letter in candidate):
            bracket_codes.append(list(dict.fromkeys(candidate)))
    if bracket_codes:
        code = bracket_codes[-1]
        if len(code) > 1:
            return code

    # Direct bubbles such as “仅失代偿期才可有BDEGH”. Only use this fallback
    # for a currently single-letter answer so existing parsed keys are stable.
    current = stem.get("answer", [])
    if len(current) <= 1:
        direct = re.search(r"([A-Z]{2,24})\s*$", raw.upper())
        if direct and all(letter in keys for letter in direct.group(1)):
            return list(dict.fromkeys(direct.group(1)))
    return current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    changed = 0
    for group in payload["groups"]:
        for index, stem in enumerate(group["stems"]):
            key = f"{group['id']}:{index}"
            answer = MANUAL.get(key, recover(group, stem))
            if answer != stem.get("answer", []):
                stem["answer"] = answer
                changed += 1
            stem["answerMode"] = "多选" if len(answer) > 1 else "单选"

    payload.setdefault("answerRepair", {})["changedStems"] = changed
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"repaired {changed} stems")


if __name__ == "__main__":
    main()
