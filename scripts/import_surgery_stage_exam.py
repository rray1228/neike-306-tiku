"""Import the 37 supplied surgery exam questions and the user's answer key.

Default output is an apply_patch; --check verifies the saved data against the
PDF. --images converts previously rendered source pages to readable WebP.
"""
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader
from import_surgery_biochemistry_homework import surgery_topic

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '【外科】阶段考试 天天师兄27考研 不白学！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
TARGET = ROOT / 'src/data/surgery-stage-exam-data.json'
KEY = 'surgery-stage-exam-2026-10'
ANSWER_ROWS = ['BBDBB', 'DCDCC', 'DDACC', 'CBBBC', 'ADDCB', 'BCACC', 'CBADA', 'AD']
ANSWERS = ''.join(ANSWER_ROWS)
# Per-question tested chapters. Ulcer perforation uses the existing shared
# medical/surgical ulcer lecture, not the stomach-tumor chapter.
CHAPTERS = [31,35,34,33,32,1,1,4,3,'ulcer',5,7,12,9,8,10,11,
            16,16,16,13,14,'pancreatitis',15,17,19,18,20,29,28,26,21,27,23,24,25,25]


def clean(text):
    text = re.sub(r'\s+', ' ', text.replace('ttsx', '')).strip()
    text = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '', text)
    return re.sub(r'\s*([，。：；、])\s*', r'\1', text)


def extract():
    records = {}
    current = field = None
    pages = PdfReader(SOURCE).pages
    assert len(pages) == 6
    for page_no, page in enumerate(pages, 1):
        for raw in page.extract_text().splitlines():
            line = clean(raw)
            if not line or '每日计划' in line or re.fullmatch(r'- \d+ -', line):
                continue
            match = re.match(r'^(\d{1,2})\.(?!\d)(.*)', line)
            if match:
                number = int(match[1])
                assert number == len(records) + 1, number
                current = {'page':page_no, 'pages':{page_no}, 'text':[match[2]], 'options':{}}
                records[number] = current
                field = current['text']
                continue
            if current is None:
                continue
            current['pages'].add(page_no)
            option = re.match(r'^([A-D])\.(.*)', line)
            if option:
                assert option[1] not in current['options']
                current['options'][option[1]] = [option[2]]
                field = current['options'][option[1]]
            else:
                field.append(line)
    assert list(records) == list(range(1,38))
    for number, q in records.items():
        assert list(q['options']) == list('ABCD'), number
        q['text'] = clean(' '.join(q['text']))
        q['options'] = {k:clean(' '.join(v)) for k,v in q['options'].items()}
        assert q['text'] and all(q['options'].values()), number
    # Verified against page 3: the superscript 9 is flattened by PDF extraction.
    assert '16×109/L' in records[18]['text']
    records[18]['text'] = records[18]['text'].replace('16×109/L', '16×10⁹/L')
    return records


def build():
    assert len(ANSWERS) == len(CHAPTERS) == 37
    assert set(ANSWERS) <= set('ABCD')
    groups = []
    for number, q in extract().items():
        chapter = CHAPTERS[number-1]
        if chapter == 'ulcer':
            topic, lid = '胃十二指肠疾病', 'med-lecture-16'
        else:
            topic = surgery_topic(chapter)
            lid = 'med-lecture-23' if chapter == 'pancreatitis' else f'lecture-{chapter:02d}'
        answer = ANSWERS[number-1]
        groups.append({
            'id':f'{KEY}-q{number:03d}', 'page':q['page'],
            'sourceKey':KEY, 'sourceName':SOURCE_NAME, 'sourceSection':'外科学',
            'sourceQuestion':str(number), 'sourceLabel':'阶段考试',
            'sourcePages':sorted(q['pages']), 'title':f'阶段考试 · 第{number}题',
            'kind':'A', 'kindLabel':'单项选择', 'answerLayout':'rows',
            'topic':topic, 'lectureIds':[lid], 'supplement':True,
            'supplementNotice':'答案按提供的答案序列录入',
            'answerSourceLabel':'提供的答案',
            'answerSourceName':'2026-10-04提供的外科阶段考试答案序列',
            'options':[{'key':k,'displayKey':k,'label':v} for k,v in q['options'].items()],
            'stems':[{'number':number, 'sourceQuestion':number, 'sourcePage':q['page'],
                      'text':q['text'], 'answerRaw':answer, 'answer':[answer],
                      'answerMode':'单选', 'answerState':'按提供的答案序列录入', 'lectureId':lid}],
        })
    med = json.loads((ROOT/'src/data/med-data.json').read_text())
    ulcer = next(l for l in med['lectures'] if l['id']=='lecture-16')
    return {
        'meta':{'title':'外科学·阶段考试', 'sourceName':SOURCE_NAME, 'sourcePages':6,
                'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'groupCount':37, 'stemCount':37, 'answerRows':ANSWER_ROWS,
                'answerNote':'按用户提供的37个答案逐题对应；保留原卷选项顺序，不代表已进行讲义答案勘误。'},
        'lectures':[{'id':'med-lecture-16', 'number':16,
                     'title':'内科与外科 消化性溃疡与消化道出血（共用第16讲）',
                     'pageCount':ulcer['pageCount'], 'file':ulcer['file'], 'sourceSubject':'med'}],
        'groups':groups,
        'pages':[{'page':n,'sourceKey':KEY,'image':f'surgery/{KEY}/page-{n:02d}.webp'} for n in range(1,7)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--images', type=Path)
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT / 'public/surgery' / KEY
        dest.mkdir(parents=True, exist_ok=True)
        for n in range(1,7):
            with Image.open(args.images/f'page-{n}.png') as im:
                im.convert('RGB').save(dest/f'page-{n:02d}.webp', quality=92)
        print('6 original source pages converted to WebP.')
    elif args.check:
        assert json.loads(TARGET.read_text()) == data
        print('37 questions, 148 choices, 37 supplied answers, chapter assignments: PASS')
    else:
        new = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        print('*** Begin Patch')
        if TARGET.exists():
            print('*** Update File: src/data/surgery-stage-exam-data.json')
            for line in list(difflib.unified_diff(TARGET.read_text().splitlines(), new.splitlines(), n=3))[2:]:
                print('@@' if line.startswith('@@') else line)
        else:
            print('*** Add File: src/data/surgery-stage-exam-data.json')
            print('\n'.join('+' + line for line in new.splitlines()))
        print('*** End Patch')


if __name__ == '__main__':
    main()
