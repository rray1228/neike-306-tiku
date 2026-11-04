#!/usr/bin/env python3
"""Reapply reviewed foundation-paper notes; never rank OCR paragraphs."""
import json
from apply_reviewed_mock_notes import ROOT, apply_reviewed_notes, existing_images, load_reviews, source_index


def main() -> None:
    reviews, index, images = load_reviews(), source_index(), existing_images()
    count = 0
    for path in sorted(ROOT.glob('src/data/*-foundation-mock-exam-data.json')):
        payload = json.loads(path.read_text())
        count += apply_reviewed_notes(payload, reviews, index, images, render_missing=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reviewedFoundationQuestions': count}, ensure_ascii=False))


if __name__ == '__main__':
    main()
