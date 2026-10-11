"""Source-page 35–60 review, checked against lectures 24–35.

Apply after OCR/manual grouping. Never rebuild other systems as a side effect.
Letter case is significant (notably p45, p40 and p60).
"""

OPTION_REPAIRS = {
    'p36-g1': {'A': '有全身症状（T>38℃、血WBC↑）', 'P': '喹诺酮类（除外莫西沙星）'},
    'p37-g1': {'A': '尿比重≤1.012', 'I': '尿比重≥1.018', 'L': '尿肌酐/血清肌酐≥40'},
    'p37-g2': {'J': 'β2-微球蛋白'},
    'p38-g2': {'C': '血Cr≥707 μmol/L', 'D': 'GFR≥90 ml/(min·1.73m²)'},
    'p39-g2': {'E': '急进性肾炎（《病理学》中也可叫急进性肾炎综合征）'},
    'p39-g3': {'J': '水肿多从下肢开始（赖不住水），或从眼睑、颜面部开始'},
    'p40-g1': {
        'F': '部分肾小球的部分毛细血管袢硬化（累及少数肾小球<50%，累及肾小球的少数毛细血管袢<50%）',
        'e': '可表现为各种病理类型，以系膜增生性肾炎最常见',
        'f': '起病缓慢而隐匿，病程常>3个月，可急性发作；B超示双肾体积早期正常、后期对称性缩小（长径<10cm）',
    },
    'p41-g1': {'J': '收缩压<120 mmHg、尿蛋白<1 g/d', 'D': '不常规应用糖皮质激素＋环磷酰胺'},
    'p42-g3': {'F': '口腔炎和口角炎、舌乳头萎缩呈镜面舌/光滑舌'},
    'p43-g2': {'E': '骨髓铁染色示骨髓小粒可染铁消失：骨髓小粒的铁蛋白和含铁血黄素（骨髓细胞外铁）缺乏'},
    'p48-g1': {'K': '内脏出血多见（深）', 'L': '内脏出血多见（浅）'},
    'p49-g1': {'F': '出血倾向：血小板减少、血小板功能异常（被M蛋白包裹）、凝血异常、血管壁受损'},
    'p49-g2': {'G': '血肌酐≥177 μmol/L，或肌酐清除率≤40 ml/min'},
    'p50-g1': {'A': '骨髓原始细胞≥30%为急性白血病', 'B': '骨髓原始细胞≥20%为急性白血病'},
    'p51-g2': {'C': '外周血贫血或全血细胞↓'},
    'p51-g3': {'E': '网织红细胞↓（原位溶血时可正常或轻度增加）', 'G': '巨核细胞数量显著减少（全片未见巨核细胞）'},
    'p52-g3': {
        'B': '骨髓原始细胞占NEC≥30%，各阶段粒细胞≥20%，各阶段单核细胞≥20%',
        'C': '骨髓原粒细胞占NEC的30%～89%',
        'D': '骨髓原始细胞占NEC≥30%，幼红细胞≥50%',
        'E': '骨髓原始巨核细胞≥30%，血小板抗原（+）',
        'H': '骨髓原和幼单核细胞占NEC≥30%，各阶段单核细胞≥80%',
        'I': '骨髓早幼粒细胞占NEC≥30%',
    },
    'p52-g4': {
        'C': '肝脾肿大：多为轻中度，巨脾见于CML及CML急性变',
        'G': '出血：血小板减少、感染、凝血异常、白血病细胞浸润血管壁、白血病细胞淤滞在血管腔',
        'H': '淋巴结肿大（多无痛）：多见于ALL、CLL，纵隔淋巴结肿大多见于T细胞性；AML有时可有，CML几乎无淋巴结肿大',
    },
    'p53-g3': {'B': 't(8;21)(q22;q22)形成RUNX1-RUNX1T1（AML1-ETO）'},
    'p53-g4': {'A': '骨髓早幼粒细胞≥30%', 'E': '各阶段单核细胞≥80%', 'M': 't(8;21)(q22;q22)→RUNX1-RUNX1T1'},
    'p54-g3': {'C': '多数为急粒变，也可为淋巴、单核、巨核、红细胞等类型急性变', 'H': '外周血或骨髓原始细胞≥10%、外周血嗜碱性粒细胞>20%、血小板进行性减少或增加'},
    'p55-g2': {'C': '常见骨髓象：原始细胞≥30%（FAB分型）或≥20%（WHO分型）', 'L': '常见骨髓象：慢性期原始细胞<10%，加速期原始细胞≥10%，急变期原始细胞>20%'},
    'p56-g1': {
        'A': '膈肌同侧≥2组淋巴结',
        'C': '膈肌上下组淋巴结；可伴相关结外器官局部受累ⅢE、可累及脾ⅢS（查体触及或影像），可两者均有ⅢE+S',
        'F': '多个结外器官（如剖腹探查见胃与胰头及腹膜粘连）',
    },
    'p56-g2': {'F': '首发部位2/3为淋巴结、1/3为结外器官组织（胃肠道以回肠、胸部以肺门和纵隔、骨骼以胸腰椎最常见）'},
    'p57-g2': {
        'F': '儿童更多见，常表现为白血病（血WBC↑，但一般不超过100×10⁹/L）',
        'H': '区分反应性增生滤泡和肿瘤滤泡：肿瘤单克隆、18号染色体的BCL2基因转位致BCL2蛋白高表达',
        'J': '满天星/星空现象（瘤细胞间有胞质丰富的反应性巨噬细胞）→预后差',
        'K': '外周血B淋巴细胞≥5×10⁹/L、骨髓淋巴细胞≥40%，以成熟淋巴细胞为主',
    },
    'p58-g2': {'B': '霍奇金细胞（单核）'},
}

