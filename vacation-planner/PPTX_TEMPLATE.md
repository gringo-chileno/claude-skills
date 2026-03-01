# PowerPoint Presentation Template

Complete working Python template for building a vacation comparison presentation using `python-pptx`.

## Dependencies

```bash
pip install python-pptx Pillow requests
```

## Core Utilities

```python
#!/usr/bin/env python3
"""Build a vacation comparison presentation."""

import os, time, subprocess, requests, json, base64
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

# ── Configuration ──
PHOTO_DIR = "vacation-photos"
OUTPUT = "vacation-presentation.pptx"
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# ── Color Scheme ──
BG_DARK = RGBColor(0x1a, 0x1a, 0x2e)
BG_MEDIUM = RGBColor(0x16, 0x21, 0x3e)
ACCENT_GOLD = RGBColor(0xff, 0xd7, 0x00)
ACCENT_TEAL = RGBColor(0x00, 0xd2, 0xd3)
TEXT_WHITE = RGBColor(0xff, 0xff, 0xff)
TEXT_LIGHT = RGBColor(0xcc, 0xcc, 0xcc)
ACCENT_CORAL = RGBColor(0xff, 0x63, 0x48)
GREEN = RGBColor(0x2e, 0xcc, 0x71)

# Assign each destination a distinct color
DEST_COLORS = {
    # "dest_key": RGBColor(r, g, b),
    # Good palette: orange, green, cyan, gold, coral, purple, pink
}
```

## Photo Download Functions

```python
def get_wikimedia_url(filename):
    """Get direct image URL from Wikimedia Commons."""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "titles": f"File:{filename}",
        "prop": "imageinfo", "iiprop": "url", "iiurlwidth": "1280", "format": "json",
    }
    resp = requests.get(api_url, params=params, timeout=15,
                        headers={"User-Agent": "VacationPlanBot/1.0 (vacation planning)"})
    data = resp.json()
    for page in data["query"]["pages"].values():
        if "imageinfo" in page:
            info = page["imageinfo"][0]
            return info.get("thumburl", info["url"])
    return None


def search_wikimedia(query, limit=5):
    """Search Wikimedia Commons for photos matching a query."""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": "6", "gsrlimit": str(limit),
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": "1280",
        "format": "json",
    }
    resp = requests.get(api_url, params=params, timeout=15,
                        headers={"User-Agent": "VacationPlanBot/1.0 (vacation planning)"})
    data = resp.json()
    results = []
    for page in data.get("query", {}).get("pages", {}).values():
        if "imageinfo" in page:
            info = page["imageinfo"][0]
            results.append({
                "title": page["title"],
                "url": info.get("thumburl", info["url"]),
            })
    return results


def download_image(url, local_name):
    """Download image using curl (Python requests gets 403 from Wikimedia)."""
    path = os.path.join(PHOTO_DIR, local_name)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    try:
        tmp_path = path + ".tmp"
        result = subprocess.run(
            ["curl", "-sL", "-o", tmp_path, "-w", "%{http_code}",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url], capture_output=True, text=True, timeout=30)
        status = result.stdout.strip()
        if status != "200" or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 1000:
            if os.path.exists(tmp_path): os.remove(tmp_path)
            return None
        # Resize to keep file size reasonable
        img = Image.open(tmp_path).convert("RGB")
        if max(img.size) > 1920:
            ratio = 1920 / max(img.size)
            img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
        img.save(path, "JPEG", quality=85)
        os.remove(tmp_path)
        return path
    except Exception as e:
        if os.path.exists(path + ".tmp"): os.remove(path + ".tmp")
        return None


def generate_gemini_image(prompt, local_name, api_key):
    """Generate image using Gemini API."""
    path = os.path.join(PHOTO_DIR, local_name)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"Generate a photorealistic travel photograph: {prompt}. Professional travel magazine quality, vibrant colors, landscape orientation 16:9."}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
        }
        resp = requests.post(url, json=payload, timeout=60)
        data = resp.json()
        if "candidates" in data:
            for part in data["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    img = Image.open(BytesIO(img_data)).convert("RGB")
                    if max(img.size) > 1920:
                        ratio = 1920 / max(img.size)
                        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
                    img.save(path, "JPEG", quality=90)
                    return path
        return None
    except Exception:
        return None
```

## Slide Builder Functions

