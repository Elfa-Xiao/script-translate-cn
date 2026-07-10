#!/usr/bin/env python3
"""
Word (.docx) 外语→中文翻译脚本：直接编辑文本，保留完整格式。
适用于剧本、报告、方案等格式敏感的 Word 文件。

用法：python3 translate_docx.py <input.docx> <lang> [output.docx]
      lang: en / th / ms / id

依赖：pip install python-docx
"""

import sys, os, re
from docx import Document
from docx.shared import Pt, Emu
from copy import deepcopy


# 每个剧本段落最大字符数（超出考虑微调字号）
PARAGRAPH_MAX_CHARS = 200


def get_lang_info(lang_code):
    """返回语言信息：语系、文字方向等"""
    info = {
        "en": {"name": "English", "family": "germanic", "direction": "ltr"},
        "th": {"name": "Thai", "family": "taic", "direction": "ltr"},
        "ms": {"name": "Malay", "family": "austronesian", "direction": "ltr"},
        "id": {"name": "Indonesian", "family": "austronesian", "direction": "ltr"},
    }
    return info.get(lang_code, info["en"])


def is_slug_line(para):
    """判断是否为剧本场景标题 (SLUG LINE)"""
    text = para.text.strip()
    if not text:
        return False
    # 场景标题特征：全大写、以 INT/EXT/INT./EXT. 开头
    slug_patterns = [
        r'^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s',
        r'^第\d+场',
        r'^SCENE\s+\d+',
    ]
    for p in slug_patterns:
        if re.match(p, text, re.IGNORECASE):
            return True
    # 如果段落全是大写且较短，可能是角色名或场景标题
    if text.isupper() and len(text.split()) <= 8:
        first_words = text.split()[:3]
        common_slug = ['INT', 'EXT', 'INT/EXT', 'I/E', 'SCENE', 'CUT', 'FADE',
                       'DISSOLVE', 'SMASH', 'MATCH']
        for w in first_words:
            clean = w.rstrip('.:')
            if clean in common_slug:
                return True
    return False


def is_character_cue(para, prev_para=None):
    """判断是否为剧本角色名称行"""
    text = para.text.strip()
    if not text or len(text) > 40:
        return False
    # 角色名称特征：全大写、居中、单行、前面通常是空白行或场景标题
    if text.isupper() and len(text.split()) <= 4:
        # 检查对齐方式
        if para.alignment is not None:
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                return True
        # 如果是全大写且前面紧接空行或场景标题
        return True
    return False


def should_skip_paragraph(para):
    """判断此段落应跳过不翻译"""
    text = para.text.strip()
    if not text:
        return True  # 空行不处理
    # 纯数字
    if text.isdigit():
        return True
    # 纯英文且全大写且很短 → 角色名/场景标题
    if text.isupper() and len(text.split()) <= 4 and re.match(r'^[A-Z\s\.\,\!\?\:\;]+$', text):
        return True  # 保留角色名
    return False


def should_keep_original(text):
    """判断是否为应保留原文的专有名词段落"""
    # 如果整段都是英文/符号且无中文字符，且不是纯描述性文字
    if not re.search(r'[\u4e00-\u9fff]', text):
        # 纯英文段落处理
        return False  # 仍需要翻译，除非被其他规则拦截
    return False


def translate_paragraph_runs(doc, para_idx, lang):
    """翻译单个段落。这里用占位逻辑，实际翻译由主流程的翻译回调完成。"""
    pass


def adjust_font_size_if_needed(doc, para_idx, original_text, translated_text, lang):
    """
    如果译文明显比原文长，缩小字号 1-2pt。
    剧本对话段落保持原字号。
    """
    # 对话段落特征：较长、非全大写、不是场景标题
    para = doc.paragraphs[para_idx]
    text = para.text.strip()

    if not text:
        return

    # 判断是否为剧本对话：缩进较大或前有角色名
    fmt = para.paragraph_format
    left_indent = fmt.left_indent

    ratio = len(translated_text) / max(len(original_text), 1)

    # 翻译变长超过 30% → 考虑缩小字号
    if ratio > 1.3 and left_indent is not None and left_indent > Pt(36):
        # 对话段落 - 微调
        for run in para.runs:
            if run.font.size:
                current = run.font.size.pt
                run.font.size = Pt(max(current - 1, 9))
    elif ratio > 1.5:
        # 显著变长
        for run in para.runs:
            if run.font.size:
                current = run.font.size.pt
                run.font.size = Pt(max(current - 1.5, 8))


