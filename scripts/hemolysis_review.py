"""Reviewed against workbook pp.45–46 and lecture 30 pp.2–5 (2026-10-11).

Apply after legacy grouping/evidence repair so a rebuild cannot reintroduce
the invented K or erase the lecture-backed answers. Preserve stable row IDs.
"""

REVISION = 'hemolysis-20261011'


def repair_hemolysis(payload):
    groups = {g['id']: g for g in payload['groups']}
    g = groups['p45-g3']
    g['options'] = [o for o in g['options'] if o['key'] != 'K']
    if not any(s['text'] == '红细胞自身缺陷和外部异常' for s in g['stems']):
        g['stems'].insert(0, {'text': '红细胞自身缺陷和外部异常', 'sourceY': 0})
    s = next(s for s in g['stems'] if s['text'] == '红细胞自身缺陷和外部异常')
    s.update(answer=[], answerMode='待核对', answerState='待原题页核对', sourceText=s['text'])
    g['answerRevision'] = REVISION

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
    g = next(g for g in payload['groups'] if g['id'] == 'med-teacher-06-07-08')
    diagnosis, complication = g['stems']
    # The answer PDF marks B, but Ham/Rous positivity and lecture p.4 identify PNH.
    diagnosis.update(sourceAnswerRaw='B', answerRaw='C', answer=['q7-C'],
                     answerMode='单选', answerState='讲义核对答案')
    # Lecture p.4 names hepatic thrombosis as a cause of death, not the MOST COMMON
    # complication. Do not silently equate those claims or guess C/D from them.
    complication.update(sourceAnswerRaw='C', answerRaw='', answer=[],
                        answerMode='待核对', answerState='待原题页核对')
    g.update(answerRevision=REVISION, reviewState='诊断已按讲义复核；第8题待核对',
             supplementNotice='已核对诊断答案；第8题暂不判分', answerSourceLabel='讲义答案')
    g['lectureEvidence'] = {
        'lectureId': 'lecture-30', 'page': 4,
        'image': 'med/lecture-pages/lecture-30-page-04.webp',
        'title': '第30讲第4页：阵发性睡眠性血红蛋白尿',
        'description': '对应PNH的临床表现、Ham与Rous试验及治疗。',
    }
    payload['meta']['answeredStemCount'] = sum(bool(s.get('answer')) for g in payload['groups'] for s in g['stems'])
    payload['meta']['answerNote'] = '按答案PDF红色选项录入，PNH诊断按讲义纠正；第6组第8题及第8组第3题暂不判分'
