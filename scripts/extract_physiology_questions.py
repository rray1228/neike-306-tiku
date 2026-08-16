#!/usr/bin/env python3
"""Extract the physiology workbook without integrating it into the study site.

The physiology source is a born-digital PDF whose layout differs from the
internal-medicine and pathology workbooks:

    numbered group -> shared A/B/C options -> numbered stems
    -> lecture-source image -> answer row

The lecture-source image is intentionally not OCR'd here.  The goal of this
pass is to preserve the authored question text and answer row, flag ambiguous
source content, and leave lecture linking/site integration for a later pass.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber


CHAPTER_RE = re.compile(r"^(第[一二三四五六七八九十]+章)\s*(.+)$")
GROUP_START_RE = re.compile(r"^(\d+)\s*[.．、]\s*A(?:\s*[.．、,，:：]|\s+)")
PROMPT_RE = re.compile(r"^(\d+)\s*(?:[.．、:：]|\s+(?=\S)|(?=[\u4e00-\u9fffA-Za-z]))\s*(.+)$")
EXPLICIT_OPTION_RE = re.compile(
    r"(?<![A-Za-z0-9/+\-])([A-Z])\s*[.．、,，:：]\s*"
)
IMPLICIT_OPTION_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Z])"
    r"(?=\s*(?:[\u4e00-\u9fff]|NaC[Il]\b))"
)
PAGE_NUMBER_RE = re.compile(r"^-?\s*\d+\s*-?$")
WATERMARK = "B站/公众号：小凯的医学之路"


def clean_line(text: str) -> str:
    text = text.replace(WATERMARK, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_noise(text: str) -> bool:
    value = clean_line(text)
    return not value or bool(PAGE_NUMBER_RE.fullmatch(value))


def chapter_parts(text: str) -> tuple[str, str] | None:
    match = CHAPTER_RE.match(clean_line(text))
    if not match:
        return None
    return match.group(1), match.group(2).strip()


def looks_like_group_start(text: str) -> bool:
    return bool(GROUP_START_RE.match(clean_line(text)))


def extract_raw_groups(source_pdf: Path) -> tuple[list[dict], list[dict]]:
    """Return raw question blocks and page-level searchable text."""
    groups: list[dict] = []
    page_records: list[dict] = []
    question_lines: list[dict] = []
    state = "question"
    current_chapter_number = ""
    current_chapter_title = ""
    awaiting_answer_index: int | None = None

    with pdfplumber.open(source_pdf) as document:
        for page_number, page in enumerate(document.pages, 1):
            page_text = page.extract_text() or ""
            page_records.append(
                {
                    "page": page_number,
                    "searchText": clean_line(page_text)[:7000],
                }
            )

            for raw_line in page_text.splitlines():
                line = clean_line(raw_line)
                if not line:
                    continue

                chapter = chapter_parts(line)
                if chapter:
                    current_chapter_number, current_chapter_title = chapter

                if "【讲义来源】" in line:
                    before_marker = clean_line(line.split("【讲义来源】", 1)[0])
                    if before_marker:
                        question_lines.append(
                            {"page": page_number, "text": before_marker}
                        )
                    groups.append(
                        {
                            "chapterNumber": current_chapter_number,
                            "chapterTitle": current_chapter_title,
                            "questionLines": question_lines,
                            "questionPage": (
                                question_lines[0]["page"]
                                if question_lines
                                else page_number
                            ),
                            "sourcePage": page_number,
                            "answerPage": None,
                            "answerRaw": None,
                        }
                    )
                    question_lines = []
                    state = "source"
                    awaiting_answer_index = None
                    continue

                if "【答案】" in line:
                    state = "answer"
                    awaiting_answer_index = len(groups) - 1
                    after_marker = clean_line(line.split("【答案】", 1)[1])
                    if after_marker and awaiting_answer_index >= 0:
                        groups[awaiting_answer_index]["answerRaw"] = after_marker
                        groups[awaiting_answer_index]["answerPage"] = page_number
                        state = "question"
                        awaiting_answer_index = None
                    continue

                if state == "answer":
                    if is_noise(line):
                        continue
                    if looks_like_group_start(line) or chapter:
                        # The source itself has one blank answer block on page
                        # 107.  Keep it blank and begin the next question.
                        state = "question"
                        awaiting_answer_index = None
                        question_lines.append({"page": page_number, "text": line})
                        continue
                    if awaiting_answer_index is not None:
                        groups[awaiting_answer_index]["answerRaw"] = line
                        groups[awaiting_answer_index]["answerPage"] = page_number
                    state = "question"
                    awaiting_answer_index = None
                    continue

                if state == "source":
                    continue

                if not is_noise(line):
                    question_lines.append({"page": page_number, "text": line})

    return groups, page_records


def option_markers(line: str, expected_key: str | None) -> list[tuple[int, int, str]]:
    """Find option markers while avoiding terms such as ACh, VIP and P substance."""
    explicit = [
        (match.start(), match.end(), match.group(1), "explicit")
        for match in EXPLICIT_OPTION_RE.finditer(line)
    ]
    occupied = {(start, key) for start, _, key, _ in explicit}
    implicit: list[tuple[int, int, str, str]] = []
    for match in IMPLICIT_OPTION_RE.finditer(line):
        key = match.group(1)
        if (match.start(), key) in occupied:
            continue
        implicit.append((match.start(), match.end(), key, "implicit"))

    candidates = sorted(explicit + implicit, key=lambda item: (item[0], item[1]))
    accepted: list[tuple[int, int, str]] = []
    next_key = expected_key
    for candidate_index, (start, end, key, kind) in enumerate(candidates):
        at_line_start = not line[:start].strip()
        if kind == "implicit":
            # If an explicit marker for the same key appears later on the same
            # line, this occurrence is part of the preceding label, e.g.
            # "A.来源胰岛 B 细胞    B.来源胰岛 A 细胞".
            if any(
                later_key == key and later_kind == "explicit"
                for _, _, later_key, later_kind in candidates[
                    candidate_index + 1 :
                ]
            ):
                continue
            if key != next_key:
                continue
        elif (
            next_key
            and key < next_key
            and not at_line_start
        ):
            # Vitamin lists such as "VitA、D、E、K" resemble explicit option
            # markers.  Ignore backward/repeated letters inside a label, while
            # allowing a genuine source-side skip such as E -> G.
            continue

        accepted.append((start, end, key))
        next_key = chr(ord(key) + 1) if key < "Z" else None

    return accepted


def parse_options(lines: list[str]) -> tuple[list[dict], list[str]]:
    options: list[dict] = []
    issues: list[str] = []
    current: dict | None = None
    expected_key: str | None = "A"

    for line in lines:
        markers = option_markers(line, expected_key)
        if not markers:
            if current:
                current["label"] = clean_line(current["label"] + " " + line)
                current["sourceText"] = clean_line(
                    current["sourceText"] + " " + line
                )
            elif line:
                issues.append(f"选项区存在无法归属的文本：{line}")
            continue

        prefix = clean_line(line[: markers[0][0]])
        if prefix:
            if current:
                current["label"] = clean_line(current["label"] + " " + prefix)
                current["sourceText"] = clean_line(
                    current["sourceText"] + " " + prefix
                )
            else:
                issues.append(f"首个选项前存在文本：{prefix}")

        for marker_index, (start, end, key) in enumerate(markers):
            if current:
                options.append(current)
            segment_end = (
                markers[marker_index + 1][0]
                if marker_index + 1 < len(markers)
                else len(line)
            )
            label = clean_line(line[end:segment_end])
            current = {
                "key": key,
                "label": label,
                "sourceText": clean_line(line[start:segment_end]),
            }
            expected_key = chr(ord(key) + 1) if key < "Z" else None

    if current:
        options.append(current)

    keys = [option["key"] for option in options]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        issues.append("原题选项字母重复：" + "、".join(duplicates))
    if keys and keys[0] == "A":
        highest = max(keys)
        expected_keys = {
            chr(code) for code in range(ord("A"), ord(highest) + 1)
        }
        missing = sorted(expected_keys - set(keys))
        if missing:
            issues.append("原题选项字母不连续，缺少：" + "、".join(missing))
    if options and options[0]["key"] != "A":
        issues.append(f"选项未从 A 开始：{options[0]['key']}")
    if any(not option["label"] for option in options):
        issues.append("存在空选项文本")
    return options, issues


def parse_stems(lines: list[str]) -> tuple[list[dict], list[str]]:
    stems: list[dict] = []
    issues: list[str] = []
    current: dict | None = None

    for line in lines:
        match = PROMPT_RE.match(line)
        if match:
            if current:
                stems.append(current)
            number = int(match.group(1))
            text = clean_line(match.group(2)).rstrip("：:")
            current = {
                "number": number,
                "text": text,
                "sourceText": line,
            }
        elif current:
            current["text"] = clean_line(current["text"] + " " + line).rstrip(
                "：:"
            )
            current["sourceText"] = clean_line(
                current["sourceText"] + " " + line
            )
        else:
            issues.append(f"小问区存在无法归属的文本：{line}")

    if current:
        stems.append(current)

    numbers = [stem["number"] for stem in stems]
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        issues.append("小问编号不连续：" + "、".join(map(str, numbers)))
    if not stems:
        issues.append("未提取到小问")
    return stems, issues


def split_answer_row(answer_raw: str | None, stem_count: int) -> list[str]:
    if not answer_raw:
        return []
    answer_raw = clean_line(answer_raw)
    if re.search(r"[、，,]", answer_raw):
        parts = [
            clean_line(part)
            for part in re.split(r"\s*[、，,]\s*", answer_raw)
            if clean_line(part)
        ]
    else:
        parts = [part for part in answer_raw.split() if part]

    if (
        stem_count > 1
        and all(re.fullmatch(r"[A-Z]+", part) for part in parts)
        and sum(len(part) for part in parts) == stem_count
    ):
        # PDF text extraction occasionally collapses visual spaces, e.g.
        # "C B A" becomes "C BA".  When every stem has a single-letter
        # answer and the total letter count matches, restore the visual split.
        parts = list("".join(parts))
    return parts


def answer_keys(answer: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[A-Z]", answer)))


def parse_group(raw_group: dict, index: int) -> dict:
    lines = [
        {"page": row["page"], "text": clean_line(row["text"])}
        for row in raw_group["questionLines"]
        if clean_line(row["text"])
    ]
    content_lines = []
    for row in lines:
        if row["text"] == "学成选择题（生理学）":
            continue
        if chapter_parts(row["text"]):
            continue
        content_lines.append(row["text"])

    issues: list[str] = []
    group_number: int | None = None
    if content_lines:
        match = re.match(r"^(\d+)\s*[.．、]\s*(.+)$", content_lines[0])
        if match:
            group_number = int(match.group(1))
            content_lines[0] = clean_line(match.group(2))
        else:
            issues.append("未识别题组编号")
    else:
        issues.append("题组正文为空")

    prompt_start = None
    for line_index, line in enumerate(content_lines):
        if PROMPT_RE.match(line):
            prompt_start = line_index
            break
    if prompt_start is None:
        option_lines = content_lines
        stem_lines: list[str] = []
    else:
        option_lines = content_lines[:prompt_start]
        stem_lines = content_lines[prompt_start:]

    options, option_issues = parse_options(option_lines)
    stems, stem_issues = parse_stems(stem_lines)
    issues.extend(option_issues)
    issues.extend(stem_issues)

    answer_parts = split_answer_row(raw_group["answerRaw"], len(stems))
    if not raw_group["answerRaw"]:
        issues.append("原题【答案】栏为空")
    elif len(answer_parts) != len(stems):
        issues.append(
            f"答案数量与小问数量不一致：{len(answer_parts)} / {len(stems)}"
        )

    option_key_set = {option["key"] for option in options}
    for stem_index, stem in enumerate(stems):
        answer_raw = (
            answer_parts[stem_index] if stem_index < len(answer_parts) else ""
        )
        keys = answer_keys(answer_raw)
        missing_keys = [key for key in keys if key not in option_key_set]
        if missing_keys:
            issues.append(
                f"第{stem['number']}小问答案引用缺失选项："
                + "、".join(missing_keys)
            )
        stem["answerRaw"] = answer_raw
        stem["answer"] = keys
        if "＞" in answer_raw or ">" in answer_raw or "-" in answer_raw:
            stem["answerMode"] = "排序"
        elif len(keys) > 1:
            stem["answerMode"] = "多选"
        elif len(keys) == 1:
            stem["answerMode"] = "单选"
        else:
            stem["answerMode"] = "待核对"

    chapter_number = raw_group["chapterNumber"]
    chapter_title = raw_group["chapterTitle"]
    identifier = f"phys-{index:03d}"
    title = stems[0]["text"] if stems else f"第{group_number or index}题组"
    if len(stems) > 1:
        title = title[:38].rstrip("；，、 ") + "等"

    source_pages = list(
        dict.fromkeys(
            page
            for page in (
                raw_group["questionPage"],
                raw_group["sourcePage"],
                raw_group["answerPage"],
            )
            if page is not None
        )
    )
    return {
        "id": identifier,
        "chapterNumber": chapter_number,
        "chapterTitle": chapter_title,
        "groupNumber": group_number,
        "title": title,
        "questionPage": raw_group["questionPage"],
        "sourcePage": raw_group["sourcePage"],
        "answerPage": raw_group["answerPage"],
        "sourcePages": source_pages,
        "options": options,
        "stems": stems,
        "answerRaw": raw_group["answerRaw"] or "",
        "sourceQuestionText": "\n".join(row["text"] for row in lines),
        "reviewState": "待人工复核" if issues else "已自动提取",
        "issues": list(dict.fromkeys(issues)),
    }


def progression_issues(groups: list[dict]) -> list[dict]:
    by_chapter: dict[str, list[dict]] = defaultdict(list)
    for group in groups:
        by_chapter[group["chapterNumber"]].append(group)

    findings: list[dict] = []
    for chapter_number, chapter_groups in by_chapter.items():
        actual = [group["groupNumber"] for group in chapter_groups]
        expected = list(range(1, len(chapter_groups) + 1))
        if actual != expected:
            findings.append(
                {
                    "chapterNumber": chapter_number,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return findings


def build_payload(source_pdf: Path) -> tuple[dict, dict]:
    raw_groups, pages = extract_raw_groups(source_pdf)
    groups = [
        parse_group(raw_group, index)
        for index, raw_group in enumerate(raw_groups, 1)
    ]
    chapters = []
    for group in groups:
        key = (group["chapterNumber"], group["chapterTitle"])
        if key not in [
            (chapter["number"], chapter["title"]) for chapter in chapters
        ]:
            chapters.append({"number": key[0], "title": key[1]})

    issue_counter = Counter(
        issue
        for group in groups
        for issue in group["issues"]
    )
    audit = {
        "sourcePdf": source_pdf.name,
        "pageCount": len(pages),
        "chapterCount": len(chapters),
        "groupCount": len(groups),
        "stemCount": sum(len(group["stems"]) for group in groups),
        "optionCount": sum(len(group["options"]) for group in groups),
        "answeredStemCount": sum(
            1
            for group in groups
            for stem in group["stems"]
            if stem["answerRaw"]
        ),
        "groupsNeedingReview": sum(
            bool(group["issues"]) for group in groups
        ),
        "issueCount": sum(issue_counter.values()),
        "issueSummary": dict(issue_counter),
        "groupProgressionIssues": progression_issues(groups),
        "reviewGroups": [
            {
                "id": group["id"],
                "chapter": (
                    f"{group['chapterNumber']} {group['chapterTitle']}"
                ),
                "groupNumber": group["groupNumber"],
                "page": group["questionPage"],
                "issues": group["issues"],
            }
            for group in groups
            if group["issues"]
        ],
    }

    payload = {
        "meta": {
            "title": "生理学学成选择题（独立提取稿）",
            "sourcePdf": source_pdf.name,
            "sourcePdfPages": len(pages),
            "chapterCount": len(chapters),
            "groupCount": len(groups),
            "stemCount": audit["stemCount"],
            "generatedBy": "scripts/extract_physiology_questions.py",
            "siteIntegrated": False,
            "lectureLinked": False,
            "answerNote": (
                "答案按原题【答案】栏原样拆分；排序题同时保留 answerRaw。"
                "本轮不关联讲义、不导入网站。"
            ),
        },
        "chapters": chapters,
        "pages": pages,
        "groups": groups,
    }
    return payload, audit


def markdown_for(payload: dict, audit: dict) -> str:
    lines = [
        "# 生理学学成选择题（独立提取稿）",
        "",
        f"- 源文件：{payload['meta']['sourcePdf']}",
        f"- PDF 页数：{payload['meta']['sourcePdfPages']}",
        f"- 章节：{payload['meta']['chapterCount']}",
        f"- 题组：{payload['meta']['groupCount']}",
        f"- 小问：{payload['meta']['stemCount']}",
        f"- 待人工复核题组：{audit['groupsNeedingReview']}",
        "- 状态：未关联讲义，未导入网站",
        "",
    ]

    current_chapter = None
    for group in payload["groups"]:
        chapter = (group["chapterNumber"], group["chapterTitle"])
        if chapter != current_chapter:
            current_chapter = chapter
            lines.extend(
                [
                    f"## {chapter[0]} {chapter[1]}",
                    "",
                ]
            )

        page_text = "、".join(map(str, group["sourcePages"]))
        lines.extend(
            [
                f"### {group['groupNumber']}. {group['title']}",
                "",
                f"原页：{page_text}",
                "",
                "选项：",
                "",
            ]
        )
        for option in group["options"]:
            lines.append(f"- {option['key']}. {option['label']}")
        lines.extend(["", "小问与原题答案：", ""])
        for stem in group["stems"]:
            answer = stem["answerRaw"] or "（原题未给答案）"
            lines.append(
                f"{stem['number']}. {stem['text']}  \n"
                f"   答案：{answer}"
            )
        if group["issues"]:
            lines.extend(
                [
                    "",
                    "复核提示：" + "；".join(group["issues"]),
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()

    payload, audit = build_payload(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.markdown.write_text(
        markdown_for(payload, audit),
        encoding="utf-8",
    )
    args.audit.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
