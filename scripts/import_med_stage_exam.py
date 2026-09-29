"""Import the 116-question stage exam and the user's ordered answer image.

Print an apply_patch (default); --check verifies the committed data, --images
converts separately rendered PDF pages and retains question 30's ECG image.
No answer is inferred from an option's wording or silently medically corrected.
"""
from pathlib import Path
import argparse
import difflib
import json
import re
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '【内科含诊断】阶段考试 天天师兄27考研 带动复习！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
TARGET = ROOT / 'src/data/med-stage-exam-data.json'
KEY = 'med-stage-exam-2026-09'
# Transcribed row-by-row, left-to-right from the supplied screenshot.
ANSWER_ROWS = [
    'CCDCD CBBAC DBACC', 'CDCAD CDCCB BDDAA',
    'CCBCB DABCC CCBAB', 'CBCDD CAABA ABCCD',
    'CCBAA BBBAA BCABB', 'CCBDB CDCCC CDCCD',
    'DBBDB BDCDC ACBCD', 'ABACA CCABA A',
]
ANSWERS = ''.join(ANSWER_ROWS).replace(' ', '')
SHARED = {42: 43, 71: 72, 74: 76, 89: 91, 94: 95, 96: 97}
# Reviewed by tested knowledge, not by distractor disease names.
CHAPTER_RANGES = [
    (1,3,1),(4,5,9),(6,6,5),(7,7,7),(8,8,6),(9,11,8),
    (12,13,3),(14,15,10),(16,18,13),(19,20,2),(21,22,12),(23,23,11),
    (24,27,55),(28,30,56),(31,32,52),(33,37,54),(38,41,53),
    (42,44,49),(45,46,50),(47,48,51),(49,49,57),
    (50,50,14),(51,52,15),(53,54,16),(55,55,15),(56,56,16),
    (57,58,17),(59,61,18),(62,62,19),(63,64,22),(65,65,20),(66,66,21),(67,67,23),
    (68,68,24),(69,77,27),(78,79,25),(80,81,26),
    (82,84,28),(85,86,30),(87,87,31),(88,88,33),(89,92,34),
    (93,95,35),(96,97,32),(98,98,31),
    (99,100,36),(101,101,37),(102,102,39),(103,104,40),(105,105,41),(106,108,38),
    (109,109,43),(110,110,45),(111,112,44),(113,113,45),(114,114,46),(115,116,48),
]


