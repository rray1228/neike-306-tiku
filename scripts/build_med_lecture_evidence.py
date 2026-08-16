#!/usr/bin/env python3
"""Attach the most relevant lecture page to every internal-medicine group.

The source PDFs stay outside the web app. This script extracts their page text,
matches each question group against the already assigned lecture(s), renders
only the selected pages, and writes the resulting evidence metadata into
med-data.json.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from pypdf import PdfReader


PUNCTUATION = re.compile(r"[\s\u3000，。；、：:（）()【】\[\]《》<>“”‘’'\"！？!?…·—–_\-/,.;]+")
ASCII_TOKEN = re.compile(r"[a-z0-9]+")
IGNORED_TOKENS = {
    "表现", "诊断", "治疗", "主要", "常见", "相关", "包括", "以下", "错误", "正确",
    "首选", "可有", "不正确", "不包括", "的是", "属于", "疾病", "患者", "题", "组",
}

TOPIC_RANGES = {
    "呼吸": (1, 13),
    "消化": (14, 23),
    "肾脏": (24, 27),
    "血液": (28, 35),
    "内分泌": (36, 42),
    "风湿": (43, 47),
    "中毒": (48, 48),
    "循环": (49, 57),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return PUNCTUATION.sub("", value)


def chinese_grams(value: str, size: int = 2) -> set[str]:
    value = normalize(value)
    return {value[i : i + size] for i in range(len(value) - size + 1)}


def ascii_tokens(value: str) -> set[str]:
    return {token for token in ASCII_TOKEN.findall(normalize(value)) if token not in IGNORED_TOKENS}


def item_score(item: str, page: str) -> float:
    query = normalize(item)
    target = normalize(page)
    if len(query) < 2 or len(target) < 2:
        return 0.0

    score = 0.0
    if len(query) >= 4 and query in target:
        score += 36.0 + min(len(query), 24) * 0.5

    query_grams = chinese_grams(query)
    if query_grams:
        score += 18.0 * len(query_grams & chinese_grams(target)) / len(query_grams)

    query_tokens = ascii_tokens(query)
    if query_tokens:
        target_tokens = ascii_tokens(target)
        score += 12.0 * len(query_tokens & target_tokens) / len(query_tokens)
    return score


def group_score(group: dict, page: str) -> float:
    stems = [stem.get("text", "") for stem in group.get("stems", [])]
    options = [option.get("label", "") for option in group.get("options", [])]
    stem_scores = sorted((item_score(item, page) for item in stems), reverse=True)
    option_scores = sorted((item_score(item, page) for item in options), reverse=True)
    # The strongest stems identify the page; options help when OCR shortened a stem.
    return sum(stem_scores[:4]) + sum(option_scores[:5]) * 0.22


def read_pages(lecture_dir: Path, lecture: dict) -> list[str]:
    pdf_path = lecture_dir / lecture["file"]
    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


def inferred_lecture_ids(group: dict) -> list[str]:
    stem_text = " ".join(stem.get("text", "") for stem in group.get("stems", []))
    if group.get("topic") == "消化" and (group.get("page") == 28 or any(word in stem_text for word in ("美沙拉嗪", "奥沙拉嗪", "柳氮磺吡啶", "UC"))):
        return ["lecture-18"]
    if group.get("topic") == "血液" and any(word in stem_text for word in ("结节硬化型", "霍奇金", "混合细胞型")):
        return ["lecture-35"]
    return []


def candidate_lecture_ids(group: dict, lecture_by_id: dict[str, dict]) -> list[str]:
    """Prefer the topic's lecture range over polluted historical assignments."""
    existing = [str(item) for item in group.get("lectureIds", []) if str(item) in lecture_by_id]
    inferred = inferred_lecture_ids(group) if not existing else []
    if inferred:
        return [lecture_id for lecture_id in inferred if lecture_id in lecture_by_id]
    topic_range = TOPIC_RANGES.get(group.get("topic"))
    if topic_range:
        start, end = topic_range
        return [f"lecture-{number:02d}" for number in range(start, end + 1) if f"lecture-{number:02d}" in lecture_by_id]
    return existing or list(lecture_by_id)


