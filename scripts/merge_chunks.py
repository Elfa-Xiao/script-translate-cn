#!/usr/bin/env python3
"""
合并所有 chunk 翻译结果 → translations.json。
用法: python3 merge_chunks.py <chunks_dir> <translations.json>
"""
import json, sys, os, re

def main():
    chunks_dir  = sys.argv[1] if len(sys.argv) > 1 else "/tmp/trans_chunks"
    trans_path  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/translations.json"

    # 加载已有翻译
    try:
        with open(trans_path) as f:
            trans = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        trans = {}

    # 找所有 chunk_done.txt 文件
    done_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('_done.txt')])

    total = 0
    new_count = 0
    for fname in done_files:
        fpath = os.path.join(chunks_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()

        # 提取 idx|type|翻译文本
        pattern = re.compile(r'^(\d+)\|(dialog|action|other|parenthetical|note|meta)\|(.+)$', re.MULTILINE)
        matches = pattern.findall(content)

        chunk_new = 0
        for idx, typ, text in matches:
            text = text.strip()
            if text:
                old = trans.get(idx)
                trans[idx] = text
                if old != text:
                    chunk_new += 1

        total += len(matches)
        new_count += chunk_new
        print(f"  {fname}: {len(matches)} 行, {chunk_new} 条新增/更新")

    with open(trans_path, 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=1)

    print(f"\n✓ 合并完成: {total} 行处理, {new_count} 条新增/更新")
    print(f"  总翻译数: {len(trans)}")
    print(f"  输出: {trans_path}")

if __name__ == '__main__':
    main()