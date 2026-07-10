---
name: translate-cn
description: 外语→中文翻译本地化技能。当用户要求翻译文件（PDF、Word、纯文本等）、转换文档语言时使用。支持源语言：英语、泰语、马来语、印尼语。自动检测文件格式选择对应管线（Word → 直接编辑保留可编辑性；PDF/图片 → 覆盖翻译保留视觉排版；纯文本 → 直接翻译）。特别适用于剧本格式的 Word 文件——保留所有格式元素（对齐、缩进、间距、角色名称位置等）。
metadata:
  version: 1.1.0
---

# 翻译技能 v1.1（外语→中文）

## 核心原则

### 翻译范围

| ✅ 必须翻译 | ❌ 保留原文（拉丁字母） | ⚠️ 音译/转写（非拉丁字母） |
|---|---|---|
| 正文段落、剧情描述、对话台词、场景说明 | 拉丁字母人名、角色名（FALIQ, ELIZAD） | 非拉丁字母人名 → 优先用英文转写，无通用英文转写时用中文音译 |
| 标签/分类/标题的主体内容 | 作品名/书名（拉丁字母） | 非拉丁字母作品名 → 用粉丝圈通用英文转写，无则中文音译 |
| 统计数据行的描述文字 | 品牌名/平台名（TikTok, Netflix 等） | 同上 |
| 说明性文字 | 邮箱、网址、电话 | — |
| 通用地点词（卧室、医院、厨房等） | 奖项/榜单名（USA Today Bestseller 等） | — |
| 场景标题中的时间/过渡词 | 专有缩写/术语（YA, Franchise 等） | — |
| Logo/图片上的文字 | — | 图片上的非拉丁文字 → 翻译成中文 |

### 专有名词分级保留规则

专有名词是否保留，**取决于书写系统而非语言**：

| 书写系统 | 处理方式 | 示例 |
|---|---|---|
| **拉丁字母**（英/马/印/法/德等） | 保留原文 | FALIQ, ELIZAD, TikTok, Instagram |
| **泰文/高棉文/缅文** | 有英文转写 → 用英文转写；无 → 中文音译 | โจ → JO, วิว → 薇 |
| **西里尔字母**（俄/乌/保等） | 有通用英文转写 → 用英文转写；无 → 中文音译 | Дмитрий → Dmitry / 德米特里 |
| **阿拉伯字母**（阿/波/乌尔都等） | 同上 | محمد → Mohammed / 穆罕默德 |
| **中日韩汉字** | 保留原文 | 中文名、日文汉字名保留 |
| **日文假名** | 罗马音转写或中文音译 | たかし → Takashi / 隆史 |

**判断标准**：以目标读者（中文用户）能否理解为底线。
- 拉丁字母写的人名 → 读者能读能搜，保留
- 非拉丁字母写的人名 → 读者完全无法辨认，必须转写
- 优先使用**粉丝圈公认的英文转写**（如泰BL圈中 JO / Ming / Ing妈 / Vudee哥 已经固化），搜资源、查弹幕、追推特都能对上号
- 无公认英文转写时才用中文音译

### 场景标题（SLUG LINE）翻译规则

| SLUG 元素 | 翻译 | 示例 |
|---|---|---|
| INT. / EXT. / EST. / INTERCUT | 内景 / 外景 / 定场 / 交叉剪辑 | INT. HOSPITAL → 内景. 医院 |
| 通用地点词 | 翻译成中文 | DEWAN KULIAH → 讲堂, RUANG TAMU → 客厅 |
| 时间指示 | 翻译成中文 | SIANG → 白天, MALAM → 晚上, PAGI → 早上 |
| 过渡词 | 翻译成中文 | CUT TO → 切至, FADE IN → 淡入 |
| MONTAGE / FLASHBACK / INSERT | 翻译成中文 | 蒙太奇 / 闪回 / 插入 |
| SFX | 翻译成中文 | 音效 |
| NOTE 标签 | 标签保留，内容翻译 | NOTE: ELIZAD AND FALIQ → 注：ELIZAD 和 FALIQ |

