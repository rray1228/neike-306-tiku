#!/usr/bin/env python3
"""Build the surgery question payload from the scanned workbook.

The surgery workbook is split into compact horizontal question bands. Each band
usually contains a shared option bank on the left and one or more blue prompts
with answer bubbles on the right. OCR is treated as an extraction aid: answers
that cannot be reconciled with the visible option keys are kept as unresolved
instead of being guessed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image

import build_med_content as shared


RIGHT_X = 420
PAGE_WIDTH = 767

TOPICS = [
    "颈部疾病",
    "乳房疾病",
    "胸部疾病",
    "胃十二指肠疾病",
    "腹部损伤与感染",
    "小肠与阑尾疾病",
    "结直肠与肛管疾病",
    "腹外疝",
    "肝胆胰疾病",
    "周围血管疾病",
    "泌尿外科",
]

PAGE_TOPIC = {
    1: "颈部疾病", 2: "颈部疾病",
    3: "乳房疾病", 4: "乳房疾病", 5: "乳房疾病",
    6: "胸部疾病", 7: "胃十二指肠疾病",
    8: "腹部损伤与感染", 9: "小肠与阑尾疾病",
    10: "小肠与阑尾疾病", 11: "小肠与阑尾疾病",
    12: "结直肠与肛管疾病", 13: "结直肠与肛管疾病",
    14: "腹外疝", 15: "腹外疝", 16: "腹外疝",
    17: "肝胆胰疾病", 18: "肝胆胰疾病", 19: "肝胆胰疾病",
    20: "肝胆胰疾病", 21: "肝胆胰疾病", 22: "肝胆胰疾病",
    23: "肝胆胰疾病", 24: "周围血管疾病",
    25: "周围血管疾病", 26: "泌尿外科", 27: "泌尿外科",
    28: "泌尿外科", 29: "泌尿外科",
}

# Page 3 starts with the final thyroid group before moving into breast disease.
SEGMENT_TOPIC_OVERRIDES = {(3, 1): "颈部疾病"}

LECTURE_IDS = {
    "颈部疾病": ["lecture-01"],
    "乳房疾病": ["lecture-03"],
    "胸部疾病": ["lecture-02", "lecture-04"],
    "胃十二指肠疾病": ["lecture-05"],
    "腹部损伤与感染": ["lecture-06", "lecture-07"],
    "小肠与阑尾疾病": ["lecture-08", "lecture-09"],
    "结直肠与肛管疾病": ["lecture-10", "lecture-11"],
    "腹外疝": ["lecture-12"],
    "肝胆胰疾病": ["lecture-13", "lecture-14", "lecture-15", "lecture-16"],
    "周围血管疾病": ["lecture-17"],
    "泌尿外科": ["lecture-18", "lecture-19"],
}

OPTION_ALIASES = {
    "A": "Aa人信从",
    "B": "Bb日昌",
    "C": "Cc",
    "D": "Dd口",
    "E": "Ee上",
    "F": "Ff",
    "G": "Gg",
    "H": "Hh",
    "I": "Ii1l|",
    "J": "Jj4了小",
    "K": "Kk",
    "L": "Ll[",
    "M": "Mm",
    "N": "Nn",
    "O": "Oo0",
    "P": "Pp",
    "Q": "Qq",
    "R": "Rr",
    "S": "Ss",
    "T": "Tt",
    "U": "Uu",
    "V": "Vv",
    "W": "Ww",
    "X": "Xx",
    "Y": "Yy",
    "Z": "Zz",
}

NOISE = ("小红书", "385106504", "beautiful things", "Daily Reminder", "It's time")


def clean_text(text: str) -> str:
    text = text.replace("ttsx", "").replace("天天师兄", "")
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"(?<=[A-Z])\s+(?=[A-Z])", "", text)
    text = re.sub(r"\s+", " ", text).strip(" |")
    return text


def load_ocr(path: Path) -> dict[int, list[dict]]:
    pages = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        scale = PAGE_WIDTH / float(data.get("width") or PAGE_WIDTH)
        rows = []
        for row in data.get("rows", []):
            box = row.get("box") or []
            if not box:
                continue
            text = clean_text(row.get("text", ""))
            if not text or any(item in text for item in NOISE):
                continue
            rows.append({
                "text": text,
                "x": float(box[0][0]) * scale,
                "y": float(box[0][1]) * scale,
                "score": float(row.get("score", 0)),
            })
        pages[int(data["page"])] = sorted(rows, key=lambda row: (row["y"], row["x"]))
    return pages


def divider_rows(image_path: Path) -> list[int]:
    image = Image.open(image_path).convert("L")
    width, height = image.size
    dark_rows = []
    pixels = image.load()
    for y in range(height):
        count = sum(1 for x in range(5, width - 5) if pixels[x, y] < 80)
        if count > width * 0.65:
            dark_rows.append(y)
    runs: list[list[int]] = []
    for y in dark_rows:
        if not runs or y > runs[-1][-1] + 1:
            runs.append([y])
        else:
            runs[-1].append(y)
    return [round(sum(run) / len(run)) for run in runs]


def strip_option_prefix(text: str, key: str) -> str | None:
    value = text.strip()
    if not value:
        return None
    aliases = OPTION_ALIASES[key]
    if value[0] not in aliases:
        if key == "H" and value.startswith("HH"):
            pass
        elif key == "J" and value.startswith(("JJ", "JT")):
            pass
        elif key == "E" and value.startswith("EE"):
            pass
        else:
            return None
    value = value[1:]
    if value and value[0] == key:
        value = value[1:]
    return value.lstrip(" .。．、,，:：;；-|_")


def parse_options(rows: list[dict]) -> tuple[list[dict], list[str]]:
    options = []
    issues = []
    start_index = next(
        (index for index, row in enumerate(rows)
         if strip_option_prefix(row["text"], "A") is not None),
        None,
    )
    if start_index is None:
        return [], ["未稳定提取到共用选项"]

    expected = "A"
    for row in rows[start_index:]:
        label = strip_option_prefix(row["text"], expected)
        if label is None:
            # Once A is found, the source uses one compact option per line.
            # Highlighted or narrow glyphs are frequently dropped by OCR, so
            # preserve the row and infer its sequential key instead of losing
            # the option from the answer bank.
            label = row["text"].lstrip(" .。．、,，:：;；-|_")
        options.append({
            "key": expected,
            "label": label or "原题文字待核对",
            "sourceText": row["text"],
            "sourceY": row["y"],
            "ocrScore": round(row["score"], 3),
        })
        if expected == "Z":
            break
        expected = chr(ord(expected) + 1)

    if len(options) < 2:
        issues.append("未稳定提取到共用选项")
    if any(item["label"] == "原题文字待核对" for item in options):
        issues.append("存在空选项文本")
    return options, issues


def answer_candidate(text: str) -> tuple[str, list[str]]:
    value = clean_text(text)
    openings = [value.rfind(char) for char in "（([【<《〈"]
    start = max(openings)
    if start >= 0:
        raw = value[start + 1:]
        raw = re.split(r"[）)\]】>》〉]", raw, maxsplit=1)[0]
        code = re.sub(r"[^A-Za-z0-9]", "", raw).upper().replace("1", "I").replace("0", "O")
        if 1 <= len(code) <= 24:
            return value[:start].rstrip(" :：,，"), list(dict.fromkeys(code))

    match = re.search(r"([A-Z1](?:[\s,/+_-]*[A-Z0-9]){0,23})\W*$", value.upper())
    if not match:
        return value, []
    code = re.sub(r"[^A-Z0-9]", "", match.group(1)).replace("1", "I").replace("0", "O")
    prefix = value[:match.start()].rstrip(" :：,，([{<《〈")
    if not prefix or len(code) > 24:
        return value, []
    return prefix, list(dict.fromkeys(code))


def parse_stems(rows: list[dict], option_keys: set[str]) -> tuple[list[dict], list[str]]:
    stems = []
    pending = []
    issues = []
    for row in rows:
        prompt, raw_answer = answer_candidate(row["text"])
        if not raw_answer:
            pending.append(row["text"])
            continue
        text_parts = [part for part in pending if part]
        if prompt and prompt not in text_parts:
            text_parts.append(prompt)
        text = clean_text("；".join(text_parts)).strip("； ")
        pending = []
        repaired_suffix = []
        while raw_answer and raw_answer[-1] not in option_keys:
            repaired_suffix.insert(0, raw_answer.pop())
        invalid = [key for key in raw_answer if key not in option_keys]
        answer = [key for key in raw_answer if key in option_keys]
        stem = {
            "text": text or "请结合原题页完成本小题",
            "answer": answer,
            "answerMode": "多选" if len(answer) > 1 else "单选",
            "sourceText": row["text"],
            "sourceY": row["y"],
            "ocrScore": round(row["score"], 3),
        }
        if repaired_suffix and answer:
            stem["answerRepair"] = (
                "已移除 OCR 在答案泡末尾误识别的字符：" + "".join(repaired_suffix)
            )
        if invalid or not answer:
            stem["answerState"] = "待原题页核对"
            stem["answerMode"] = "待核对"
            stem["rawAnswer"] = "".join(raw_answer)
            if invalid:
                stem["unresolvedLetters"] = invalid
                issues.append(f"答案含选项池外字母：{''.join(invalid)}")
            else:
                issues.append("未提取到有效答案")
        stems.append(stem)

    if pending:
        text = clean_text("；".join(pending)).strip("； ")
        if text:
            stems.append({
                "text": text[:500],
                "answer": [],
                "answerMode": "待核对",
                "answerState": "待原题页核对",
                "sourceText": text,
                "sourceY": rows[-1]["y"] if rows else None,
            })
            issues.append("末尾题干未识别到答案")
    if not stems:
        issues.append("未提取到题干")
    return stems, issues


def title_for(stems: list[dict], options: list[dict], page: int, group_number: int) -> str:
    candidates = [stem["text"] for stem in stems if stem.get("text")]
    if not candidates:
        candidates = [item["label"] for item in options if item.get("label")]
    title = candidates[0] if candidates else f"第 {page} 页第 {group_number} 题组"
    title = re.sub(r"^[一二三四五六七八九十0-9]+[.、．]\s*", "", title)
    return title if len(title) <= 42 else title[:42] + "…"


def segment_groups(page: int, rows: list[dict], image_path: Path) -> list[dict]:
    dividers = divider_rows(image_path)
    bounds = [0] + dividers + [1084]
    groups = []
    for index, (start, end) in enumerate(zip(bounds, bounds[1:]), 1):
        segment_rows = [row for row in rows if start + 3 <= row["y"] < end - 3]
        left_rows = [row for row in segment_rows if row["x"] < RIGHT_X]
        right_rows = [row for row in segment_rows if row["x"] >= RIGHT_X]
        options, option_issues = parse_options(left_rows)
        option_keys = {item["key"] for item in options}
        stems, stem_issues = parse_stems(right_rows, option_keys)

        # Source-only tables still stay visible and searchable.
        if not stems and segment_rows:
            source = clean_text(" | ".join(row["text"] for row in segment_rows))
            stems = [{
                "text": source[:500] or "请结合原题页完成本题组",
                "answer": [],
                "answerMode": "待核对",
                "answerState": "待原题页核对",
                "sourceText": source,
                "sourceY": start,
            }]

        if not options and not stems:
            continue
        topic = SEGMENT_TOPIC_OVERRIDES.get((page, index), PAGE_TOPIC[page])
        unresolved = any(stem.get("answerState") for stem in stems)
        low_score = any(stem.get("ocrScore", 1) < 0.45 for stem in stems)
        issues = list(dict.fromkeys(option_issues + stem_issues))
        if low_score:
            issues.append("题干 OCR 置信度偏低")
        kind = "B" if len(options) >= 2 and len(stems) >= 2 else "matching"
        if not options:
            kind = "source"
        elif len(stems) == 1 and len(stems[0].get("answer", [])) > 1:
            kind = "multi"
        kind_label = {
            "B": "B型题",
            "matching": "匹配 / 归类",
            "source": "原题页核对",
            "multi": "多项选择",
        }[kind]
        source_text = clean_text(" | ".join(row["text"] for row in segment_rows))[:5000]
        groups.append({
            "id": f"p{page:02d}-g{index}",
            "page": page,
            "title": title_for(stems, options, page, index),
            "kind": kind,
            "kindLabel": kind_label,
            "options": [{k: v for k, v in item.items() if k != "sourceY"} for item in options],
            "stems": stems,
            "sourceText": source_text,
            "reviewState": "待原题页核对" if unresolved or issues else "已完成结构校对",
            "reviewIssues": issues,
            "topic": topic,
            "lectureIds": LECTURE_IDS[topic],
        })
    return groups


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    pages = load_ocr(args.ocr)
    lectures = shared.build_lectures(args.lecture_dir)
    page_records = []
    groups = []
    for page in sorted(pages):
        rows = pages[page]
        page_records.append({
            "page": page,
            "image": f"surgery/source-pages/page-{page:02d}.png",
            "topic": PAGE_TOPIC[page],
            "searchText": clean_text(" ".join(row["text"] for row in rows))[:7000],
        })
        groups.extend(segment_groups(page, rows, args.image_dir / f"page-{page:02d}.png"))

    payload = {
        "meta": {
            "title": "外科学题库",
            "sourcePdf": "外科各论除骨科(去胶带版).pdf",
            "sourcePages": len(page_records),
            "sourcePdfPages": len(pages),
            "lectureCount": len(lectures),
            "generatedBy": "scripts/build_surgery_content.py",
            "siteIntegrated": True,
            "answerNote": "按原题页横向题组提取；答案与选项池不一致或识别不清的题干不自动判分，保留原题页供继续校对。",
        },
        "topics": ["全部", *TOPICS, "综合"],
        "pages": page_records,
        "groups": groups,
        "lectures": lectures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pages": len(page_records),
        "lectures": len(lectures),
        "groups": len(groups),
        "stems": sum(len(group["stems"]) for group in groups),
        "unresolvedStems": sum(
            1 for group in groups for stem in group["stems"] if stem.get("answerState")
        ),
        "types": dict(Counter(group["kind"] for group in groups)),
        "topics": dict(Counter(group["topic"] for group in groups)),
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