```python
def set_slide_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height, text, font_size=18,
                color=TEXT_WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_multiline_textbox(slide, left, top, width, height, lines,
                          font_size=16, color=TEXT_WHITE, font_name="Calibri"):
    """lines = [(text, is_bold, text_color, size_override), ...]"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, (text, is_bold, text_color, size_override) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size_override or font_size)
        p.font.color.rgb = text_color or color
        p.font.bold = is_bold
        p.font.name = font_name
        p.space_after = Pt(4)
    return txBox


def add_bullet_list(slide, left, top, width, height, items,
                    font_size=16, color=TEXT_WHITE):
    """items = [(text, text_color), ...]"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, (text, text_color) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"\u2022  {text}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = text_color or color
        p.font.name = "Calibri"
        p.space_after = Pt(6)
    return txBox


def add_image_safe(slide, photo_paths, key, left, top, width, height):
    """Add image to slide, with colored placeholder fallback."""
    path = photo_paths.get(key)
    if path and os.path.exists(path):
        try:
            slide.shapes.add_picture(path, left, top, width, height)
            return True
        except Exception:
            pass
    # Placeholder
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x33, 0x33, 0x55)
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"[{key}]"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_LIGHT
    p.alignment = PP_ALIGN.CENTER
    return False
```

## Slide Types

### Hero Slide (1 per destination)
```python
def build_hero_slide(prs, photo_paths, title, tagline, hero_key, accent_color, facts):
    """facts = [("Label", "Value"), ...]"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    set_slide_bg(slide, BG_DARK)
    # Hero photo on right half
    add_image_safe(slide, photo_paths, hero_key, Inches(6.5), Inches(0.3), Inches(6.5), Inches(4.5))
    # Color accent bar
    bar = slide.shapes.add_shape(1, Inches(0.5), Inches(1.2), Inches(0.15), Inches(2))
    bar.fill.solid(); bar.fill.fore_color.rgb = accent_color; bar.line.fill.background()
    # Title + tagline
    add_textbox(slide, Inches(1), Inches(1), Inches(5.2), Inches(1), title, font_size=40, color=accent_color, bold=True)
    add_textbox(slide, Inches(1), Inches(2.2), Inches(5.2), Inches(0.6), f'"{tagline}"', font_size=20, color=TEXT_LIGHT)
    # Key facts
    lines = [(f"{label}:  {value}", False, TEXT_WHITE, 16) for label, value in facts]
    add_multiline_textbox(slide, Inches(1), Inches(3.2), Inches(5), Inches(3), lines)
```

### Photos Slide (1 per destination)
```python
def build_photos_slide(prs, photo_paths, title, photo_keys, captions, accent_color):
    """4 photos in a row with captions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_MEDIUM)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.7), title, font_size=28, color=accent_color, bold=True)
    pw, ph, gap = Inches(2.9), Inches(2.2), Inches(0.25)
    num = min(len(photo_keys), 4)
    total = num * pw + (num - 1) * gap
    sx = (SLIDE_WIDTH - total) // 2
    for i, (key, cap) in enumerate(zip(photo_keys[:4], captions[:4])):
        x = sx + i * (pw + gap)
        add_image_safe(slide, photo_paths, key, x, Inches(1.3), pw, ph)
        add_textbox(slide, x, Inches(3.6), pw, Inches(0.4), cap, font_size=13, color=TEXT_LIGHT, alignment=PP_ALIGN.CENTER)
```

### Activities Slide (1 per destination)
```python
def build_activities_slide(prs, title, activities, accent_color):
    """Two-column bulleted list. activities = [("Label", "Description"), ...]"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_MEDIUM)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.7),
                f"{title} — Activities", font_size=28, color=accent_color, bold=True)
    left_items = activities[:len(activities)//2]
    right_items = activities[len(activities)//2:]
    for col, items in enumerate([left_items, right_items]):
        x = Inches(0.8) + col * Inches(6.2)
        bullet_items = []
        for label, desc in items:
            bullet_items.append((label, accent_color))
            bullet_items.append((f"    {desc}", TEXT_LIGHT))
        add_bullet_list(slide, x, Inches(1.3), Inches(5.8), Inches(5.5), bullet_items, font_size=17)
```