**通用地点词一定要翻**（卧室、办公室、医院、咖啡馆、餐厅、厨房），否则读者缺信息。
**专有地名中的特定名称成分保留**（如"ABC Hospital" → "ABC 医院"）。

### 语言适配规则

| 翻译方向 | 长度变化 | 字号处理 |
|---|---|---|
| 英→中 | 中文压缩至原文约 60-70% | 保持原字号 |
| 泰→中 | 中文比泰文短 30-40% | 保持原字号，多余空间居中 |
| 马/印→中 | 中文略短 | 保持原字号 |
| 中→外（逆向） | 外文可能变长 | 超框时缩小 1-2pt |

---

## 输入格式检测与管线选择

```
输入文件 → 检测扩展名
  ├── .docx / .doc ───────→ A. Word 直接编辑管线（推荐，保留可编辑性）
  ├── .pdf / .png / .jpg ─→ B. PDF/图片覆盖翻译管线（保留视觉排版）
  └── .txt / 纯文本 ──────→ C. 纯文本直接翻译
```

---

## 管线 A：Word 直接编辑管线（剧本首选）

### 核心思路

剧本**行数巨大但按场景分组**，逐行盲翻会导致上下文缺失和效率低下。

**方案**：场景合并 → 并行翻译 → 合并写回。

### 流程

```
源 .docx
  │
extract_script.py    ← 提取段落结构（识别 slug/character/dialog/action）
  │
merge_blocks.py      ← 按场景合并（~1000 行 → ~50 个场景块）
  │
split_chunks.py      ← 切为 N 块（推荐 4 块，每块 ~250 行）
  │
  ├── sub-agent 1 → chunk_1_done.txt
  ├── sub-agent 2 → chunk_2_done.txt   ← 并行翻译
  ├── sub-agent 3 → chunk_3_done.txt
  └── sub-agent 4 → chunk_4_done.txt
  │
merge_chunks.py      ← 合并 → translations.json
  │
apply_translations.py ← 逐段写回 .docx，保留全部格式
  │
输出：原文件名_中文版.docx
```

### 详细步骤

```bash
# 1. 提取段落结构
python3 scripts/extract_script.py <源文件.docx>

# 2. 合并为场景块
python3 scripts/merge_blocks.py

# 3. 切割为并行 chunk（推荐 4 块）
python3 scripts/split_chunks.py /tmp/script_blocks.txt /tmp/trans_chunks 4

# 4. 子 agent 翻译每块（保持 idx|type|译文 格式不变）
# 5. 合并翻译结果
python3 scripts/merge_chunks.py /tmp/trans_chunks /tmp/translations.json

# 6. 写回 .docx
python3 scripts/apply_translations.py <源文件.docx>
```

### 场景块格式

```
## 场景 1: OVER BLACK.

8|dialog|Kalau kita dua-dua dah
9|dialog|kahwin nanti kan,
10|dialog|kau lupa aku tak?

---

## 场景 2: INT. UNIVERSITI / DEWAN KULIAH - SIANG.

15|action|Dewan kuliah dipenuhi pelajar yang tengah berbual dan belajar bersama.
```

- `## 场景 N: 标题` 提供上下文供模型理解整场对话
- `idx|type|原文` 每行一个翻译条目
- `---` 场景分隔线

### 性能预期

| 剧集规模 | 翻译条目 | 场景数 | 并行度 | 总耗时 |
|---|---|---|---|---|
| 1 集标准 | ~1000 行 | ~50 场 | 4 个子 agent | ~5 分钟 |
| 1 集大型 | ~2000 行 | ~80 场 | 6 个子 agent | ~8 分钟 |
| 10 集全季 | ~10000 行 | ~500 场 | 逐个处理 | ~50 分钟 |

### 剧本格式保护

