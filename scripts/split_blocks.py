#!/usr/bin/env python3
"""
将翻译后的场景块拆回 translations.json 格式。
从模型输出中提取 `idx|翻译文本` 对。
"""
import json, sys, re

def main():
    input_path  = sys.argv[1] if len(sys.argv) > 1 else "/tmp/script_blocks_translated.txt"
    trans_path  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/translations.json"
    struct_path = sys.argv[3] if len(sys.argv) > 3 else "/tmp/script_structure.json"

    # 读取已有翻译（保留 slug 等已有翻译）
    try:
        with open(trans_path) as f:
            translations = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        translations = {}

    # 解析翻译后的块
    with open(input_path, encoding='utf-8') as f:
        raw = f.read()

    # 提取格式: idx|type|翻译文本
    pattern = re.compile(r'^(\d+)\|(dialog|action|other|parenthetical|note)\|(.+)$', re.MULTILINE)
    matches = pattern.findall(raw)

    new_count = 0
    for idx, typ, text in matches:
        text = text.strip()
        if text:
            old = translations.get(idx)
            translations[idx] = text
            if old != text:
                new_count += 1

    # 写入
    with open(trans_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=1)

    print(f"✓ 拆分完成: 处理 {len(matches)} 行, 新增/更新 {new_count} 条")
    print(f"  总翻译数: {len(translations)}")

if __name__ == '__main__':
    main()