### Plan Slide (1 per destination)
```python
def build_itinerary_slide(prs, title, itinerary_days, pros, cons, cost, accent_color):
    """Three-column: itinerary | pros | cons. itinerary_days = [("Day X", "Description"), ...]"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_DARK)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.7),
                f"{title} — The Plan", font_size=28, color=accent_color, bold=True)
    # Itinerary column
    add_textbox(slide, Inches(0.5), Inches(1.2), Inches(3), Inches(0.5), "ITINERARY", font_size=16, color=ACCENT_GOLD, bold=True)
    lines = []
    for day_label, day_desc in itinerary_days:
        lines.append((day_label, True, accent_color, 15))
        lines.append((day_desc, False, TEXT_LIGHT, 14))
    add_multiline_textbox(slide, Inches(0.5), Inches(1.8), Inches(4.5), Inches(5.5), lines)
    # Pros column
    add_textbox(slide, Inches(5.3), Inches(1.2), Inches(3.5), Inches(0.5), "WHY GO", font_size=16, color=GREEN, bold=True)
    add_multiline_textbox(slide, Inches(5.3), Inches(1.8), Inches(3.8), Inches(5),
                          [(f"+ {p}", False, GREEN, 15) for p in pros])
    # Cons column
    add_textbox(slide, Inches(9.5), Inches(1.2), Inches(3.5), Inches(0.5), "WATCH OUT", font_size=16, color=ACCENT_CORAL, bold=True)
    add_multiline_textbox(slide, Inches(9.5), Inches(1.8), Inches(3.5), Inches(5),
                          [(f"- {c}", False, ACCENT_CORAL, 15) for c in cons])
    # Budget footer
    add_textbox(slide, Inches(0.5), Inches(6.8), Inches(12), Inches(0.5),
                f"Budget: {cost}", font_size=18, color=ACCENT_GOLD, bold=True)
```

### Comparison Slide
```python
def build_comparison_slide(prs, dest_names, dest_colors, categories, scores_matrix, budgets):
    """
    Numeric comparison table with color-coded scores and averages.
    dest_names = ["Dest A", "Dest B", ...]
    categories = ["Fun Activities", "Beach", "Easy Travel", ...]
    scores_matrix = [[5,4,3], [4,5,2], ...]  # one row per category, one score per dest
    budgets = ["$$", "$$$", ...]
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_DARK)
    add_textbox(slide, Inches(0.5), Inches(0.2), Inches(12), Inches(0.6),
                "HEAD TO HEAD", font_size=36, color=ACCENT_GOLD, bold=True, alignment=PP_ALIGN.CENTER)

    headers = [""] + dest_names
    num_dest = len(dest_names)

    # Compute averages
    averages = [0.0] * num_dest
    for scores in scores_matrix:
        for i, s in enumerate(scores):
            averages[i] += s
    averages = [round(a / len(scores_matrix), 1) for a in averages]

    num_rows = len(categories) + 3  # header + data + separator + average
    table_shape = slide.shapes.add_table(num_rows, len(headers), Inches(0.5), Inches(1.1), Inches(12.3), Inches(5.5))
    table = table_shape.table
    table.columns[0].width = Inches(2.0)
    for i in range(1, len(headers)):
        table.columns[i].width = Inches(10.3 // num_dest)

    # Header row
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = ACCENT_GOLD
            p.font.name = "Calibri"; p.alignment = PP_ALIGN.CENTER
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0x0d, 0x0d, 0x1a)

    # Data rows
    for r, (label, scores) in enumerate(zip(categories, scores_matrix)):
        row_idx = r + 1
        bg = RGBColor(0x1f, 0x1f, 0x3a) if r % 2 == 0 else BG_DARK
        cell = table.cell(row_idx, 0)
        cell.text = label
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(15); p.font.color.rgb = TEXT_WHITE; p.font.bold = True; p.font.name = "Calibri"
        cell.fill.solid(); cell.fill.fore_color.rgb = bg
        for c, score in enumerate(scores):
            cell = table.cell(row_idx, c + 1)
            cell.text = str(score)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(22); p.font.bold = True; p.font.name = "Calibri"; p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = GREEN if score >= 5 else TEXT_WHITE if score >= 4 else TEXT_LIGHT if score >= 3 else ACCENT_CORAL
            cell.fill.solid(); cell.fill.fore_color.rgb = bg

    # Separator + Average row
    sep_idx = len(categories) + 1
    for c in range(len(headers)):
        cell = table.cell(sep_idx, c); cell.text = ""; cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x0d, 0x0d, 0x1a)
    avg_idx = len(categories) + 2
    cell = table.cell(avg_idx, 0); cell.text = "AVERAGE"
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(16); p.font.color.rgb = ACCENT_GOLD; p.font.bold = True; p.font.name = "Calibri"
    cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0x0d, 0x0d, 0x1a)
    max_avg = max(averages)
    for c, avg in enumerate(averages):
        cell = table.cell(avg_idx, c + 1); cell.text = str(avg)
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(24); p.font.bold = True; p.font.name = "Calibri"; p.alignment = PP_ALIGN.CENTER
            p.font.color.rgb = ACCENT_GOLD if avg == max_avg else TEXT_WHITE
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0x0d, 0x0d, 0x1a)

    # Budget footer
    budget_text = "Budget:     " + "          ".join(f"{n}: {b}" for n, b in zip(dest_names, budgets))
    add_textbox(slide, Inches(0.5), Inches(6.7), Inches(12.3), Inches(0.5),
                budget_text, font_size=14, color=ACCENT_GOLD, alignment=PP_ALIGN.CENTER)
```

