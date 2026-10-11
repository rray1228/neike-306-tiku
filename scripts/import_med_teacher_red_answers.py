"""Read option-letter colors from the teacher's answer PDF; emit an apply_patch.

Never infer an answer from medical knowledge or from red emphasis in a stem.
Only a red A/B/C/D option marker is an answer. Existing stable question IDs
are retained, including per-question keys inside shared-stem groups.
"""
from __future__ import annotations
import argparse
import difflib
import json
import re
import sys
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_teacher_pathology_med_supplements import clean, med_topic, MED_LECTURES, title_for_question
from hemolysis_review import repair_hemolysis_homework

EXPECTED = {1:16, 2:19, 3:18, 4:12, 5:12, 6:15, 7:15, 8:19}
LECTURES = {**MED_LECTURES,
    7:[32,39,36,36,36,36,36,37,37,37,37,37,40,41,41],
    8:[38,38,38,38,45,45,45,45,44,44,46,46,47,47,47,47,48,48,48]}
MARKER = re.compile(r'([A-D])[.．]')

def red(char):
    color = char.get('non_stroking_color')
    return isinstance(color, (tuple,list)) and len(color)==3 and color[0]>.8 and color[1]<.2 and color[2]<.2

def extract(path):
    records = {}
    section = None
    current = None
    pending = None
    context = None
    active_option = None
    with pdfplumber.open(path) as doc:
        for page_number, page in enumerate(doc.pages, 1):
            for line in page.extract_text_lines():
                text = clean(line['text'])
                header = re.match(r'内科含诊断\s*(\d+)\s*课后巩固',text)
                if header:
                    section=int(header.group(1));current=None;context=None;pending=None;active_option=None
                    continue
                if re.search(r'第\s*\d+\s*页\s*/\s*共',text): continue
                shared = re.match(r'\((\d+)-(\d+)题共用题干\)(.*)',text)
                if shared:
                    pending={'start':int(shared.group(1)),'end':int(shared.group(2)),'text':shared.group(3)}
                    active_option=None
                    continue
                question = re.match(r'^(\d{1,2})[.、](?!\d)\s*(.*)',text)
                expected_number = 1 + sum(s == section for s, _ in records)
                if question and int(question.group(1)) != expected_number:
                    question = None
                if question and section:
                    number=int(question.group(1))
                    if pending:
                        assert number==pending['start'],(section,number,pending)
                        context=pending;pending=None
                    current={'section':section,'number':number,'page':page_number,'text':question.group(2),
                             'context':context['text'] if context and number<=context['end'] else '',
                             'options':{},'answer':[]}
                    assert (section,number) not in records,(section,number)
                    records[section,number]=current;active_option=None
                    continue
                if pending:
                    pending['text']+=' '+text
                    continue
                if not current: continue
                chars=sorted(line['chars'],key=lambda c:c['x0'])
                raw=''.join(c['text'] for c in chars)
                matches=list(MARKER.finditer(raw))
                if matches:
                    for index,match in enumerate(matches):
                        key=match.group(1)
                        label=clean(raw[match.end():matches[index+1].start() if index+1<len(matches) else len(raw)])
                        assert key not in current['options'],(section,current['number'],key)
                        current['options'][key]=label;active_option=key
                        if red(chars[match.start()]): current['answer'].append(key)
                elif active_option:
                    current['options'][active_option]+=' '+text
                else:
                    current['text']+=' '+text
    for section,count in EXPECTED.items():
        assert sorted(n for s,n in records if s==section)==list(range(1,count+1)),section
    for key,record in records.items():
        record['answer']=sorted(set(record['answer']))
        assert len(record['options'])==4 or key==(8,3),(key,record)
        assert record['answer'] or key==(8,3),(key,'No red answer')
    return records

def bind_answers(g,records,section):
    for s in g['stems']:
        record=records[section,s['number']]
        choices=[o for o in g['options'] if not s.get('optionCategory') or o.get('category')==s['optionCategory']]
        # Check all four markers against the existing question, not its position alone.
        assert {o.get('displayKey',o['key']) for o in choices}==set(record['options']),(g['id'],s['number'])
        for o in choices:
            label=o.get('displayKey',o['key'])
            a=re.sub(r'[^\w]', '',clean(o['label'])).lower()
            b=re.sub(r'[^\w]', '',clean(record['options'][label])).lower()
            assert difflib.SequenceMatcher(None,a,b).ratio()>.63,(g['id'],s['number'],label,a,b)
        s['answerRaw']=''.join(record['answer'])
        s['answer']=[o['key'] for o in choices if o.get('displayKey',o['key']) in record['answer']]
        s['answerMode']='多选' if len(s['answer'])>1 or '多选' in record['text'] else '单选'
        s['answerState']='原PDF标红答案' if s['answer'] else '原PDF选项与答案缺失'
        s['answerSourcePage']=record['page']
    g['answerSourceLabel']='课后题答案'
    g['answerSourceName']='内科含诊断课后巩固合集（答案）.pdf'
    g['reviewState']='按答案PDF红色选项录入（非讲义勘误）'
    g['supplementNotice']='已录入原PDF标红答案'
    g['kindLabel']='多项选择' if all(s['answerMode']=='多选' for s in g['stems']) else '单项选择'

