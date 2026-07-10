# script-translate-cn
多语种剧本中文翻译助手，针对跨国剧本、创意写作、小说翻译、出海短剧文本保留格式与可读性的翻译流水线
支持英语、泰语、马来语、印尼语至中文的翻译，适用于影视剧本、文学作品、短剧等创作场景。

---

## 适用场景

- **影视创作**：海外剧本（英/泰/马/印尼）本地化为中文，保留剧本格式与可编辑性，便于国内团队协作开发
- **小说本地化**：跨语种文学作品翻译，支持纯文本和多格式文档
- **出海短剧制作**：中文剧本翻译为外语，支持逆向翻译流程，适配海外拍摄需求
- **字幕/翻译组**：批量处理剧本格式文档，提升翻译效率与一致性

## 核心特色

### 1. 保留剧本格式，保证可读性

剧本翻译最怕的不是"翻不翻得对"，而是"翻完之后格式乱了"。本工具在翻译过程中完整保留：
- 场景标题对齐方式、加粗、全大写样式
- 角色名居中位置、对话缩进层级
- 括号提示、动作描述等排版元素
- 字体、字号、段落间距等样式细节

译文写回后，打开即用，无需二次排版。

### 2. 场景合并翻译（而非逐行盲翻）

剧本按场景分组，每场戏内的对话有语气连贯性。逐行翻译会丢失上下文，导致语气割裂。

本工具将翻译条目按场景合并为自然段落，再交给语言模型处理。对比：

| 方式 | 翻译质量 | 效率 |
|---|---|---|
| 逐行盲翻 | 上下文丢失，对话语气割裂 | 1000 行 → token 爆炸 |
| 场景合并+并行翻译 | 上下文完整，对话连贯 | 4 个子 agent 并行，~5 分钟 |

### 3. 专有名词分级保留

根据书写系统自动决定专有名词的处理方式，避免非拉丁字母文字在译文中变成"天书"：

| 书写系统 | 处理方式 | 示例 |
|---|---|---|
| 拉丁字母 | 保留原文 | FALIQ, ELIZAD, TikTok |
| 泰文/高棉文 | 优先用粉丝圈英文转写，无则中文音译 | โจ → JO, วิว → 薇 |
| 西里尔字母 | 同上 | Дмитрий → Dmitry / 德米特里 |
| 中日韩汉字 | 保留原文 | 中文名、日文汉字名保留 |

### 4. 三种管线，按需选择

```
输入文件 → 检测扩展名
  ├── .docx / .doc ───────→ Word 直接编辑管线（保留可编辑性，推荐）
  ├── .pdf / .png / .jpg ─→ PDF/图片覆盖翻译管线（保留视觉排版）
  └── .txt / 纯文本 ──────→ 纯文本直接翻译
```

---

## 快速开始

### 环境要求

- Python 3.8+
- 安装依赖

```bash
pip install python-docx
```

PDF 管线额外依赖：

```bash
pip install PyMuPDF Pillow
apt install poppler-utils    # Linux
```

### 使用流程（Word 剧本管线）

```bash
# 1. 提取段落结构
python3 scripts/extract_script.py 源文件.docx

# 2. 按场景合并
python3 scripts/merge_blocks.py

# 3. 切分为并行 chunk
python3 scripts/split_chunks.py /tmp/script_blocks.txt /tmp/trans_chunks 4

# 4. 翻译每块（交给语言模型处理，保持 idx|type|译文 格式）
# 5. 合并翻译结果
python3 scripts/merge_chunks.py /tmp/trans_chunks /tmp/translations.json

# 6. 写回翻译后的文档
python3 scripts/apply_translations.py 源文件.docx
```

输出文件：`源文件_中文版.docx`

---

## 文件结构

```
script-translate-cn/
├── SKILL.md                          # 完整技能说明
├── README.md
├── LICENSE
└── scripts/
    ├── extract_script.py             # 提取剧本段落结构
    ├── merge_blocks.py               # 按场景合并翻译条目
    ├── split_chunks.py               # 切分为并行 chunk
    ├── merge_chunks.py               # 合并翻译结果
    ├── apply_translations.py         # 逐段写回 .docx
    ├── translate_pdf_overlay.py      # PDF/图片覆盖翻译
    └── translate_docx.py             # 旧版：逐段翻译（单线程）
```

---

## 脚本依赖

| 脚本 | 依赖 |
|---|---|
| extract_script.py | python-docx |
| merge_blocks.py | 无（纯标准库） |
| split_chunks.py | 无（纯标准库） |
| merge_chunks.py | 无（纯标准库） |
| apply_translations.py | python-docx |
| translate_pdf_overlay.py | PyMuPDF, Pillow, poppler-utils |
| translate_docx.py | python-docx |

---

## 许可证

[MIT](./LICENSE)

Copyright (c) 2026 肖婧澜 (Elfa Xiao)
