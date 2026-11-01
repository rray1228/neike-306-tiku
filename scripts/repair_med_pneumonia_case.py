"""Keep the pneumonia treatment question with its source case (questions 2–4)."""
def repair_pneumonia_case(data):
    groups = data['groups']
    base = next(g for g in groups if g['id'] == 'med-teacher-02-02-03')
    treatment = next((g for g in groups if g['id'] == 'med-teacher-02-04'), None)
    if treatment is None:
        return
    for option in treatment['options']:
        base['options'].append({**option, 'key': 'q4-' + option['key'],
                                'displayKey': option.get('displayKey', option['key']), 'category': '第 4 题选项'})
    stem = treatment['stems'][0]
    base['stems'].append({**stem, 'answer': ['q4-' + key for key in stem['answer']], 'optionCategory': '第 4 题选项'})
    base.update(title='第 2–4 题共用题干', sourceQuestion='2–4', sharedQuestionCount=3,
                answerRevision='pneumonia-case-v1')
    base['sourceText'] += ' ' + treatment['sourceText']
    groups.remove(treatment)
    data['meta']['groupCount'] = len(groups)