def apply_translation_to_docx(input_path, output_path, translations, lang):
    """
    将翻译结果写入 Word 文档。

    translations: list of (paragraph_index, translated_text)
    """
    doc = Document(input_path)

    # 收集原始文本长度以做字号适配
    original_texts = {}
    for idx, text in translations:
        original_texts[idx] = doc.paragraphs[idx].text if idx < len(doc.paragraphs) else ""

    # 逐段替换文字（只替换 run 的 text，保留格式）
    for idx, trans_text in translations:
        if idx >= len(doc.paragraphs):
            continue

        para = doc.paragraphs[idx]

        # 如果段落应该跳过（角色名/场景标题等），不变
        if should_skip_paragraph(para):
            continue

        # 保留角色名行
        if is_character_cue(para):
            continue

        # 替换文字：清除原有 runs 的文字，填入译文
        if para.runs:
            # 保留第一个 run 的格式写入译文
            first_run = para.runs[0]
            first_run.text = trans_text
            # 清空其他 run
            for run in para.runs[1:]:
                run.text = ""
        else:
            # 没有 runs 的情况
            para.add_run(trans_text)

        # 字号适配
        if idx in original_texts:
            adjust_font_size_if_needed(doc, idx, original_texts[idx], trans_text, lang)

    doc.save(output_path)
    print(f"✓ 已保存: {output_path}")
    return output_path


def extract_text_structure(input_path):
    """提取 Word 文档的文本结构用于翻译参考"""
    doc = Document(input_path)
    result = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        fmt = para.paragraph_format
        info = {
            "index": i,
            "text": text,
            "alignment": str(para.alignment) if para.alignment else None,
            "left_indent": str(fmt.left_indent) if fmt.left_indent else None,
            "first_line_indent": str(fmt.first_line_indent) if fmt.first_line_indent else None,
            "runs_count": len(para.runs),
            "is_slug": is_slug_line(para),
            "is_character": should_skip_paragraph(para) and text.isupper(),
            "bold": any(r.bold for r in para.runs) if para.runs else False,
            "font_size": para.runs[0].font.size.pt if para.runs and para.runs[0].font.size else None,
        }
        result.append(info)
    return result


def main():
    if len(sys.argv) < 3:
        print("用法: python3 translate_docx.py <input.docx> <lang> [output.docx]")
        print("      lang: en / th / ms / id")
        sys.exit(1)

    input_path = sys.argv[1]
    lang = sys.argv[2]

    if lang not in ("en", "th", "ms", "id"):
        print(f"⚠ 不支持的语言: {lang}，支持: en, th, ms, id")
        sys.exit(1)

    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"{base}_中文版.docx"

    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    # 提取文档结构
    structure = extract_text_structure(input_path)
    total_paras = len([s for s in structure if s["text"]])
    print(f"输入: {input_path}")
    print(f"语言: {lang} → 中文")
    print(f"段落: {total_paras} 段（含 {len([s for s in structure if s['is_slug']])} 场景标题，"
          f"{len([s for s in structure if s['is_character']])} 角色名）")
    print(f"输出: {output_path}")
    print("\n段落文本摘要（用于翻译参考）:")
    for s in structure:
        marker = ""
        if s["is_slug"]:
            marker = " [场景]"
        elif s["is_character"]:
            marker = " [角色]"
        print(f"  [{s['index']}]{marker} {s['text'][:80]}")

    print("\n⚠ 请逐段提供中文翻译，然后调用 apply_translation_to_docx() 写入文档。")


if __name__ == "__main__":
    main()