### Voting Slide
```python
def build_voting_slide(prs, photo_paths, options):
    """options = [("1. NAME", "Short\ndescription", "photo_key", accent_color), ...]"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_DARK)
    add_textbox(slide, Inches(0.5), Inches(0.5), Inches(12), Inches(1),
                "WHICH ADVENTURE DO YOU WANT?", font_size=44, color=ACCENT_GOLD, bold=True, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, Inches(0.5), Inches(1.5), Inches(12), Inches(0.6),
                "Pick your top choice!", font_size=24, color=TEXT_WHITE, alignment=PP_ALIGN.CENTER)
    card_w, card_h, gap = Inches(2.2), Inches(1.5), Inches(0.3)
    num = len(options)
    total_w = num * card_w + (num - 1) * gap
    sx = (SLIDE_WIDTH - total_w) // 2
    for i, (name, desc, pk, color) in enumerate(options):
        x = sx + i * (card_w + gap)
        add_image_safe(slide, photo_paths, pk, x, Inches(2.5), card_w, card_h)
        add_textbox(slide, x, Inches(4.2), card_w, Inches(0.5), name, font_size=16, color=color, bold=True, alignment=PP_ALIGN.CENTER)
        add_textbox(slide, x, Inches(4.7), card_w, Inches(0.8), desc, font_size=11, color=TEXT_LIGHT, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, Inches(0.5), Inches(6.2), Inches(12), Inches(0.8),
                "Vote by writing your name under your favorite!", font_size=20, color=ACCENT_TEAL, alignment=PP_ALIGN.CENTER)
```

## Main Function Pattern

```python
def main():
    os.makedirs(PHOTO_DIR, exist_ok=True)

    # 1. Download/generate all photos
    photo_paths = {}
    for key, filename in WIKIMEDIA_PHOTOS.items():
        url = get_wikimedia_url(filename)
        if url:
            photo_paths[key] = download_image(url, f"{key}.jpg")
            time.sleep(2)  # Rate limiting
    for key, prompt in GEMINI_PHOTOS.items():
        photo_paths[key] = generate_gemini_image(prompt, f"{key}.jpg", GEMINI_API_KEY)
        time.sleep(2)

    # 2. Build presentation
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    build_title_slide(prs, photo_paths)

    # For each destination: hero + photos + activities + plan
    # ...

    build_comparison_slide(prs, ...)
    build_voting_slide(prs, photo_paths, ...)

    prs.save(OUTPUT)
    print(f"Saved: {OUTPUT} ({os.path.getsize(OUTPUT) / 1024 / 1024:.1f} MB)")

if __name__ == "__main__":
    main()
```

## Common Airport Codes

For flight searches, common South American codes:
- **Chile:** SCL (Santiago)
- **Brazil:** GRU (São Paulo), GIG (Rio), SSA (Salvador), CGB (Cuiabá), CGR (Campo Grande), SLZ (São Luís), FOR (Fortaleza), BPS (Porto Seguro), REC (Recife), FLN (Florianópolis)
- **Argentina:** EZE (Buenos Aires Ezeiza), AEP (Buenos Aires Aeroparque)
- **Colombia:** BOG (Bogotá), CTG (Cartagena), MDE (Medellín)
- **Peru:** LIM (Lima), CUZ (Cusco)
- **Ecuador:** UIO (Quito), GYE (Guayaquil), GPS (Galápagos)
- **Bolivia:** LPB (La Paz), VVI (Santa Cruz)
