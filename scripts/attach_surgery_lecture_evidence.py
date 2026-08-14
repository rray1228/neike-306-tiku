#!/usr/bin/env python3
"""Attach and render a lecture page for every surgery question group.

Existing hand-reviewed evidence is preserved. Missing evidence is matched
against the text of the surgery lecture PDFs, rendered through Poppler, and
stored as real WebP files so the site never serves a PNG with a WebP suffix.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "src/data/surgery-data.json"
DEFAULT_OUTPUT = ROOT / "public/surgery/lecture-pages"
DEFAULT_PDFTOPPM = (
    "/Users/ray/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/native/poppler/poppler/bin/pdftoppm"
)
PUNCTUATION = re.compile(r"[\s\u3000，。；、：:（）()【】\[\]《》<>“”‘’'\"！？!?…·—–_\-/,.;]+")
ASCII_TOKEN = re.compile(r"[a-z0-9]+")
IGNORED_TOKENS = {
    "表现", "诊断", "治疗", "主要", "常见", "相关", "包括", "以下", "错误", "正确",
    "首选", "可有", "不正确", "不包括", "的是", "属于", "疾病", "患者", "题", "组",
}

# These workbook groups sit across a printed chapter boundary and therefore
# inherited the neighbouring topic's lecture assignment during OCR splitting.
LECTURE_OVERRIDES = {
    "p05-g4": ["lecture-04"],  # 肋骨骨折
    "p06-g1": ["lecture-04"],  # 纵隔肿瘤
    "p06-g2": ["lecture-05"],  # 胃癌 Borrmann 分型
    "p06-g3": ["lecture-05"],  # 胃癌检查
    "p06-g4": ["lecture-05"],  # 胃肿瘤讲义中的跨肿瘤靶向药小结
    "p07-g3": ["lecture-06"],  # 腹腔穿刺液鉴别
    "p07-g4": ["lecture-06"],  # 原发性腹膜炎感染途径
    "p18-g4": ["lecture-16"],  # 胰头癌与胆道肿瘤横向鉴别表
}


def normalize(value: str) -> str:
    return PUNCTUATION.sub("", unicodedata.normalize("NFKC", value or "").lower())


def chinese_grams(value: str, size: int = 2) -> set[str]:
    value = normalize(value)
    return {value[index : index + size] for index in range(len(value) - size + 1)}


def ascii_tokens(value: str) -> set[str]:
    return {
        token for token in ASCII_TOKEN.findall(normalize(value))
        if token not in IGNORED_TOKENS
    }


def item_score(item: str, page: str) -> float:
    query = normalize(item)
    target = normalize(page)
    if len(query) < 2 or len(target) < 2:
        return 0.0
    score = 0.0
    if len(query) >= 4 and query in target:
        score += 38.0 + min(len(query), 28) * 0.55
    grams = chinese_grams(query)
    if grams:
        score += 20.0 * len(grams & chinese_grams(target)) / len(grams)
    tokens = ascii_tokens(query)
    if tokens:
        score += 12.0 * len(tokens & ascii_tokens(target)) / len(tokens)
    return score


def group_score(group: dict, page_text: str) -> float:
    title_score = item_score(group.get("title", ""), page_text) * 1.25
    stem_scores = sorted(
        (item_score(stem.get("text", ""), page_text) for stem in group.get("stems", [])),
        reverse=True,
    )
    option_scores = sorted(
        (item_score(option.get("label", ""), page_text) for option in group.get("options", [])),
        reverse=True,
    )
    return title_score + sum(stem_scores[:5]) + sum(option_scores[:8]) * 0.22


def read_lecture_pages(lecture_dir: Path, lectures: list[dict]) -> dict[str, list[str]]:
    pages: dict[str, list[str]] = {}
    for lecture in lectures:
        pdf_path = lecture_dir / lecture["file"]
        if not pdf_path.exists():
            raise FileNotFoundError(f"missing lecture PDF: {pdf_path}")
        reader = PdfReader(str(pdf_path))
        pages[lecture["id"]] = [page.extract_text() or "" for page in reader.pages]
    return pages


def choose_page(group: dict, pages: dict[str, list[str]]) -> tuple[float, str, int]:
    assigned = set(LECTURE_OVERRIDES.get(group["id"], group.get("lectureIds", [])))
    candidates = assigned or set(pages)
    ranked: list[tuple[float, str, int]] = []
    for lecture_id, lecture_pages in pages.items():
        if lecture_id not in candidates:
            continue
        for page_number, page_text in enumerate(lecture_pages, start=1):
            score = group_score(group, page_text)
            ranked.append((score, lecture_id, page_number))
    if not ranked:
        raise ValueError(f"no lecture candidates for {group['id']}")
    return max(ranked)


def render_webp(
    pdf_path: Path,
    output_path: Path,
    page_number: int,
    *,
    pdftoppm: str,
    dpi: int,
    quality: int,
    max_width: int,
    temp_dir: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    prefix = temp_dir / output_path.stem
    png_path = prefix.with_suffix(".png")
    subprocess.run(
        [
            pdftoppm,
            "-f", str(page_number),
            "-l", str(page_number),
            "-singlefile",
            "-png",
            "-r", str(dpi),
            str(pdf_path),
            str(prefix),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    with Image.open(png_path) as opened:
        image = opened.convert("RGB")
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        image.save(output_path, "WEBP", quality=quality, method=6, exact=True)
    png_path.unlink()


def attach_evidence(
    content: dict,
    lecture_dir: Path,
    output_dir: Path,
    *,
    pdftoppm: str,
    dpi: int,
    quality: int,
    max_width: int,
    dry_run: bool,
) -> tuple[int, set[tuple[str, int]], list[tuple[str, float]]]:
    lecture_by_id = {lecture["id"]: lecture for lecture in content.get("lectures", [])}
    pages = read_lecture_pages(lecture_dir, list(lecture_by_id.values()))
    selected: set[tuple[str, int]] = set()
    uncertain: list[tuple[str, float]] = []
    attached = 0

    for group in content.get("groups", []):
        evidence = group.get("lectureEvidence")
        if evidence and evidence.get("image"):
            continue
        score, lecture_id, page_number = choose_page(group, pages)
        lecture = lecture_by_id[lecture_id]
        group["lectureIds"] = [lecture_id]
        group["lectureEvidence"] = {
            "lectureId": lecture_id,
            "page": page_number,
            "image": f"surgery/lecture-pages/{lecture_id}-page-{page_number:02d}.webp",
            "title": f"第{lecture['number']}讲第{page_number}页：{lecture['title']}",
            "description": "本题组已对应至相关讲义原页；点击可查看并核对。",
            "method": "按题干和选项匹配讲义页，并保留原页供人工复核。",
        }
        attached += 1
        selected.add((lecture_id, page_number))
        if score < 35:
            uncertain.append((group["id"], score))
        print(f"{group['id']}\t{lecture_id}\tpage={page_number}\tscore={score:.1f}")

    if not dry_run:
        temp_dir = ROOT / "tmp/pdfs/surgery-lecture-pages"
        for lecture_id, page_number in sorted(selected):
            output_path = output_dir / f"{lecture_id}-page-{page_number:02d}.webp"
            if output_path.exists():
                continue
            render_webp(
                lecture_dir / lecture_by_id[lecture_id]["file"],
                output_path,
                page_number,
                pdftoppm=pdftoppm,
                dpi=dpi,
                quality=quality,
                max_width=max_width,
                temp_dir=temp_dir,
            )
        if temp_dir.exists():
            temp_dir.rmdir()
    return attached, selected, uncertain


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pdftoppm", default=DEFAULT_PDFTOPPM)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--quality", type=int, default=88)
    parser.add_argument("--max-width", type=int, default=1600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    content = json.loads(args.data.read_text(encoding="utf-8"))
    attached, selected, uncertain = attach_evidence(
        content,
        args.lecture_dir,
        args.output_dir,
        pdftoppm=args.pdftoppm,
        dpi=args.dpi,
        quality=args.quality,
        max_width=args.max_width,
        dry_run=args.dry_run,
    )
    if not args.dry_run:
        args.data.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "attached_groups": attached,
        "referenced_pages": len(selected),
        "uncertain": [{"group": group_id, "score": round(score, 1)} for group_id, score in uncertain],
        "dry_run": args.dry_run,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
