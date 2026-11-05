# 内科题库

## 手机访问

优先使用已部署的个人网页（手机和电脑都可打开）：

<https://neike-306-tiku.phamkhanhs87501.chatgpt.site>

这是私有站点，需要在浏览器中登录与当前 Codex 相同的 ChatGPT/OpenAI 账号；登录后可在任意网络访问。

电脑需要保持运行题库服务。若电脑 IP 变化，用下面命令查看新地址：

```bash
ipconfig getifaddr en0
```

## 启动

```bash
pnpm run dev --host 0.0.0.0 --port 4173
```

## 五科口诀库

顶栏入口现为“速记”，内含“口诀”和“数字”两个分类；旧的口诀链接与收藏继续有效。

## 内外科数字填空与速记

顶栏“数字填空”用于作答，“速记 → 数字”用于集中查阅。两个入口共用
`src/data/numeric-memory-data.json`，支持科目、章节、类别、多关键词搜索，
以及收藏、错题重练和未作答筛选。作答、收藏和错题保存在当前浏览器，暂不跨设备同步。
可在一条知识点的完整展示与对应填空之间跳转。

直接入口：`/?view=numbers`、`/?view=mnemonics&memory=numbers`。
范围接受 `-`、`～`、`至` 等写法；单位和比较符号保留在题干中。
每条知识点均附讲义文件名、PDF 页码及可展开、放大的原页图片。
含表格条目按 PDF 单元格位置恢复行列与表头（当前 164 条、189 处表格），电脑端显示对照表，
手机端按疾病或对照项目分组并显示字段名称。原始知识点 ID、数字答案和空格编号保留，原有作答记录继续有效。

数字填空沿用题库快捷键：A/D 上一空或下一空，W/E 上一行或下一行（保留空格列），
↑/↓ 切换作答行，←/→ 上一条或下一条，Enter 提交或重新作答，
单按 Shift 打开或关闭讲义原页弹窗（Esc 也可关闭），单按 Option/Alt 收藏，⌘/Ctrl+K 搜索。
方向键在输入框内保留光标编辑功能；搜索、筛选、输入法和修饰键组合不会触发练习操作。

当前来源为桌面 2027 内科 57 份、外科 38 份分章讲义，共 545 条知识点、1588 个数字空。
提取范围是核心精讲、专题串联、易错小结与考点补充的文字层，保留完整编号段落和适用条件；
真题选项、仅存在于图片中的数字不自动转成答案。范围、剂量、时间、比值和阈值自动生成填空，
不能据此声称已人工穷尽所有图表考点。原讲义围术期第 2 页的“1.4 天、2.7 天”表述含义不明，
已明确标注并排除出答案。

重新导入：`python3 scripts/build_numeric_memory.py --source <306目录> --render`。
需要 pypdf、pdfplumber、Pillow 和 Poppler；`--render` 会补齐缺失的原页图片。
导入自动调用 `scripts/layout_numeric_tables.py`；也可单独运行该脚本更新已有知识点的表格布局。
校验：`node --test tests/numeric-memory.test.mjs`。

### 原有口诀库说明

在顶栏选择“口诀”，复用原搜索框查找口诀、疾病或知识点；首页按科目、系统／章节展示目录。搜索区分口诀名称与知识点，名称直接命中优先；卡片仅展示经过精简的对应关系及必要条件，支持当前浏览器收藏。
直接入口：`/?view=mnemonics`。可附加 `q` 和 `mnemonicSubject` 参数。

数据来自五科现有 Notion 口诀文档，原始 2557 条，经明确重复合并及无效边注清理后为 2363 条；跨科重复保留多个分类入口，搜索只呈现一条。来源标识、合并记录和各科条数保存在 `src/data/mnemonics-data.json`。更新时将五页正文导出为 `mnemonic-source-{subject}.md`，再运行 `python3 scripts/import_mnemonics.py <导出目录>`；去重及排除清单保存在 `src/data/mnemonic-consolidation.json`；逐条修订保存在 `src/data/mnemonic-curation.json`，导入会调用 `scripts/curate_mnemonics.py`。搜索和导入完整性校验：`node --test tests/mnemonics.test.mjs`。

如需在本地调试，仍可使用上面的局域网方式；本地服务必须保持电脑运行。