# Primary lecture and exact evidence page; no broad whole-system association.
LOCATIONS = {
    'p35-g1': (24, 1), 'p35-g2': (24, 2), 'p35-g3': (25, 1),
    'p36-g1': (25, 2), 'p36-g2': (25, 3), 'p36-g3': (26, 1),
    'p37-g1': (26, 1), 'p37-g2': (26, 2), 'p37-g3': (26, 2),
    'p38-g1': (26, 2), 'p38-g2': (26, 3), 'p38-g3': (27, 1),
    'p39-g1': (27, 3), 'p39-g2': (27, 3), 'p39-g3': (27, 3),
    'p40-g1': (27, 12), 'p41-g1': (27, 12), 'p41-g2': (27, 10), 'p41-g3': (27, 11),
    'p42-g1': (28, 1), 'p42-g2': (28, 1), 'p42-g3': (28, 1), 'p42-g4': (28, 2),
    'p43-g1': (28, 3), 'p43-g2': (28, 2), 'p44-g1': (28, 4), 'p44-g2': (29, 1),
    'p45-g1': (30, 2), 'p45-g2': (30, 2), 'p45-g3': (30, 2), 'p45-g4': (30, 4),
    'p46-g1': (30, 4), 'p46-g2': (31, 1), 'p46-g3': (31, 2),
    'p47-g1': (31, 2), 'p47-table1': (31, 2), 'p47-g2': (31, 2),
    'p48-g1': (31, 3), 'p48-g2': (31, 3),
    'p49-g1': (32, 1), 'p49-g2': (32, 2), 'p49-g3': (32, 2),
    'p50-g1': (33, 1), 'p50-g2': (33, 1), 'p50-g3': (33, 1),
    'p51-g1': (33, 2), 'p51-g2': (33, 3), 'p51-g3': (33, 3),
    'p52-g1': (34, 1), 'p52-g2': (34, 2), 'p52-g3': (34, 2), 'p52-g4': (34, 2),
    'p53-g1': (34, 2), 'p53-g2': (34, 3), 'p53-g3': (34, 4), 'p53-g4': (34, 5),
    'p54-g1': (34, 5), 'p54-g2': (34, 5), 'p54-g3': (34, 6),
    'p55-g1': (34, 6), 'p55-g2': (34, 6),
    'p56-g1': (35, 1), 'p56-g2': (35, 1), 'p56-g3': (35, 4),
    'p57-g1': (35, 3), 'p57-g2': (35, 3),
    'p58-g1': (35, 3), 'p58-g2': (35, 5), 'p58-g3': (35, 5), 'p58-g4': (35, 5),
    'p59-g1': (35, 5), 'p60-g1': (35, 6),
}


