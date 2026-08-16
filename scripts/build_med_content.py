#!/usr/bin/env python3
"""Build the internal-medicine study payload from the local scanned question bank.

The PDF is a scanned workbook. RapidOCR produces line-level text with coordinates;
this script keeps the source page image for every group so the learner can always
verify the exact original wording. Groups with a shared option list become B-type
groups by default; single-stem or table-like groups remain a source-backed review
block instead of being forced into a single-choice shape.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pdfplumber


PAGE_WIDTH = 1124
RIGHT_X = 560

TOPIC_RULES = [
    ("呼吸", ["COPD", "肺动脉高压", "肺栓塞", "肺炎", "肺结核", "支气管", "ARDS", "呼吸衰竭", "肺癌", "胸膜", "肺脓肿", "间质性肺", "肺气肿"]),
    ("消化", ["胃食管", "胃炎", "消化性溃疡", "肠结核", "结核性腹膜", "炎症性肠病", "肠易激", "肝性脑病", "肝硬化", "肝癌", "胰腺炎", "腹水", "消化道"]),
    ("肾脏", ["泌尿", "尿路感染", "肾衰竭", "肾小球", "蛋白尿", "血尿", "CKD", "肾炎"]),
    ("循环", ["高血压", "冠心病", "心衰", "心律失常", "心包", "心瓣膜", "感染性心内膜", "心肌", "心脏骤停", "肺源性心脏", "房早", "室早", "房性早搏", "室性早搏", "房颤", "房扑", "室速", "室上速", "心动过速", "房室阻滞", "预激综合征"]),
    ("血液", ["贫血", "白血病", "MDS", "淋巴瘤", "骨髓瘤", "出血性", "骨髓", "溶血"]),
    ("内分泌", ["甲状腺", "Graves", "甲减", "糖尿病", "原醛", "库欣", "嗜铬", "内分泌", "胰岛素"]),
    ("风湿", ["SLE", "类风湿", "干燥", "血管炎", "风湿"]),
    ("中毒", ["中毒", "一氧化碳", "有机磷", "酒精"]),
]

ANSWER_RE = re.compile(r"([A-Za-z0-9]{1,24})\s*[)）】]?\s*$")
LETTER_OPTION_RE = re.compile(r"^([A-Z]|[a-z]|[0-9]{1,2}|[①②③④⑤⑥⑦⑧⑨⑩])[.。．、]\s*(.+)$")
COMPACT_OPTION_RE = re.compile(r"^([A-Z])(?:\s+|(?=[\u4e00-\u9fff]))(.+)$")

ANSWER_OVERRIDES = {
    "p94-g1:0": list("BFIKL"),
}


def clean_text(text: str) -> str:
    text = text.strip().replace("个", "↑") if "血压个" in text else text.strip()
    text = text.replace("ttsx", "").replace("天天师兄", "")
    text = text.replace("川级", "III级").replace("Ⅱ级", "II级").replace("Ⅰ级", "I级")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" |")


def topic_for(text: str) -> str:
    text = text.lower()
    for topic, keys in TOPIC_RULES:
        if any(key.lower() in text for key in keys):
            return topic
    return "综合"


def parse_answer(text: str):
    """Return (prompt, answer_letters) for a blue right-column answer row.

    The answer in the workbook may be glued to Chinese text, wrapped in brackets,
    or written in lower-case. We only accept a trailing run of letters and keep the
    original line in sourceText for review.
    """
    raw = clean_text(text)
    if re.fullmatch(r"[A-Za-z]", raw):
        return "", ["I" if raw.upper() == "1" else raw.upper()]

    # Parenthesized answer bubbles are common in the scan, including forms such
    # as “治疗（bd）” and “症状少（E/B）”.
    bracket = re.search(r"[（(\[【]\s*([A-Za-z](?:\s*[/+、,，&]\s*[A-Za-z])*)", raw)
    if bracket:
        code = re.sub(r"[^A-Za-z]", "", bracket.group(1)).upper()
        prefix = raw[:bracket.start()].rstrip(" =：:，,;；")
        if prefix and code:
            return prefix, ["I" if ch == "1" else ch for ch in code]

    # Slash/plus separated keys, e.g. “I/K/M/O” or “F/H/L/N/Q”.
    separated = re.search(r"([A-Za-z0-9](?:\s*[/+、,，&]\s*[A-Za-z0-9]){1,})\s*$", raw)
    if separated:
        code = re.sub(r"[^A-Za-z0-9]", "", separated.group(1)).upper()
        prefix = raw[:separated.start()].rstrip(" =：:，,;；")
        if code:
            code = code.replace("1", "I")
            return prefix, list(code)

    # Remove common OCR/annotation wrappers around the answer bubble. The OCR
    # can insert spaces into “ACD” (e.g. “AC D”), so fold an uppercase run from
    # the prefix into the detected suffix before returning the key.
    m = ANSWER_RE.search(raw)
    if not m:
        return raw, []
    code = m.group(1)
    prefix = raw[:m.start()].rstrip(" (（[【=：:，,;；")
    if not prefix:
        return raw, []
    trailing = re.search(r"([A-Z](?:\s*[A-Z]){0,23})\s*$", prefix)
    if trailing and trailing.start() > 0:
        code = trailing.group(1) + code
        prefix = prefix[:trailing.start()].rstrip(" (（[【=：:，,;；")

    # Avoid treating ordinary abbreviations as answer keys when a right-column
    # line is just a topic heading (COPD, ARDS, HAP, etc.).
    if prefix.endswith(("肺炎", "COPD", "ARDS", "HAP", "CT", "MRI", "MRPA", "DSA", "ICS", "SABA", "LABA", "LAMA", "NSCLC")):
        return raw, []
    answer = ["I" if ch == "1" else ch.upper() for ch in code if ch.isalpha() or ch == "1"]
    if "".join(answer) in {"ICS", "SABA", "LABA", "LAMA", "COPD", "ARDS", "HAP", "CT", "MRI", "MRPA", "DSA", "NSCLC", "FEV"}:
        return raw, []
    # Do not let long English words become a 20-choice answer code.
    if len(answer) > 20:
        return raw, []
    return prefix, answer


def recover_answer_code(text: str, current: list[str], option_keys: set[str]) -> list[str]:
    """Recover multi-letter answer bubbles that begin inside an OCR bracket."""
    if not option_keys:
        return current

    def runs(value: str) -> list[str]:
        return re.findall(r"[A-Z]{1,24}", value.upper())

    def filtered(value: str) -> list[str]:
        letters = []
        for run in runs(value):
            if run and all(letter in option_keys for letter in run):
                letters.extend(run)
        return list(dict.fromkeys(letters))

    closing = max(text.rfind(")"), text.rfind("）"), text.rfind("]"), text.rfind("】"))
    if closing >= 0:
        tail = filtered(text[closing + 1 :])
        if len(tail) > 1:
            return tail

    for match in re.finditer(r"[（(【\[]\s*([A-Z](?:\s*[A-Z]){1,23})(?=$|[）)】\]])", text.upper()):
        code = "".join(match.group(1).split())
        if len(code) > 1 and all(letter in option_keys for letter in code):
            return list(dict.fromkeys(code))

    if len(current) <= 1:
        direct = re.search(r"([A-Z]{2,24})\s*$", text.upper())
        if direct and all(letter in option_keys for letter in direct.group(1)):
            return list(dict.fromkeys(direct.group(1)))
    return current


def load_ocr(path: Path):
    pages = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        rows = []
        for row in data.get("rows", []):
            box = row.get("box") or []
            if not box:
                continue
            x = float(box[0][0])
            y = float(box[0][1])
            rows.append({"text": clean_text(row.get("text", "")), "x": x, "y": y, "box": box, "score": row.get("score", 0)})
        pages[data["page"]] = sorted(rows, key=lambda r: (r["y"], r["x"]))
    return pages


def option_line(row):
    match = LETTER_OPTION_RE.match(row["text"])
    if not match:
        compact = COMPACT_OPTION_RE.match(row["text"])
        if compact:
            key, label = compact.groups()
            return {"key": key.upper(), "label": clean_text(label), "sourceText": row["text"]}
    if not match:
        return None
    key, label = match.groups()
    # OCR sometimes turns the letter O/I into 0/1; preserve the source text but
    # normalize the display key where it is unambiguous.
    if key == "0":
        key = "O"
    if key == "1" and label and not label[0].isdigit():
        key = "I"
    return {"key": key.upper(), "label": clean_text(label), "sourceText": row["text"]}


def extract_groups(page_number: int, rows):
    right_rows = [r for r in rows if r["x"] >= RIGHT_X and r["y"] < 1480 and not "小红书" in r["text"]]
    starts = [r["y"] for r in right_rows if re.match(r"^问\s*[:：]?$", r["text"])]
    if not starts:
        # Some pages are continuation tables without a literal “问：”. Keep the
        # entire page as one source-backed block and classify it as flexible.
        starts = [0]
    starts = sorted(set(starts))
    segments = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else 1500
        left = [r for r in rows if r["x"] < RIGHT_X and (r["y"] >= start - 35) and r["y"] < end]
        right = [r for r in right_rows if r["y"] >= start and r["y"] < end]
        options = []
        for row in left:
            opt = option_line(row)
            if opt and not any(existing["key"] == opt["key"] for existing in options):
                options.append(opt)

        stems = []
        pending = []
        for row in right:
            text = row["text"]
            if not text or text.startswith("问"):
                continue
            prompt, answer = parse_answer(text)
            answer = recover_answer_code(text, answer, {item["key"] for item in options})
            if answer:
                parts = [p for p in pending if p and not p.startswith("问")]
                if prompt and prompt not in parts:
                    parts.append(prompt)
                stem = "；".join(parts).strip("； ")
                if stem:
                    stems.append({"text": stem, "answer": answer, "sourceText": text, "sourceY": row["y"]})
                pending = []
            else:
                # A heading line such as “肺炎链球菌肺炎” belongs to the next
                # answer row; preserve it in the stem instead of dropping it.
                pending.append(text)

        # If OCR did not detect a trailing answer, retain the right-side content
        # as a flexible review prompt so no source material disappears.
        if not stems and right:
            text = "；".join(r["text"] for r in right if not r["text"].startswith("问"))
            if text:
                stems = [{"text": text[:260], "answer": [], "sourceText": text, "sourceY": right[0]["y"]}]

        if options or stems:
            source_text = " | ".join(r["text"] for r in rows if start - 35 <= r["y"] < end)
            title = stems[0]["text"] if stems else (options[0]["label"] if options else f"第{page_number}页原题块")
            if len(title) > 42:
                title = title[:42] + "…"
            if len(options) >= 2 and len(stems) >= 2:
                kind = "B"
                kind_label = "B型题"
            elif len(options) >= 2 and len(stems) == 1 and len(stems[0]["answer"]) > 1:
                kind = "multi"
                kind_label = "多项选择"
            elif len(options) >= 2:
                kind = "matching"
                kind_label = "匹配 / 归类"
            else:
                kind = "source"
                kind_label = "原题页核对"
            group_id = f"p{page_number:02d}-g{len(segments)+1}"
            for stem_index, stem in enumerate(stems):
                override = ANSWER_OVERRIDES.get(f"{group_id}:{stem_index}")
                if override:
                    stem["answer"] = override
                stem["answerMode"] = "多选" if len(stem.get("answer", [])) > 1 else "单选"
            segments.append({
                "id": group_id,
                "page": page_number,
                "title": title,
                "kind": kind,
                "kindLabel": kind_label,
                "options": options,
                "stems": stems,
                "sourceText": source_text[:5000],
                "reviewState": "待讲义复核",
            })
    return segments


def build_lectures(lecture_dir: Path):
    lectures = []
    for path in sorted(lecture_dir.glob("*.pdf"), key=lambda p: p.name):
        match = re.match(r"(\d+)\s+27考研：(.+?)\s+核心", path.stem)
        number = int(match.group(1)) if match else len(lectures) + 1
        title = match.group(2).strip() if match else path.stem
        with pdfplumber.open(path) as doc:
            pages = [(page.extract_text() or "") for page in doc.pages]
        text = "\n".join(pages)
        clean = re.sub(r"\n{2,}", "\n", text).strip()
        lectures.append({
            "id": f"lecture-{number:02d}",
            "number": number,
            "title": title,
            "file": path.name,
            "pageCount": len(pages),
            "charCount": len(clean),
            "excerpt": clean[:900],
            "text": clean,
        })
    return lectures


def related_lectures(topic, lectures):
    keys = {"呼吸": ["COPD", "肺", "胸膜", "支气管", "ARDS", "呼吸"], "消化": ["胃", "肠", "肝", "胰", "溃疡", "反流"], "肾脏": ["肾", "尿", "泌尿"], "循环": ["心", "高血压", "冠心病"], "血液": ["贫血", "白血病", "MDS", "淋巴瘤", "骨髓"], "内分泌": ["甲状腺", "糖尿病", "肾上腺", "内分泌"], "风湿": ["风湿", "SLE", "类风湿", "干燥", "血管炎"], "中毒": ["中毒"]}.get(topic, [])
    ids = []
    for lecture in lectures:
        if any(key.lower() in lecture["title"].lower() for key in keys):
            ids.append(lecture["id"])
    return ids[:6]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    pages = load_ocr(args.ocr)
    lectures = build_lectures(args.lecture_dir)
    page_records = []
    groups = []
    for page_number in sorted(pages):
        rows = pages[page_number]
        text = " ".join(row["text"] for row in rows)
        # Page 20 is the transition page: both blocks are GERD questions.
        # A respiratory keyword in the last option bank (e.g. asthma or
        # interstitial lung disease) must not misclassify the whole page.
        topic = "消化" if page_number == 20 else topic_for(text)
        page_records.append({
            "page": page_number,
            "image": "",
            "topic": topic,
            "searchText": clean_text(text)[:7000],
        })
        for group in extract_groups(page_number, rows):
            group["topic"] = topic
            group["lectureIds"] = related_lectures(topic, lectures)
            groups.append(group)

    data = {
        "meta": {
            "title": "内科题库",
            "sourcePdf": "西综-学成选择题(内科汇总去胶带版).pdf",
            "sourcePages": len(page_records),
            "lectureCount": len(lectures),
            "generatedBy": "scripts/build_med_content.py",
            "answerNote": "source answers are preserved from the scanned workbook and should be checked against the linked lectures before relying on them.",
        },
        "topics": ["全部", "呼吸", "消化", "肾脏", "循环", "血液", "内分泌", "风湿", "中毒", "综合"],
        "pages": page_records,
        "groups": groups,
        "lectures": lectures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pages": len(page_records),
        "lectures": len(lectures),
        "groups": len(groups),
        "stems": sum(len(group["stems"]) for group in groups),
        "types": dict(Counter(group["kind"] for group in groups)),
        "topics": dict(Counter(page["topic"] for page in page_records)),
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
