"""Reviewed against workbook pp.45–46 and lecture 30 pp.2–5 (2026-10-11).

Apply after legacy grouping/evidence repair so a rebuild cannot reintroduce
the invented K or erase the lecture-backed answers. Preserve stable row IDs.
"""

REVISION = 'hemolysis-20261011'
HOMEWORK_REVISION = 'hemolysis-homework-20261015'


def repair_hemolysis(payload):
    groups = {g['id']: g for g in payload['groups']}
    g = groups['p45-g3']
    g['options'] = [o for o in g['options'] if o['key'] != 'K']
    g['stems'] = [s for s in g['stems'] if s['text'] != '红细胞自身缺陷和外部异常']
    g['answerRevision'] = 'hemolysis-lab-no-placeholder-20261104'

    g = groups['p46-g1']
    for text, original, answer in [
        ('温抗体型自身免疫性溶血性贫血', 'AIMNO', 'AIMNOU'),
        ('PNH', 'BGSTL', 'BGILST'),
    ]:
        s = next(s for s in g['stems'] if s['text'] == text)
        s.update(answer=list(answer), answerMode='多选', sourceAnswerRaw=original, sourceText=text+' '+answer)
    g['answerRevision'] = REVISION

    for gid, pages, title, description in [
        ('p45-g3', [2, 3], '溶血性贫血检查', '第2页为检查分类和红细胞破坏指标，第3页补充溶血性黄疸。'),
        ('p46-g1', [4, 5], '溶血性贫血类型与汇总表', '第4页为各类溶贫检查与治疗，第5页为六种溶贫的对照汇总表。'),
    ]:
        first, last = pages
        groups[gid]['lectureEvidence'] = {
            'lectureId': 'lecture-30', 'page': first, 'pages': pages,
            'pageLabel': f'第{first}–{last}页',
            'image': f'med/lecture-pages/lecture-30-pages-{first:02d}-{last:02d}.webp',
            'title': f'第30讲第{first}–{last}页：{title}', 'description': description,
        }


def repair_hemolysis_homework(payload):
    groups = {g['id']: g for g in payload['groups']}
    # Retain the legacy group IDs for bookmarks, but move question 8 back to
    # the 15-year-old girl's case (question 6), as corrected on 2026-10-15.
    g = groups['med-teacher-06-07-08']
    previous_case = groups['med-teacher-06-06']
    diagnosis = next(s for s in g['stems'] if s['number'] == 7)
    complication = next(s for s in [*g['stems'], *previous_case['stems']] if s['number'] == 8)
    complication_options = [o for o in [*g['options'], *previous_case['options']] if o['key'].startswith('q8-')]
    # The answer PDF marks B, but Ham/Rous positivity and lecture p.4 identify PNH.
    diagnosis.update(sourceAnswerRaw='B', answerRaw='C', answer=['q7-C'],
                     answerMode='单选', answerState='讲义核对答案')
    # Lecture p.3 explicitly lists gallstones as a common complication of
    # hereditary spherocytosis, matching the family history and fragility test.
    complication.update(sourceAnswerRaw='C', answerRaw='B', answer=['q8-B'],
                        answerMode='单选', answerState='病例归属及讲义核对答案',
                        sourcePage=71, answerSourceNote='第8题对应第6题15岁女孩病例；第30讲第3页列出常并发胆囊结石。')
    investigation = next(s for s in previous_case['stems'] if s['number'] == 6)
    question_text = '为明确诊断,最有价值的检查是'
    if not previous_case.get('sharedStem'):
        assert investigation['text'].endswith(question_text)
        previous_case['sharedStem'] = investigation['text'][:-len(question_text)]
    investigation.update(text=question_text, optionCategory='第 6 题选项', sourcePage=70)
    investigation_options = [o for o in previous_case['options'] if not o['key'].startswith('q8-')]
    for option in investigation_options:
        key = option.get('displayKey', option['key'])
        option.update(key=f'q6-{key}', displayKey=key, category='第 6 题选项')
    investigation['answer'] = [f'q6-{key.removeprefix("q6-")}' for key in investigation['answer']]
    previous_case.update(
        title='第 6、8 题共用病例', sourceQuestion='6、8', sourcePages=[70, 71],
        sharedQuestionCount=2, options=[*investigation_options, *complication_options],
        stems=[investigation, complication], answerRevision=HOMEWORK_REVISION,
        reviewState='第8题病例归属及答案已按讲义复核',
        supplementNotice='第8题归属第6题病例，答案已按讲义核对', answerSourceLabel='核对答案',
        lectureEvidence={
            'lectureId': 'lecture-30', 'page': 2, 'pages': [2, 3], 'pageLabel': '第2–3页',
            'image': 'med/lecture-pages/lecture-30-pages-02-03.webp',
            'title': '第30讲第2–3页：溶血性贫血与红细胞渗透脆性',
            'description': '第3页对应家族史、红细胞渗透脆性增高及常见并发症。',
        },
    )
    case_text = g.pop('sharedStem', '')
    if case_text:
        diagnosis['text'] = f'{case_text} {diagnosis["text"]}'
    diagnosis.pop('optionCategory', None)
    g.pop('sharedQuestionCount', None)
    g['stems'] = [diagnosis]
    g['options'] = [o for o in g['options'] if not o['key'].startswith('q8-')]
    for option in g['options']:
        option.pop('category', None)
    g.update(title='第 7 题 · 病例诊断', sourceQuestion=7,
             answerRevision=HOMEWORK_REVISION, reviewState='诊断已按讲义复核；第8题已移回第6题病例',
             supplementNotice='已核对诊断答案；原第8题已归入第6题病例', answerSourceLabel='讲义答案')
    g['lectureEvidence'] = {
        'lectureId': 'lecture-30', 'page': 4,
        'image': 'med/lecture-pages/lecture-30-page-04.webp',
        'title': '第30讲第4页：阵发性睡眠性血红蛋白尿',
        'description': '对应PNH的临床表现、Ham与Rous试验及治疗。',
    }
    for case in [previous_case, g]:
        case['sourceText'] = ' '.join([case.get('sharedStem', ''),
                                      *(s['text'] for s in case['stems']),
                                      *(o['label'] for o in case['options'])]).strip()
    payload['meta']['answeredStemCount'] = sum(bool(s.get('answer')) for g in payload['groups'] for s in g['stems'])
    payload['meta']['answerNote'] = '按答案PDF红色选项录入，PNH诊断按讲义纠正；第6组第8题归属第6题病例，答案按讲义核对为B；第8组第3题暂不判分'
