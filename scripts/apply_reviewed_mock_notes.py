#!/usr/bin/env python3
"""Apply individually reviewed notes to both diagnostic papers.

The review files are authored per question. No OCR excerpt selection or
keyword-ranking step is used to generate the study content.
"""
from __future__ import annotations

import json
import re
import hashlib
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_FILES = ['reviewed_mock_med.json', 'reviewed_mock_phys_bio.json', 'reviewed_mock_path_surg.json']
INDEX = Path('/Users/ray/Documents/考研西综/output/27冲刺押题错题本-20261021/讲义索引/全部讲义逐页文本.json')
DATA_FILES = sorted([*ROOT.glob('src/data/*-foundation-mock-exam-data.json'), *ROOT.glob('src/data/*-sprint-exam-data.json')])
SOURCE_HASHES = {}


def load_reviews() -> dict:
    reviews = {}
    for filename in REVIEW_FILES:
        records = json.loads((ROOT / 'scripts' / filename).read_text())
        overlap = reviews.keys() & records.keys()
        if overlap:
            raise ValueError(f'Duplicate review records: {sorted(overlap)}')
        reviews.update(records)
    return reviews


def source_index() -> dict:
    return {Path(entry['path']).name: entry for entry in json.loads(INDEX.read_text())}


def existing_images() -> dict:
    images = {}
    for path in ROOT.glob('src/data/*.json'):
        try:
            data = json.loads(path.read_text())
        except (ValueError, UnicodeDecodeError):
            continue
        def visit(value):
            if isinstance(value, dict):
                if value.get('sourceFile') and isinstance(value.get('page'), int) and value.get('image'):
                    image = value['image']
                    if (ROOT / 'public' / image).exists():
                        images.setdefault((value['sourceFile'], value['page']), image)
                for item in value.values():
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(data)
    return images


def image_for(reference: dict, index: dict, images: dict, render_missing: bool = False) -> str:
    name, page = reference['sourceFile'], reference['page']
    entry = index.get(name)
    if reference.get('sourcePath') and (not entry or reference['sourcePath'] != entry['path']):
        entry = {'path': reference['sourcePath']}
    if not isinstance(page, int) or page < 1 or (entry and entry.get('pages') and page > len(entry['pages'])):
        raise ValueError(f'Invalid source page: {name} / {page}')
    subject = reference['sourceSubject']
    if not entry:
        # Compiled-book pages already visually verified in the review may not
        # be represented in the separate-lecture text index.
        known = reference.get('image') or images.get((name, page))
        if known and (ROOT / 'public' / known).exists():
            return known
        if reference.get('sourcePath'):
            entry = {'path': reference['sourcePath']}
        else:
            raise ValueError(f'Unindexed source with no verified existing image: {name} / {page}')
    source = Path(entry['path'])
    if source not in SOURCE_HASHES:
        SOURCE_HASHES[source] = hashlib.sha256(source.read_bytes()).hexdigest()
    # Original chapter images include different editions. Render the exact
    # reviewed PDF again, keyed by its content hash, rather than trust their
    # deceptively similar lecture/page filenames.
    fingerprint = SOURCE_HASHES[source][:10]
    image = f'exams/reviewed-mocks-20261104/{subject}-{fingerprint}-p{page:03d}.webp'
    target = ROOT / 'public' / image
    if not target.exists():
        if not render_missing:
            raise FileNotFoundError(f'Unrendered reviewed source: {name} / {page}')
        from pypdfium2 import PdfDocument
        target.parent.mkdir(parents=True, exist_ok=True)
        document = PdfDocument(entry['path'])
        if page > len(document):
            raise ValueError(f'Page beyond physical PDF: {name} / {page}')
        bitmap = document[page - 1].render(scale=1.8).to_pil().convert('RGB')
        bitmap.save(target, quality=85, method=4)
        document.close()
    images[(name, page)] = image
    return image


def apply_reviewed_notes(payload: dict, reviews: dict | None = None, index: dict | None = None,
                         images: dict | None = None, render_missing: bool = False) -> int:
    reviews = reviews if reviews is not None else load_reviews()
    index = index if index is not None else source_index()
    images = images if images is not None else existing_images()
    count = 0
    for group in payload.get('groups', []):
        if group['id'] not in reviews:
            continue
        record = reviews[group['id']]
        stem = group['stems'][0]
        if record.get('chapterLectureId'):
            group['lectureIds'] = [record['chapterLectureId']]
            stem['lectureId'] = record['chapterLectureId']
            if record.get('chapterTitle'):
                group['title'] = re.sub(r' · [^·]+$', ' · ' + record['chapterTitle'], group['title'])
        if not record['explanation'].startswith('正确答案：'):
            raise ValueError(f"Missing reviewed answer introduction: {group['id']}")
        if len(record['knowledgeConnections']) < 2 or len(record['lectureSummary']) < 2:
            raise ValueError(f"Incomplete review: {group['id']}")
        stem['explanation'] = record['explanation']
        stem['knowledgeConnections'] = record['knowledgeConnections']
        group['lectureSummary'] = record['lectureSummary']
        if record.get('evidenceNotice'):
            group['lectureEvidenceNotice'] = record['evidenceNotice']
        proposed = record.get('evidencePages')
        if proposed:
            pages = []
            for reference in proposed:
                image = image_for(reference, index, images, render_missing)
                if any(item['image'] == image for item in pages):
                    continue
                name, page = reference['sourceFile'], reference['page']
                number = re.match(r'0?(\d+)', name)
                title = re.sub(r'^\d+\s+27考研：', '', name).split(' 核心-')[0].removesuffix('.pdf')
                pages.append({
                    'lectureId': group['lectureIds'][0],
                    'sourceSubject': reference['sourceSubject'], 'sourceFile': name,
                    'page': page, 'pageLabel': f'PDF第{page}页',
                    **({'lectureNumber': int(number[1])} if number else {}),
                    'title': reference.get('title') or f'{title} · 第{page}页',
                    'image': image, 'questionNumbers': [int(group['sourceQuestion'])],
                    'optionKeys': reference.get('optionKeys', []),
                    'knowledgePoints': reference['knowledgePoints'],
                })
            # Keep the original metabolic diagrams instead of losing them when
            # the accompanying source pages are corrected.
            pages.extend(deepcopy(page) for page in group.get('lectureEvidencePages', [])
                         if page.get('pageLabel') == '解析流程图')
            group['lectureEvidencePages'] = pages
            group['lectureEvidence'] = pages[0]
            stem['lectureEvidencePages'] = deepcopy(pages)
        elif group.get('topic') != '医学人文':
            raise ValueError(f"No reviewed lecture page: {group['id']}")
        count += 1
    return count


def main() -> None:
    reviews, index, images = load_reviews(), source_index(), existing_images()
    expected = set()
    for path in DATA_FILES:
        expected.update(group['id'] for group in json.loads(path.read_text())['groups'])
    if reviews.keys() != expected:
        raise ValueError(f'Missing: {sorted(expected - reviews.keys())}; extra: {sorted(reviews.keys() - expected)}')
    total = 0
    for path in DATA_FILES:
        payload = json.loads(path.read_text())
        total += apply_reviewed_notes(payload, reviews, index, images, render_missing=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reviewedQuestions': total, 'papers': 2, 'dataFiles': len(DATA_FILES)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