def repair_renal_blood(payload):
    from manual_med_review import option, stem, group, opts, stems

    groups = {g['id']: g for g in payload['groups']}

    def answers(gid, values):
        g = groups[gid]
        assert len(g['stems']) == len(values), gid
        for s, answer in zip(g['stems'], values):
            s.update(answer=list(answer), answerMode='多选' if len(answer) > 1 else '单选', sourceText=s['text'] + ' ' + answer)
            s.pop('answerState', None)

    def rename(gid, title):
        groups[gid]['title'] = title

    for gid, repairs in OPTION_REPAIRS.items():
        bank = {o['key']: o for o in groups[gid]['options']}
        for key, text in repairs.items():
            bank[key].update(label=text, sourceText=key+'.'+text)

    rename('p36-g1', '急性膀胱炎与急性肾盂肾炎鉴别')
    groups['p36-g1']['stems'][1]['text'] = '急性肾盂肾炎（尿路刺激症可有可无）'
    rename('p37-g2', '尿毒症毒素分类')
    rename('p37-g3', '肾脏疾病的贫血特点')
    answers('p38-g2', ['D', 'BEF', 'HJM', 'JLM', 'GKN', 'ACI'])
    rename('p40-g1', '肾小球疾病病理与临床表现')
    groups['p40-g1']['stems'][0]['text'] = '急性肾炎（包括重型的病理改变）'
    # The source's shared bracket BgJKdik applies to ALL THREE RPGN subtypes.
    answers('p40-g1', ['EJKLNObgikl', 'BJKMPdgik', 'BJKNOdgikm', 'BJKMQdgik', 'AHIKMQhq', 'ACKNOajks', 'GKNOikop', 'DKNOikmo', 'AFKNOjk', 'KNOceiknor', 'KNOfik'])
    rename('p41-g2', '急性肾炎、IgA肾病与过敏性紫癜肾炎鉴别')
    rename('p42-g1', '巨幼细胞贫血与缺铁性贫血的核浆发育')
    rename('p42-g2', '二价铁与三价铁的功能')
    rename('p42-g3', '一般贫血与组织缺铁的表现')
    rename('p43-g1', '常见贫血的铁代谢指标鉴别')
    answers('p45-g2', ['aceg', 'bcdef'])
    # The unanswered source row is restored below, without inventing option K.
    if not any(s['answer'] == ['G'] for s in groups['p46-g3']['stems']):
        groups['p46-g3']['stems'].append(stem('起效慢、不单独用', 'G'))
    groups['p46-g3']['stems'][8]['text'] = '妊娠时讲义列为不适合的治疗'
    rename('p47-g1', '出血性疾病的机制分类')
    rename('p48-g1', '出血性疾病的临床特点')
    # Preserve independent regimens and their component letters from page 49.
    g = groups['p49-g3']
    g['options'] = opts(('A', 'VD'), ('B', 'MVP'), ('C', '硼替佐米'), ('D', 'RD'), ('E', '美法仑/马法兰'), ('F', '来那度胺'), ('G', '泼尼松'), ('H', '地塞米松'))
    g['stems'] = stems(('移植候选者可选的诱导化疗方案', 'AD'), ('不适合移植者可选的诱导化疗方案', 'ABD'), ('VD方案组成', 'CH'), ('RD方案组成', 'FH'), ('MVP方案组成', 'CEG'))
    g['optionBankSections'] = [{'title': '方案名称', 'keys': list('ABD')}, {'title': '组成药物', 'keys': list('CEFGH')}]
    g = groups['p49-g2']
    g['stems'][2]['text'] = 'Ⅲ期A亚型：选出A亚型条件及全部Ⅲ期指标（Ⅲ期指标满足任一即可分期）'
    g['stems'][3]['text'] = 'Ⅲ期B亚型：选出B亚型条件及全部Ⅲ期指标（Ⅲ期指标满足任一即可分期）'
    groups['p50-g2']['stems'][3]['text'] = 'RAEB-t可用于判定的指标（满足任一即可）'
    groups['p50-g3']['stems'][1]['text'] = 'MDS-IB1可用于判定的指标（满足任一即可）'
    groups['p50-g3']['stems'][2]['text'] = 'MDS-IB2可用于判定的指标（满足任一即可）'
    g = groups['p51-g1']
    g['options'] = opts(('A', '对于IPSS-R评分>3.5分、年轻、原始细胞增多、伴预后不良染色体核型者首选'), ('C', '地西他滨'), ('D', '蒽环类'), ('E', '延迟MDS向AML转化'), ('F', '对孤立del(5q)疗效好'), ('G', '阿扎胞苷'), ('H', '沙利度胺'), ('I', '阿糖胞苷'))
    answers('p51-g1', ['DI', 'A', 'CEG', 'FH'])
    # There is no G on source page 52: H is monocytic, I is promyelocytic.
    groups['p52-g3']['options'] = [o for o in groups['p52-g3']['options'] if o['key'] != 'G']
    answers('p57-g1', ['BDEGIMO', 'ACFHJKLN', 'K', 'EMO', 'CDELMN', 'BFHJKO', 'AGI', 'AFGI', 'IK'])
    groups['p60-g1']['stems'][6]['answer'] = list('CTc')
    groups['p60-g1']['stems'][-1]['answer'] = list('Xb')
    rename('p60-g1', '血液系统肿瘤特征染色体与免疫表型')
    for s in groups['p58-g3']['stems']:
        s['answerMode'] = '排序'

    additions = [
        group('p47-table1', '血管性血友病与血友病的BT、APTT、PT（表格题）', '血液', ['lecture-31'],
              opts(('A', 'BT延长'), ('B', 'BT正常'), ('C', 'APTT延长'), ('D', 'APTT正常'), ('E', 'PT正常'), ('F', 'PT延长')),
              stems(('血管性血友病', 'ACE'), ('血友病', 'BCE'))),
        group('p58-g4', '霍奇金淋巴瘤病理分类（导图题）', '血液', ['lecture-35'],
              opts(('A', '爆米花细胞'), ('B', '预后最好'), ('C', '与EBV感染相关'), ('D', '典型RS细胞'), ('E', '多种炎细胞混合浸润为背景')),
              stems(('结节性淋巴细胞为主型霍奇金淋巴瘤（NLPHL）', 'AB'), ('经典型霍奇金淋巴瘤（CHL）的共性', 'CDE'))),
    ]
    for g, before in zip(additions, ['p47-g2', 'p59-g1']):
        if g['id'] not in groups:
            at = next(i for i, x in enumerate(payload['groups']) if x['id'] == before)
            payload['groups'].insert(at, g)
            groups[g['id']] = g

    lecture_names = {l['id']: l.get('title', l.get('file', '')) for l in payload['lectures']}
    for gid, (number, page) in LOCATIONS.items():
        g = groups[gid]
        lid = f'lecture-{number:02d}'
        g['lectureIds'] = [lid]
        g['lectureEvidence'] = {'lectureId': lid, 'page': page, 'image': f'med/lecture-pages/{lid}-page-{page:02d}.webp',
                                'title': f'第{number}讲第{page}页：{lecture_names[lid]}', 'description': f'对应第{number}讲第{page}页讲义。'}
        g['reviewState'] = '已按原题页及对应讲义逐项复核'
        for s in g['stems']:
            s['sourceText'] = s['text'] + ' ' + ''.join(s['answer'])
            if s.get('answerMode') not in ('排序', '待核对'):
                s['answerMode'] = '多选' if len(s['answer']) > 1 else '单选'
    from hemolysis_review import repair_hemolysis
    repair_hemolysis(payload)
    # These supplemental pages refer to lecture 56, NOT source workbook page 56.
    for gid in ['lecture56-av-dissociation', 'lecture56-cardiac-enlargement', 'ecg56-g1']:
        if gid in groups:
            groups[gid]['topic'] = '循环'