def clean(text):
    text = re.sub(r'\bttsx\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'\s*([，。：；、])\s*', r'\1', text)
    text = re.sub(r'(?<=\d)- (?=\d)', '-', text)
    text = text.replace('kg/m 2', 'kg/m²')
    # Restore the PDF's superscript laboratory units, not the measured values.
    text = re.sub(r'10\s*(9|12)(?=/L)', lambda m: '10'+{'9':'⁹','12':'¹²'}[m[1]], text)
    return text


def topic(lecture):
    for low, high, name in [(1,13,'呼吸'),(14,23,'消化'),(24,27,'肾脏'),
                            (28,35,'血液'),(36,42,'内分泌'),(43,47,'风湿'),
                            (48,48,'中毒'),(49,57,'循环')]:
        if low <= lecture <= high:
            return name
    raise ValueError(lecture)


def extract():
    records = {}
    shared = {}
    current = None
    field = None
    pending = None
    pages = PdfReader(SOURCE).pages
    assert len(pages) == 21
    for page_no, page in enumerate(pages, 1):
        for raw in page.extract_text().splitlines():
            line = clean(raw)
            if not line or '每日计划' in line or re.fullmatch(r'- \d+ -', line):
                continue
            if '不要焦虑正确率' in line:
                break
            match = re.match(r'^(\d{1,3})\.(?!\d)(.*)', line)
            if match and int(match[1]) == len(records)+1:
                number = int(match[1])
                if pending:
                    assert number in SHARED
                    shared[number] = pending
                    pending = None
                current = {'number': number, 'page': page_no, 'pages': {page_no}, 'text': [match[2]], 'options': {}}
                records[number] = current
                field = current['text']
                continue
            if not current:
                continue  # Cover heading only.
            # These six standalone cases precede their numbered subquestions.
            if current['number']+1 in SHARED and line.startswith('男，'):
                assert list(current['options']) == list('ABCD')
                pending = {'page': page_no, 'pages': {page_no}, 'text': [line]}
                field = pending['text']
                continue
            option = re.match(r'^([A-D])\.(.*)', line)
            (pending if pending else current)['pages'].add(page_no)
            if option and not pending:
                key = option[1]
                assert key not in current['options'], (current['number'], key)
                current['options'][key] = [option[2]]
                field = current['options'][key]
            else:
                assert field is not None, line
                field.append(line)
    assert list(records) == list(range(1,117))
    assert set(shared) == set(SHARED)
    for q in records.values():
        q['text'] = clean(' '.join(q['text']))
        assert list(q['options']) == list('ABCD'), q
        q['options'] = {k:clean(' '.join(v)) for k,v in q['options'].items()}
    for context in shared.values():
        context['text'] = clean(' '.join(context['text']))
    return records, shared


def build():
    assert len(ANSWERS) == 116 and set(ANSWERS) == set('ABCD')
    chapters = {}
    for first,last,lecture in CHAPTER_RANGES:
        for number in range(first,last+1):
            assert number not in chapters
            chapters[number] = lecture
    assert set(chapters) == set(range(1,117))
    records, contexts = extract()
    groups = []
    number = 1
    while number <= 116:
        end = SHARED.get(number, number)
        numbers = list(range(number,end+1))
        lecture = chapters[number]
        assert all(chapters[n] == lecture for n in numbers)
        lid = f'lecture-{lecture:02d}'
        context = contexts.get(number)
        label = str(number) if number == end else f'{number}–{end}'
        g = {'id':f'{KEY}-q{number:03d}', 'page':context['page'] if context else records[number]['page'],
             'sourceKey':KEY, 'sourceName':SOURCE_NAME, 'sourceSection':'内科含诊断',
             'sourceQuestion':label, 'sourceLabel':'阶段考试', 'sourcePages':sorted(set(
                 (list(context['pages']) if context else []) + [p for n in numbers for p in records[n]['pages']])),
             'title':f'阶段考试 · 第{label}题'+('（共用题干）' if context else ''),
             'kind':'A', 'kindLabel':'单项选择', 'answerLayout':'rows', 'topic':topic(lecture), 'lectureIds':[lid],
             'supplement':True, 'supplementNotice':'答案按提供的答案图录入',
             'answerSourceLabel':'提供的答案', 'answerSourceName':'2026-09-29提供的答案截图',
             'options':[], 'stems':[]}
        if context:
            g.update(sharedStem=context['text'], sharedQuestionCount=len(numbers))
        for n in numbers:
            q = records[n]
            category = f'第{n}题选项'
            key_for = lambda key: f'q{n}-{key}' if context else key
            for key,text in q['options'].items():
                option = {'key':key_for(key),'displayKey':key,'label':text}
                if context:
                    option['category'] = category
                g['options'].append(option)
            s = {'number':n,'sourceQuestion':n,'sourcePage':q['page'],'text':q['text'],
                 'answerRaw':ANSWERS[n-1],'answer':[key_for(ANSWERS[n-1])],
                 'answerMode':'单选','answerState':'按提供的答案图录入','lectureId':lid}
            if context:
                s['optionCategory'] = category
            if n == 30:
                s.update(image=f'med/{KEY}/q030-ecg.webp', imageAlt='阶段考试第30题原始心电图')
            g['stems'].append(s)
        groups.append(g)
        number = end+1
    return {'meta':{'title':'内科含诊断·阶段考试','sourceName':SOURCE_NAME,'sourcePages':21,
                    'groupCount':len(groups),'stemCount':116,'answerRows':ANSWER_ROWS,
                    'answerNote':'按用户提供的答案图逐题对应，不代表已进行讲义答案勘误。'},
            'groups':groups,'pages':[{'page':n,'sourceKey':KEY,'image':f'med/{KEY}/page-{n:02d}.webp'} for n in range(1,22)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--images', type=Path, help='Directory containing pdftoppm page-01.png through page-21.png')
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT / 'public/med' / KEY
        dest.mkdir(parents=True, exist_ok=True)
        for n in range(1,22):
            im = Image.open(args.images/f'page-{n:02d}.png').convert('RGB')
            im.save(dest/f'page-{n:02d}.webp', quality=90)
            if n == 6:
                scale = im.width/595.32
                # Original embedded ECG bounds from PDF page 6; no redrawing.
                box = tuple(round(v*scale) for v in (89,403,506,693))
                im.crop(box).save(dest/'q030-ecg.webp', quality=95)
        print('21 source pages and question30 ECG rendered.')
    elif args.check:
        assert json.loads(TARGET.read_text()) == data
        print('116 questions, 6 shared cases, 108 groups, all answers and chapter assignments: PASS')
    else:
        new = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
        print('*** Begin Patch')
        if TARGET.exists():
            print('*** Update File: src/data/med-stage-exam-data.json')
            for line in list(difflib.unified_diff(TARGET.read_text().splitlines(),new.splitlines(),n=3))[2:]:
                print('@@' if line.startswith('@@') else line)
        else:
            print('*** Add File: src/data/med-stage-exam-data.json')
            print('\n'.join('+'+line for line in new.splitlines()))
        print('*** End Patch')


if __name__ == '__main__':
    main()
