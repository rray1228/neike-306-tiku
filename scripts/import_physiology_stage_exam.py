"""Import the 62-question physiology exam with the supplied answer screenshot.

Default output is an apply_patch. --check checks reproducibility; --images
converts rendered original PDF pages for the website's source viewer.
"""
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '【生理】阶段考试 天天师兄27考研 加油哦！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
TARGET = ROOT / 'src/data/physiology-stage-exam-data.json'
KEY = 'physiology-stage-exam-2026-09'
# Screenshot rows in original order; all 62 answers are single choices.
ANSWER_ROWS = [
    'BCCCC', 'BBDDC', 'BDDCA', 'DCCDA', 'CADDC', 'AACDA',
    'CBDCC', 'DCDCD', 'CDABA', 'CDBCC', 'ADACC', 'BAACA', 'CB',
]
ANSWERS = ''.join(ANSWER_ROWS)
# Primary tested knowledge determines the lecture, not diseases in distractors.
CHAPTER_RANGES = [
    (1,1,1), (2,2,2), (3,5,3), (6,8,4), (9,12,5),
    (13,13,7), (14,14,8), (15,15,6), (16,16,9), (17,17,10),
    (18,18,12), (19,19,11), (20,20,13), (21,21,14), (22,23,15),
    (24,25,16), (26,26,17), (27,27,18), (28,28,19), (29,29,20),
    (30,31,21), (32,33,22), (34,35,23), (36,37,25), (38,40,26),
    (41,41,24), (42,42,27), (43,43,28), (44,46,29), (47,48,31),
    (49,49,32), (50,50,33), (51,52,34), (53,53,35), (54,54,36),
    (55,55,37), (56,57,38), (58,58,39), (59,59,40), (60,62,41),
]


def clean(text):
    text = text.replace('ttsx', '')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'\s*([，。：；、])\s*', r'\1', text)
    # Visual check of page 2 confirms STAT; page 6 uses square metres.
    text = text.replace('STA T', 'STAT').replace('m2', 'm²')
    return text


def topic(lecture):
    # Keep lecture 23 in the existing directory's energy/renal section.
    for lo, hi, name in [
        (1,1,'绪论'), (2,5,'细胞基本功能'), (6,8,'血液'),
        (9,13,'循环系统'), (14,17,'呼吸系统'), (18,22,'消化系统'),
        (23,26,'泌尿系统'), (27,29,'感觉系统'), (30,34,'中枢神经系统'),
        (35,40,'内分泌'), (41,41,'生殖系统'),
    ]:
        if lo <= lecture <= hi:
            return name
    raise ValueError(lecture)


def extract():
    records = {}
    current = field = None
    pages = PdfReader(SOURCE).pages
    assert len(pages) == 11
    for page_no, page in enumerate(pages, 1):
        for raw in page.extract_text().splitlines():
            line = clean(raw)
            if not line or '每日计划' in line or re.fullmatch(r'- \d+ -', line):
                continue
            if '不要焦虑正确率' in line:
                break
            match = re.match(r'^(\d{1,2})\.(?!\d)(.*)', line)
            if match:
                number = int(match[1])
                assert number == len(records)+1, (number, len(records))
                current = {'number':number, 'page':page_no, 'pages':{page_no},
                           'text':[match[2]], 'options':{}}
                records[number] = current
                field = current['text']
                continue
            if current is None:
                continue
            current['pages'].add(page_no)
            option = re.match(r'^([A-D])\.(.*)', line)
            if option:
                assert option[1] not in current['options'], current
                current['options'][option[1]] = [option[2]]
                field = current['options'][option[1]]
            else:
                field.append(line)
    assert list(records) == list(range(1,63))
    for record in records.values():
        assert list(record['options']) == list('ABCD'), record
        record['text'] = clean(' '.join(record['text']))
        record['options'] = {k:clean(' '.join(v)) for k,v in record['options'].items()}
        assert record['text'] and all(record['options'].values())
    return records


def build():
    assert len(ANSWERS) == 62 and set(ANSWERS) <= set('ABCD')
    chapters = {}
    for first,last,lecture in CHAPTER_RANGES:
        for number in range(first,last+1):
            assert number not in chapters
            chapters[number] = lecture
    assert set(chapters) == set(range(1,63))
    groups = []
    for number, q in extract().items():
        lid = f'lecture-{chapters[number]:02d}'
        groups.append({
            'id':f'{KEY}-q{number:03d}', 'page':q['page'],
            'sourceKey':KEY, 'sourceName':SOURCE_NAME, 'sourceSection':'生理学',
            'sourceQuestion':str(number), 'sourceLabel':'阶段考试',
            'sourcePages':sorted(q['pages']), 'title':f'阶段考试 · 第{number}题',
            'kind':'A', 'kindLabel':'单项选择', 'answerLayout':'rows',
            'topic':topic(chapters[number]), 'lectureIds':[lid], 'supplement':True,
            'supplementNotice':'答案按提供的答案图录入',
            'answerSourceLabel':'提供的答案', 'answerSourceName':'2026-09-29提供的生理阶段考试答案截图',
            'options':[{'key':k,'displayKey':k,'label':v} for k,v in q['options'].items()],
            'stems':[{'number':number, 'sourceQuestion':number, 'sourcePage':q['page'],
                      'text':q['text'], 'answerRaw':ANSWERS[number-1],
                      'answer':[ANSWERS[number-1]], 'answerMode':'单选',
                      'answerState':'按提供的答案图录入', 'lectureId':lid}],
        })
    return {
        'meta':{'title':'生理学·阶段考试', 'sourceName':SOURCE_NAME, 'sourcePages':11,
                'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'groupCount':62, 'stemCount':62, 'answerRows':ANSWER_ROWS,
                'answerNote':'按用户提供的答案图逐题对应，不代表已进行讲义答案勘误。'},
        'groups':groups,
        'pages':[{'page':n,'sourceKey':KEY,'image':f'physiology/{KEY}/page-{n:02d}.webp'} for n in range(1,12)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--images', type=Path)
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT / 'public/physiology' / KEY
        dest.mkdir(parents=True, exist_ok=True)
        for n in range(1,12):
            with Image.open(args.images/f'page-{n:02d}.png') as im:
                im.convert('RGB').save(dest/f'page-{n:02d}.webp', quality=92)
        print('11 original source pages converted.')
    elif args.check:
        assert json.loads(TARGET.read_text()) == data
        print('62 questions, 248 choices, 62 screenshot answers, chapter assignments: PASS')
    else:
        new = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
        print('*** Begin Patch')
        if TARGET.exists():
            print('*** Update File: src/data/physiology-stage-exam-data.json')
            for line in list(difflib.unified_diff(TARGET.read_text().splitlines(),new.splitlines(),n=3))[2:]:
                print('@@' if line.startswith('@@') else line)
        else:
            print('*** Add File: src/data/physiology-stage-exam-data.json')
            print('\n'.join('+'+line for line in new.splitlines()))
        print('*** End Patch')


if __name__ == '__main__':
    main()