def new_groups(records):
    groups=[]
    for section in [7,8]:
        number=1
        while number<=EXPECTED[section]:
            q=records[section,number];block=[q]
            while q['context'] and number+len(block)<=EXPECTED[section] and records[section,number+len(block)]['context']==q['context']:
                block.append(records[section,number+len(block)])
            suffix=f'{number:02d}' if len(block)==1 else f'{number:02d}-{block[-1]["number"]:02d}'
            options=[];stems=[]
            for item in block:
                lecture=f'lecture-{LECTURES[section][item["number"]-1]:02d}'
                category=f'第 {item["number"]} 题选项'
                for key,label in sorted(item['options'].items()):
                    option={'key':key,'label':clean(label)}
                    if len(block)>1: option.update(key=f'q{item["number"]}-{key}',displayKey=key,category=category)
                    options.append(option)
                s={'number':item['number'],'text':clean(item['text']),'sourceQuestion':item['number'],'lectureId':lecture}
                if len(block)>1:s['optionCategory']=category
                stems.append(s)
            ids=list(dict.fromkeys(s['lectureId'] for s in stems))
            topics={med_topic(LECTURES[section][item['number']-1]) for item in block}
            assert len(topics)==1,(section,number,topics)
            g={'id':f'med-teacher-{section:02d}-{suffix}','page':q['page'],'sourceKey':'teacher-answers-2026-09',
               'sourceName':'内科含诊断课后巩固合集（答案）.pdf','sourceSection':f'内科含诊断·第 {section} 组',
               'sourceQuestion':number if len(block)==1 else f'{number}–{block[-1]["number"]}',
               'title':title_for_question(q) if len(block)==1 else f'第 {number}–{block[-1]["number"]} 题共用题干',
               'kind':'A','options':options,'stems':stems,'sourceText':q['context']+' '+ ' '.join(item['text'] for item in block),
               'topic':topics.pop(),'lectureIds':ids,'supplement':True}
            if len(block)>1:g.update(sharedStem=clean(q['context']),sharedQuestionCount=len(block))
            bind_answers(g,records,section)
            if (section,number)==(8,3) or any(item['number']==3 and section==8 for item in block):
                g['supplementNotice']='第8组第3题原PDF缺A选项且未标红答案；该题暂不判分'
            groups.append(g);number+=len(block)
    return groups

def emit_file_patch(relative,old,new):
    diff=list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=3))
    if diff:print('*** Update File: '+str(ROOT/relative)+'\n'+'\n'.join('@@' if line.startswith('@@') else line for line in diff[2:]))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('pdf',type=Path);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    records=extract(args.pdf)
    path=ROOT/'src/data/med-teacher-supplement.json';old=path.read_text();data=json.loads(old)
    if args.check:
        print(json.dumps({str(s):[''.join(records[s,n]['answer']) or 'MISSING' for n in range(1,c+1)] for s,c in EXPECTED.items()},ensure_ascii=False));return
    original_groups=[g for g in data['groups'] if int(g['id'].split('-')[2])<=6]
    for g in original_groups:bind_answers(g,records,int(g['id'].split('-')[2]))
    data['groups']=sorted(original_groups+new_groups(records),key=lambda g:min((int(x[-2:]) for x in g['lectureIds']),default=58))
    data['meta'].update(sourceAnswerPdf=args.pdf.name,groupCount=len(data['groups']),stemCount=126,answeredStemCount=125,answerNote='按答案PDF红色选项录入；第8组第3题原PDF缺选项与答案，暂不判分')
    repair_hemolysis_homework(data)
    assert sum(len(g['stems']) for g in data['groups'])==126
    print('*** Begin Patch');emit_file_patch('src/data/med-teacher-supplement.json',old,json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('*** End Patch')

if __name__=='__main__':main()
