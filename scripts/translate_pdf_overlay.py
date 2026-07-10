#!/usr/bin/env python3
"""
PDF 英译中覆盖翻译脚本
用法：python3 translate_pdf_overlay.py <input.pdf> <translations.py> [output.pdf] [--dpi 200]

translations.py 应定义 TRANSLATIONS 字典，格式见 SKILL.md

依赖：pip install Pillow pymupdf
"""

import sys, os, json
from PIL import Image, ImageDraw, ImageFont
import fitz

# Default Chinese fonts - try each in order
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    # Fallback: try fc-list
    import subprocess
    result = subprocess.run(["fc-list", ":lang=zh", "-f", "%{file}\n"],
                            capture_output=True, text=True, timeout=5)
    fonts = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    if fonts:
        return fonts[0]
    raise FileNotFoundError("No Chinese font found. Install noto-cjk or wqy-microhei.")


def get_page_info(pdf_path):
    """Extract text blocks with positions from each page."""
    doc = fitz.open(pdf_path)
    pages_data = []
    for i, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        image_blocks = []
        for block in blocks:
            if block["type"] == 0:  # text
                for line in block["lines"]:
                    text = "".join([s["text"] for s in line["spans"]])
                    if text.strip():
                        bbox = [round(v, 1) for v in line["bbox"]]
                        font_size = round(line["spans"][0]["size"], 1)
                        text_blocks.append({
                            "bbox": bbox,
                            "text": text,
                            "font_size": font_size,
                        })
            elif block["type"] == 1:  # image
                image_blocks.append({
                    "bbox": [round(v, 1) for v in block["bbox"]],
                })
        pages_data.append({
            "page_num": i + 1,
            "size": [page.rect.width, page.rect.height],
            "text_blocks": text_blocks,
            "image_blocks": image_blocks,
        })
    doc.close()
    return pages_data


def main():
    if len(sys.argv) < 3:
        print("用法: python3 translate_pdf_overlay.py <input.pdf> <translations.py> [output.pdf] [--dpi 200]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    trans_file = sys.argv[2]
    output_pdf = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
    dpi = 200

    for arg in sys.argv:
        if arg.startswith("--dpi"):
            try:
                dpi = int(arg.split("=")[-1])
            except ValueError:
                pass

    if not output_pdf:
        base = os.path.splitext(os.path.basename(input_pdf))[0]
        output_pdf = f"{base}_中文版.pdf"

    # Load translations
    trans_globals = {}
    exec(open(trans_file).read(), trans_globals)
    translations = trans_globals.get("TRANSLATIONS", {})

    # Get page info
    doc = fitz.open(input_pdf)
    total_pages = len(doc)
    pdf_w = doc[0].rect.width
    pdf_h = doc[0].rect.height
    doc.close()

    scale = dpi / 72
    img_w = int(pdf_w * scale)
    img_h = int(pdf_h * scale)

    print(f"输入: {input_pdf} ({total_pages} 页, {pdf_w:.0f}x{pdf_h:.0f})")
    print(f"DPI: {dpi}, 图片尺寸: {img_w}x{img_h}")
    print(f"输出: {output_pdf}")
    print(f"翻译条目: {sum(len(v) for v in translations.values())} 条")
    print()

    # Find font
    font_path = find_font()
    print(f"使用字体: {font_path}")

    # Convert PDF pages to images and overlay translations
    # Use pdftoppm for conversion
    import tempfile, subprocess
    tmpdir = tempfile.mkdtemp(prefix="pdf_translate_")
    page_images = []

    for page_idx in range(total_pages):
        print(f"\r正在处理第 {page_idx+1}/{total_pages} 页...", end="")

        # Convert page to PNG
        png_path = os.path.join(tmpdir, f"page-{page_idx+1:03d}.png")
        subprocess.run([
            "pdftoppm", "-png", "-r", str(dpi),
            "-f", str(page_idx + 1), "-l", str(page_idx + 1),
            input_pdf, os.path.join(tmpdir, f"page-{page_idx+1:03d}")
        ], capture_output=True, timeout=60)

        # Find the actual file
        png_files = [f for f in os.listdir(tmpdir) if f.startswith(f"page-{page_idx+1:03d}-") and f.endswith(".png")]
        if png_files:
            png_path = os.path.join(tmpdir, png_files[0])
        else:
            # pdftoppm with -f/-l may produce non-suffixed names
            simple_path = os.path.join(tmpdir, f"page-{page_idx+1:03d}.png")
            if os.path.exists(simple_path):
                png_path = simple_path
            else:
                print(f"\n  ⚠ 第 {page_idx+1} 页转换失败，跳过")
                continue

        img = Image.open(png_path).convert("RGBA")

        # Apply translations for this page
        if page_idx in translations:
            trans_list = translations[page_idx]
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            for trans_entry in trans_list:
                bbox, text, font_size_pt = trans_entry[:3]
                x0 = int(bbox[0] * scale)
                y0 = int(bbox[1] * scale)
                x1 = int(bbox[2] * scale)
                y1 = int(bbox[3] * scale)
                w = x1 - x0
                h = y1 - y0

                px_size = int(font_size_pt * scale)
                try:
                    font = ImageFont.truetype(font_path, px_size)
                except:
                    font = ImageFont.load_default()

                lines = text.split("\n")
                line_height = int(font_size_pt * scale * 1.3)
                pad = int(8 * scale)

                # Draw semi-transparent dark background
                draw.rectangle(
                    [x0 - pad, y0 - pad, x1 + pad, y1 + pad],
                    fill=(0, 0, 0, 200)
                )

                # Draw centered text
                y_pos = y0
                for line in lines:
                    bbt = draw.textbbox((0, 0), line, font=font)
                    tw = bbt[2] - bbt[0]
                    tx = x0 + (w - tw) // 2
                    draw.text((tx, y_pos), line, fill="white", font=font)
                    y_pos += line_height

            img = Image.alpha_composite(img, overlay)

        # Save as RGB
        out_path = os.path.join(tmpdir, f"out-{page_idx+1:03d}.png")
        img.convert("RGB").save(out_path, "PNG")
        page_images.append(out_path)

    print(f"\n\n正在生成 PDF...")

    # Combine images into PDF
    pil_images = [Image.open(p).convert("RGB") for p in page_images]
    pil_images[0].save(output_pdf, "PDF", save_all=True, append_images=pil_images[1:])

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"✓ 完成！PDF 已保存到: {output_pdf}")
    print(f"  共 {total_pages} 页，{os.path.getsize(output_pdf)/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()