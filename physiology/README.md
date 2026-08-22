# 生理学题目提取

本目录保存生理学学成选择题的提取结果，以及依据 2027 考研生理讲义完成的网站同步与勘误记录。

## 文件

- `source/天天学成选择题（生理学）.pdf`：本轮使用的原始题册副本。
- `extracted-questions.json`：结构化题组、选项、小问、原题答案及原页定位。
- `extracted-questions.md`：便于人工通读的题目清单。
- `extraction-audit.json`：原题异常与待复核题组。
- `lecture-reconciliation.json`：160 个题组对应今年讲义页的完整映射，以及修改前后内容。
- `lecture-reconciliation.md`：19 个勘误题组的可读报告。
- `../public/physiology/lecture-pages/`：题组引用的 27 年讲义原页图片，可在网站右侧讲义栏放大查看。

网站使用的数据位于 `src/data/physiology-data.json`，原题页图片位于 `public/physiology/source-pages/`。

## 重新提取

```bash
python3 scripts/extract_physiology_questions.py \
  --source "physiology/source/天天学成选择题（生理学）.pdf" \
  --out physiology/extracted-questions.json \
  --markdown physiology/extracted-questions.md \
  --audit physiology/extraction-audit.json
```

当前解析规则针对本题册的版式：题组编号、公共选项、小问、讲义来源截图、答案。讲义来源截图不在本轮 OCR 范围内。

## 重新核对并生成网站数据

```bash
python3 scripts/build_physiology_content.py \
  --questions physiology/extracted-questions.json \
  --lecture-dir "/Users/ray/Desktop/306/生理学/讲义" \
  --out src/data/physiology-data.json \
  --audit-out physiology/lecture-reconciliation.json \
  --report-out physiology/lecture-reconciliation.md

python3 scripts/audit_physiology_content.py
```
