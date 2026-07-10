#!/usr/bin/env python3
"""
将翻译结果逐段写回 .docx，保留全部格式。
读取 translations.json（idx → 译文），用译文替换对应段落文本。

用法: python3 apply_translations.py <源文件.docx> [translations.json] [输出路径]
"""
import json, sys, os, re
from docx import Document
from docx.shared import Pt, Inches, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from copy import deepcopy


def get_paragraph_text(para):
    """获取段落完整文本（合并所有 run）"""
    return ''.join(run.text for run in para.runs)


def replace_paragraph_text(para, new_text):
    """
    替换段落文本，保持格式。
    策略：用第一个 run 的格式写入新文本，保留其他 run 的格式特征。
    """
    if not para.runs:
        para.add_run(new_text)
        return

    # 保存第一个 run 的格式
    first_run = para.runs[0]
    fmt = {
        'bold': first_run.bold,
        'italic': first_run.italic,
        'size': first_run.font.size,
        'name': first_run.font.name,
        'color': str(first_run.font.color.rgb) if first_run.font.color and first_run.font.color.rgb else None,
    }

    # 清空所有 run
    for run in para.runs:
        run.text = ''

    # 用第一个 run 写新文本，保持格式
    para.runs[0].text = new_text
    if fmt['bold'] is not None:
        para.runs[0].bold = fmt['bold']
    if fmt['italic'] is not None:
        para.runs[0].italic = fmt['italic']
    if fmt['size']:
        para.runs[0].font.size = fmt['size']
    if fmt['name']:
        para.runs[0].font.name = fmt['name']
    if fmt['color']:
        try:
            para.runs[0].font.color.rgb = RGBColor(*bytes.fromhex(fmt['color'].lstrip('#')))
        except Exception:
            pass


def auto_adjust_font_size(para, original_text, new_text):
    """
    自动检测并调整字号。
    如果译文明显变短，保持原字号。
    如果译文明显变长（超过原文 120%），尝试缩小 1-2pt。
    """
    if not para.runs:
        return

    orig_len = len(original_text)
    new_len = len(new_text)
    ratio = new_len / orig_len if orig_len > 0 else 1.0

    # 泰→中：中文通常比泰文短 30-40%，不需要缩小
    # 英→中：中文压缩至 60-70%，不需要缩小
    if ratio <= 1.2:
        return  # 没变长太多，不动

    # 译文明显变长，缩小 1-2pt
    first_run = para.runs[0]
    if first_run.font.size:
        current_size = first_run.font.size.pt
        if current_size > 8:
            new_size = max(current_size - 2, 6)
            first_run.font.size = Pt(new_size)
            return True  # 已缩小

    return False


def main():
    docx_path     = sys.argv[1] if len(sys.argv) > 1 else None
    trans_path    = sys.argv[2] if len(sys.argv) > 2 else "/tmp/translations.json"
    out_path      = sys.argv[3] if len(sys.argv) > 3 else None

    if not docx_path or not os.path.exists(docx_path):
        print("用法: python3 apply_translations.py <源文件.docx> [translations.json] [输出路径]", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(trans_path):
        print(f"✗ 翻译文件不存在: {trans_path}", file=sys.stderr)
        sys.exit(1)

    # 加载翻译结果
    with open(trans_path, encoding='utf-8') as f:
        translations = json.load(f)

    if not translations:
        print("✗ 翻译结果为空", file=sys.stderr)
        sys.exit(1)

    # 打开源文档
    doc = Document(docx_path)

    applied = 0
    skipped = 0
    resized = 0

    for idx, para in enumerate(doc.paragraphs):
        str_idx = str(idx)
        if str_idx in translations:
            orig_text = get_paragraph_text(para)
            new_text = translations[str_idx]

            if not new_text or new_text == orig_text:
                skipped += 1
                continue

            # 替换文本
            replace_paragraph_text(para, new_text)

            # 自动调整字号
            if auto_adjust_font_size(para, orig_text, new_text):
                resized += 1

            applied += 1

    # 确定输出路径
    if not out_path:
        base, ext = os.path.splitext(docx_path)
        out_path = f"{base}_中文版{ext}"

    # 保存
    doc.save(out_path)

    print(f"✓ 翻译应用完成")
    print(f"  ├─ 已应用: {applied} 段")
    print(f"  ├─ 已跳过: {skipped} 段（空/无变化）")
    print(f"  ├─ 已缩字: {resized} 段")
    print(f"  └─ 输出: {out_path}")


if __name__ == '__main__':
    main()