def render_page(pdf_path: Path, output_path: Path, page_number: int, pdftoppm: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = output_path.with_suffix("")
    subprocess.run(
        [pdftoppm, "-r", "120", "-png", "-f", str(page_number), "-l", str(page_number), "-singlefile", str(pdf_path), str(prefix)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("src/data/med-data.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("public/med/lecture-pages"))
    parser.add_argument(
        "--pdftoppm",
        default="/Users/ray/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftoppm",
    )
    args = parser.parse_args()

    content = json.loads(args.data.read_text(encoding="utf-8"))
    lecture_by_id = {lecture["id"]: lecture for lecture in content.get("lectures", [])}
    page_text_by_id: dict[str, list[str]] = {}
    page_choice_by_id: dict[str, int] = {}
    rendered: set[tuple[str, int]] = set()
    unmatched = []

    for group in content.get("groups", []):
        if group.get("id") == "p01-g1" or not any(normalize(stem.get("text", "")) for stem in group.get("stems", [])):
            group.pop("lectureEvidence", None)
            continue
        lecture_ids = candidate_lecture_ids(group, lecture_by_id)
        inferred = inferred_lecture_ids(group)
        if inferred and not group.get("lectureIds"):
            group["lectureIds"] = inferred
        candidates = [(lecture_id, lecture_by_id[lecture_id]) for lecture_id in lecture_ids]
        if not candidates:
            group.pop("lectureEvidence", None)
            if group.get("stems"):
                unmatched.append(group["id"])
            continue

        ranked: list[tuple[float, str, int]] = []
        for lecture_id, lecture in candidates:
            if lecture_id not in page_text_by_id:
                page_text_by_id[lecture_id] = read_pages(args.lecture_dir, lecture)
            for index, page_text in enumerate(page_text_by_id[lecture_id], start=1):
                ranked.append((group_score(group, page_text), lecture_id, index))

        ranked.sort(reverse=True)
        score, lecture_id, page_number = ranked[0]
        # A few source groups carry a wrong system label or contain a
        # cross-system comparison. Retry against all lectures when the
        # topic-range match is weak.
        if score < 50 and len(candidates) < len(lecture_by_id):
            ranked = []
            for fallback_id, lecture in lecture_by_id.items():
                if fallback_id not in page_text_by_id:
                    page_text_by_id[fallback_id] = read_pages(args.lecture_dir, lecture)
                for index, page_text in enumerate(page_text_by_id[fallback_id], start=1):
                    ranked.append((group_score(group, page_text), fallback_id, index))
            ranked.sort(reverse=True)
            score, lecture_id, page_number = ranked[0]
        if score < 4:
            lecture_id, page_number = candidates[0][0], 1
        lecture = lecture_by_id[lecture_id]
        image_name = f"med/lecture-pages/{lecture_id}-page-{page_number:02d}.webp"
        group["lectureEvidence"] = {
            "lectureId": lecture_id,
            "page": page_number,
            "image": image_name,
            "title": f"第{lecture['number']}讲第{page_number}页：{lecture['title']}",
            "description": f"本题组对应第{lecture['number']}讲第{page_number}页讲义。",
        }
        page_choice_by_id[lecture_id] = page_choice_by_id.get(lecture_id, 0) + 1
        rendered.add((lecture_id, page_number))
        print(f"{group['id']}\t{lecture_id}\tpage={page_number}\tscore={score:.1f}")

    for lecture_id, page_number in sorted(rendered):
        lecture = lecture_by_id[lecture_id]
        output_path = args.output_dir / f"{lecture_id}-page-{page_number:02d}.webp"
        if not output_path.exists():
            render_page(args.lecture_dir / lecture["file"], output_path, page_number, args.pdftoppm)

    args.data.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EVIDENCE_GROUPS={len(rendered)} unique pages for {sum(1 for group in content['groups'] if group.get('lectureEvidence'))} groups")
    if unmatched:
        print("UNMATCHED_GROUPS=" + ",".join(unmatched))


if __name__ == "__main__":
    main()