| 剧本元素 | 保护措施 |
|---|---|
| 场景标题（全大写、左对齐、加粗） | 不改变对齐和大小写 |
| 角色名称（居中、全大写） | 翻译对话时角色名保留原文 |
| 对白（左缩进、宽度受限） | 保持缩进和段落间距 |
| 括号提示（左对齐、缩进更深） | 保持缩进层级 |
| 动作描述（左对齐、通栏） | 保持段落样式 |
| 换页/分页符 | 维持原位置 |

### 字号适配

- 译文放入后检测段落宽度，明显超出原文区域时缩小 1-2pt
- 对话段落保持原字号不动

---

## 管线 B：PDF 覆盖翻译管线（图片/不可编辑文档）

适用：带复杂排版的 PDF（Canva、Keynote 导出等）、图片格式文档、扫描件等无法直接编辑的文件。

流程：
1. `pdfinfo` + PyMuPDF 提取页面尺寸和文本位置坐标
2. 每页转 PNG（默认 200 DPI）
3. 对每个翻译条目：在原坐标处绘制半透明深色背景 + 白字中文
4. 合成图片 → 输出 PDF

详细执行：`scripts/translate_pdf_overlay.py`

---

## 管线 C：纯文本直接翻译

适用：无格式要求的纯文本文件（.txt、.md 等）。

流程：读取源文本 → 直接翻译全文 → 输出译文。专有名词规则同上。

---

## 脚本清单

| 脚本 | 用途 | 依赖 |
|---|---|---|
| `scripts/extract_script.py` | 提取剧本段落结构 | python-docx |
| `scripts/merge_blocks.py` | 按场景合并翻译条目 | — |
| `scripts/split_chunks.py` | 切分为并行 chunk | — |
| `scripts/merge_chunks.py` | 合并 chunk 翻译结果 | — |
| `scripts/apply_translations.py` | 逐段写回 .docx | python-docx |
| `scripts/translate_pdf_overlay.py` | PDF/图片覆盖翻译 | Pillow, PyMuPDF, pdftoppm |
| `scripts/translate_docx.py` | 旧版：Word 逐段翻译（单线程） | python-docx |

---

## 输出格式

| 输入 | 输出 |
|---|---|
| .pdf / .png / .jpg | 翻译后 .pdf（覆盖翻译版） |
| .docx | 翻译后 .docx（可编辑版） |
| .txt / 纯文本 | 翻译后文本 |

文件名：`原文件名_中文版.{扩展名}`

---

## 必要工具检查

```bash
# PDF/图片管线
which pdfinfo pdftoppm          # poppler-utils
python3 -c "import fitz"        # PyMuPDF
python3 -c "from PIL import Image"  # Pillow

# Word 管线
python3 -c "import docx"        # python-docx

# 中文字体
fc-list :lang=zh | head -5
```

缺少依赖时优先用 pip 安装，系统包用 apt。

---

## 优先级

1. **格式完整 > 翻译精确** — 宁可译文略生硬，不可破坏排版结构（尤其是剧本格式）
2. **场景上下文 > 盲翻逐行** — 合并场景再翻译，译文衔接更自然
3. **输出可用性 > 视觉完美** — Word 版保留可编辑性优先，PDF 版保留视觉还原度优先
4. **专有名词分级处理** — 拉丁字母保留原文，非拉丁字母优先用英文转写，无通用转写时用中文音译

---

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.1 | 2026-07-10 | 新增专有名词分级保留规则（按书写系统区分）；补全 extract_script.py 和 apply_translations.py 脚本；精简全文结构 |
| v1.0 | 2026-07-09 | 新增场景合并 + 并行翻译流水线；新增 SLUG LINE 翻译规则；新增纯文本管线；脚本体系升级 |
| v0.2 | 2026-07-09 | 新增马来/印尼语支持；新增 Word 直接编辑管线 |
| v0.1 | — | 初始版本：PDF 覆盖翻译 + 英→中 |