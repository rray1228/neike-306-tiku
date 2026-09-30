"""Import 51 pathology exam questions, classified by tested knowledge.

Print an apply_patch by default. --check verifies reproducibility; --images
converts rendered PDF pages to the source images used by the website.
"""
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '【病理】阶段考试 天天师兄27考研 不要焦虑！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
TARGET = ROOT / 'src/data/pathology-stage-exam-data.json'
KEY = 'pathology-stage-exam-2026-09'
# Transcribed left-to-right, top-to-bottom from the supplied answer image.
ANSWER_ROWS = ['DBAAD DDAAA ADCAA', 'BDDAD BCACC BDCAD',
               'DCDAA ABABC BBCBD', 'DCAAA B']
ANSWERS = ''.join(ANSWER_ROWS).replace(' ', '')
# A missing lecture is intentional: the existing 26 PDFs do not contain a
# dedicated lymphohematopoietic or urinary chapter. Do not invent a PDF link.
CHAPTER_RANGES = [
    (1,3,'损伤与修复',23), (4,6,'损伤与修复',22),
    (7,8,'局部血液循环障碍',24), (9,11,'炎症',25), (12,16,'肿瘤',26),
    (17,19,'免疫性疾病',17), (20,20,'心血管系统',9),
    (21,22,'心血管系统',7), (23,23,'心血管系统',10),
    (24,24,'呼吸系统',14), (25,27,'呼吸系统',15),
    (28,28,'消化系统',1), (29,29,'消化系统',2),
    (30,30,'消化系统',3), (31,31,'消化系统',5),
    (32,33,'淋巴造血系统',None), (34,37,'泌尿系统',None),
    (38,40,'生殖系统',18), (41,41,'乳腺疾病',19),
    (42,44,'内分泌系统',16), (45,45,'传染病',21),
    (46,48,'传染病',20), (49,51,'传染病',21),
]


def clean(text):
    text = re.sub(r'\s+', ' ', text.replace('ttsx', '')).strip()
    text = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '', text)
    return re.sub(r'\s*([，。：；、])\s*', r'\1', text)


def extract():
    records = {}
    current = field = None
    pages = PdfReader(SOURCE).pages
    assert len(pages) == 8
    for page_no, page in enumerate(pages, 1):
        for raw in page.extract_text().splitlines():
            line = clean(raw)
            if not line or '每日计划' in line or re.fullmatch(r'- \d+ -', line):
                continue
            match = re.match(r'^(\d{1,2})\.(?!\d)(.*)', line)
            if match:
                number = int(match[1])
                assert number == len(records) + 1, (number, len(records))
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
    assert list(records) == list(range(1, 52))
    for record in records.values():
        assert list(record['options']) == list('ABCD'), record
        record['text'] = clean(' '.join(record['text']))
        record['options'] = {k:clean(' '.join(v)) for k,v in record['options'].items()}
        assert record['text'] and all(record['options'].values())
    return records


def build():
    assert len(ANSWERS) == 51 and set(ANSWERS) <= set('ABCD')
    chapters = {}
    for first, last, topic, lecture in CHAPTER_RANGES:
        for number in range(first, last + 1):
            assert number not in chapters
            chapters[number] = (topic, f'lecture-{lecture:02d}' if lecture else None)
    assert set(chapters) == set(range(1, 52))
    groups = []
    for number, q in extract().items():
        topic, lid = chapters[number]
        groups.append({
            'id':f'{KEY}-q{number:03d}', 'page':q['page'],
            'sourceKey':KEY, 'sourceName':SOURCE_NAME, 'sourceSection':'病理学',
            'sourceQuestion':str(number), 'sourceLabel':'阶段考试',
            'sourcePages':sorted(q['pages']), 'title':f'阶段考试 · 第{number}题',
            'kind':'A', 'kindLabel':'单项选择', 'answerLayout':'rows',
            'topic':topic, 'lectureIds':[lid] if lid else [], 'supplement':True,
            'supplementNotice':'答案按提供的答案图录入',
            'answerSourceLabel':'提供的答案',
            'answerSourceName':'2026-09-30提供的病理阶段考试答案截图',
            'options':[{'key':k,'displayKey':k,'label':v} for k,v in q['options'].items()],
            'stems':[{'number':number, 'sourceQuestion':number, 'sourcePage':q['page'],
                      'text':q['text'], 'answerRaw':ANSWERS[number-1],
                      'answer':[ANSWERS[number-1]], 'answerMode':'单选',
                      'answerState':'按提供的答案图录入',
                      **({'lectureId':lid} if lid else {})}],
        })
    return {
        'meta':{'title':'病理学·阶段考试', 'sourceName':SOURCE_NAME, 'sourcePages':8,
                'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'groupCount':51, 'stemCount':51, 'answerRows':ANSWER_ROWS,
                'answerNote':'按用户提供的答案图逐题对应，不代表已进行讲义答案勘误。'},
        'topics':['淋巴造血系统','泌尿系统'],
        'groups':groups,
        'pages':[{'page':n,'sourceKey':KEY,'image':f'pathology/{KEY}/page-{n:02d}.webp'} for n in range(1,9)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--images', type=Path)
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT / 'public/pathology' / KEY
        dest.mkdir(parents=True, exist_ok=True)
        for n in range(1,9):
            with Image.open(args.images/f'page-{n}.png') as im:
                im.convert('RGB').save(dest/f'page-{n:02d}.webp', quality=92)
        print('8 original source pages converted.')
    elif args.check:
        assert json.loads(TARGET.read_text()) == data
        print('51 questions, 204 choices, 51 screenshot answers, chapter assignments: PASS')
    else:
        new = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        print('*** Begin Patch')
        if TARGET.exists():
            print('*** Update File: src/data/pathology-stage-exam-data.json')
            for line in list(difflib.unified_diff(TARGET.read_text().splitlines(), new.splitlines(), n=3))[2:]:
                print('@@' if line.startswith('@@') else line)
        else:
            print('*** Add File: src/data/pathology-stage-exam-data.json')
            print('\n'.join('+' + line for line in new.splitlines()))
        print('*** End Patch')


if __name__ == '__main__':
    main()
