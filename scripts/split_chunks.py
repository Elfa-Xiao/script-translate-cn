#!/usr/bin/env python3
"""
将合并后的场景块切成 N 份，每份交给一个子 agent 并行翻译。
用法: python3 split_chunks.py <script_blocks.txt> <chunks_dir> <num_chunks>
"""
import json, sys, os, math, re

def main():
    blocks_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/script_blocks.txt"
    out_dir     = sys.argv[2] if len(sys.argv) > 2 else "/tmp/trans_chunks"
    num_chunks  = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    os.makedirs(out_dir, exist_ok=True)

    with open(blocks_path, encoding='utf-8') as f:
        content = f.read()

    # 按场景分割（以 ## 场景 开头的行为分割点）
    scenes = re.split(r'\n(?=## 场景)', content)
    # 去掉首尾空
    scenes = [s.strip() for s in scenes if s.strip()]

    # 均匀分配到 N 个 chunk
    chunk_size = math.ceil(len(scenes) / num_chunks)
    chunks = [scenes[i:i+chunk_size] for i in range(0, len(scenes), chunk_size)]

    scene_counts = []
    for i, chunk in enumerate(chunks):
        chunk_text = '\n\n'.join(chunk)
        out_path = os.path.join(out_dir, f"chunk_{i+1}.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(chunk_text)
        # 统计行数
        lines = chunk_text.count('\n') + 1
        scene_counts.append((i+1, len(chunk), lines))
        print(f"  chunk_{i+1}.txt: {len(chunk)} 场景, ~{lines} 行 → {out_path}")

    # 输出总览
    print(f"\n✓ 切割完成: {len(scenes)} 场景 → {len(chunks)} 个 chunk")
    print(f"  输出目录: {out_dir}")

    # 生成调用信息
    print(f"\n--- 翻译指令 ---")
    for i, sc, ln in scene_counts:
        print(f"\n子 agent {i}/{len(chunks)}:")
        print(f"  读取: /tmp/trans_chunks/chunk_{i}.txt")
        print(f"  翻译其中的所有 {sc} 个场景 (~{ln} 行)")
        print(f"  输出: /tmp/trans_chunks/chunk_{i}_done.txt")
        print(f"  格式: 保留 idx|type|译文 不变")

if __name__ == '__main__':
    main()