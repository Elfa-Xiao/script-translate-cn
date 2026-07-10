#!/usr/bin/env python3
"""
将剧本翻译条目按场景合并为自然块，让模型获得完整上下文。
用法: python3 merge_blocks.py <script_structure.json> <output.txt>
"""
import json, sys

def main():
    struct_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/script_structure.json"
    out_path    = sys.argv[2] if len(sys.argv) > 2 else "/tmp/script_blocks.txt"

    with open(struct_path) as f:
        rows = json.load(f)

    # 场景分组: 所有 slug/format 行（含已翻译的）都是场景分隔符
    scenes = []
    current_slug = None
    current_lines = []

    for r in rows:
        is_slug = r['type'] in ('slug', 'format')
        if is_slug and current_slug is not None:
            # 保存上一个场景
            if current_lines:
                scenes.append((current_slug, current_lines))
            current_slug = r
            current_lines = []
        elif is_slug:
            current_slug = r
            current_lines = []
        elif r['needs_translation']:
            current_lines.append(r)

    # 最后一个场景
    if current_slug and current_lines:
        scenes.append((current_slug, current_lines))

    # 输出合并块
    lines_out = []
    for scene_num, (slug, scene_rows) in enumerate(scenes, 1):
        slug_text = slug['text'].strip() if slug else ""
        lines_out.append(f"## 场景 {scene_num}: {slug_text}")
        lines_out.append("")

        for r in scene_rows:
            idx = r['idx']
            typ = r['type']
            txt = r['text'].strip()
            # 对话行简化为角色名:台词，更自然
            if typ == 'dialog':
                # 如果是角色名:台词格式（角色名会在上一条居中的行）
                lines_out.append(f"{idx}|{typ}|{txt}")
            else:
                lines_out.append(f"{idx}|{typ}|{txt}")

        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines_out))

    total_lines = sum(len(s) for _, s in scenes)
    print(f"✓ 合并完成: {scene_num} 个场景, {total_lines} 行")
    print(f"  输出: {out_path}")

if __name__ == '__main__':
    main()