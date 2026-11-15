import json
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
    FONT_REG = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def wrap_lines(draw, text, font, max_width):
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split(" ")
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                # Break overly long single tokens
                if draw.textbbox((0, 0), w, font=font)[2] > max_width:
                    chunk = ""
                    for ch in w:
                        if draw.textbbox((0, 0), chunk + ch, font=font)[2] <= max_width:
                            chunk += ch
                        else:
                            lines.append(chunk)
                            chunk = ch
                    current = chunk
                else:
                    current = w
        if current:
            lines.append(current)
    return lines

def render_slide(slide, idx, total, palette, handle, out_path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), palette["bg"])
    draw = ImageDraw.Draw(img)

    # Outer editorial card frame
    draw.rounded_rectangle([48, 48, W - 48, H - 48], radius=36, fill=palette["card"], outline=palette["border"], width=3)

    font_badge = load_font(FONT_BOLD, 24)
    font_page = load_font(FONT_BOLD, 26)
    font_cover_title = load_font(FONT_BOLD, 76)
    font_title = load_font(FONT_BOLD, 56)
    font_sub = load_font(FONT_REG, 34)
    font_bullet = load_font(FONT_BOLD, 32)
    font_num = load_font(FONT_BOLD, 26)
    font_footer = load_font(FONT_BOLD, 26)
    font_tag = load_font(FONT_REG, 24)

    # Top badge & pagination
    badge_text = slide.get("badge", "TREND BRIEF")
    b_box = draw.textbbox((0, 0), badge_text, font=font_badge)
    b_w = (b_box[2] - b_box[0]) + 56
    draw.rounded_rectangle([96, 102, 96 + b_w, 156], radius=27, fill=palette["accent_soft"])
    draw.text((124, 114), badge_text, font=font_badge, fill=palette["accent"])

    page_str = f"{idx:02d} / {total:02d}"
    p_box = draw.textbbox((0, 0), page_str, font=font_page)
    draw.text((W - 96 - (p_box[2] - p_box[0]), 114), page_str, font=font_page, fill=palette["secondary"])

    is_cover = (idx == 1)

    if is_cover:
        # Accent bar
        draw.rounded_rectangle([96, 260, 196, 272], radius=6, fill=palette["accent"])
        y = 310
        title_lines = wrap_lines(draw, slide.get("title", ""), font_cover_title, W - 192)
        for line in title_lines[:4]:
            draw.text((96, y), line, font=font_cover_title, fill=palette["primary"])
            y += 102

        y += 28
        sub_lines = wrap_lines(draw, slide.get("subtitle", ""), font_sub, W - 192)
        for sline in sub_lines[:3]:
            draw.text((96, y), sline, font=font_sub, fill=palette["secondary"])
            y += 52

        # Bottom callout box on cover
        draw.rounded_rectangle([96, 940, W - 96, 1130], radius=26, fill=palette["accent_soft"])
        draw.text((136, 982), "SWIPE TO READ  →", font=font_badge, fill=palette["accent"])
        draw.text((136, 1036), slide.get("cta", "옆으로 넘겨 핵심 체크리스트를 확인하세요"), font=font_bullet, fill=palette["primary"])
    else:
        y = 230
        title_lines = wrap_lines(draw, slide.get("title", ""), font_title, W - 192)
        for line in title_lines[:3]:
            draw.text((96, y), line, font=font_title, fill=palette["primary"])
            y += 78

        if slide.get("subtitle"):
            y += 8
            sub_lines = wrap_lines(draw, slide["subtitle"], font_sub, W - 192)
            for sline in sub_lines[:2]:
                draw.text((96, y), sline, font=font_sub, fill=palette["secondary"])
                y += 48

        card_y = max(y + 36, 440)
        bullets = slide.get("bullets", [])[:4]
        for b_idx, b_text in enumerate(bullets, start=1):
            b_lines = wrap_lines(draw, b_text, font_bullet, W - 300)[:3]
            box_h = max(126, len(b_lines) * 46 + 56)
            draw.rounded_rectangle([96, card_y, W - 96, card_y + box_h], radius=24, fill=palette["bg"], outline=palette["border"], width=2)

            # Number circle
            cx, cy, r = 152, card_y + box_h // 2, 24
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=palette["accent"])
            num_s = str(b_idx)
            nb = draw.textbbox((0, 0), num_s, font=font_num)
            draw.text((cx - (nb[2] - nb[0]) / 2, cy - (nb[3] - nb[1]) / 2 - 3), num_s, font=font_num, fill="#FFFFFF")

            text_y = card_y + (box_h - len(b_lines) * 46) // 2
            for bl in b_lines:
                draw.text((200, text_y), bl, font=font_bullet, fill=palette["primary"])
                text_y += 46

            card_y += box_h + 26

    # Footer
    draw.line([96, H - 155, W - 96, H - 155], fill=palette["border"], width=2)
    draw.text((96, H - 122), handle, font=font_footer, fill=palette["secondary"])
    tag_str = "DATA-DRIVEN INSIGHTS"
    tb = draw.textbbox((0, 0), tag_str, font=font_tag)
    draw.text((W - 96 - (tb[2] - tb[0]), H - 120), tag_str, font=font_tag, fill=palette["secondary"])

    img.save(out_path, format="PNG", optimize=True)

def main():
    with open("data/slides.json", "r", encoding="utf-8") as f:
        spec = json.load(f)

    palettes = {
        "cream": {
            "bg": "#FAF6F1",
            "card": "#FFFFFF",
            "border": "#E6DDD2",
            "primary": "#1E1B18",
            "secondary": "#5C534A",
            "accent": "#D96B43",
            "accent_soft": "#FBECE6"
        },
        "editorial": {
            "bg": "#F3F5F8",
            "card": "#FFFFFF",
            "border": "#DCE2EA",
            "primary": "#14171A",
            "secondary": "#536471",
            "accent": "#2563EB",
            "accent_soft": "#EFF6FF"
        },
        "dark": {
            "bg": "#141416",
            "card": "#1F1F23",
            "border": "#323238",
            "primary": "#F8F8FA",
            "secondary": "#A8A8B3",
            "accent": "#FF7A59",
            "accent_soft": "#2F211E"
        }
    }

    theme = spec.get("theme", "cream")
    palette = palettes.get(theme, palettes["cream"])
    handle = spec.get("handle", "@deepdig486")
    output_dir = Path(spec.get("output_dir", "posts/latest"))
    output_dir.mkdir(parents=True, exist_ok=True)

    slides = spec.get("slides", [])
    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        out_file = output_dir / f"slide_{i}.png"
        render_slide(slide, i, total, palette, handle, out_file)
        print(f"Rendered {out_file}")

if __name__ == "__main__":
    main()
