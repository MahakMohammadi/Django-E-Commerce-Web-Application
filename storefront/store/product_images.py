"""Generate polished, category-matched placeholder product images.

Real photo downloads aren't available in every environment this project runs
in, so this module draws attractive, category-specific vector-style images
locally with Pillow instead: a soft gradient card, a hand-drawn icon that
matches the product's collection (electronics, clothing, books, ...), and the
product title as a caption. This guarantees every product has a relevant,
non-broken image regardless of network access.
"""
import io
import random

from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

IMAGE_SIZE = (640, 480)

# Per-collection visual identity: background gradient + accent (icon/text) color.
CATEGORY_STYLES = {
    "Electronics": {"top": (30, 41, 59), "bottom": (51, 65, 85), "accent": (56, 189, 248), "icon": "electronics"},
    "Home & Kitchen": {"top": (255, 247, 237), "bottom": (253, 186, 116), "accent": (154, 52, 18), "icon": "mug"},
    "Books": {"top": (250, 245, 230), "bottom": (222, 199, 156), "accent": (92, 58, 32), "icon": "book"},
    "Clothing": {"top": (238, 242, 255), "bottom": (165, 180, 252), "accent": (55, 48, 163), "icon": "shirt"},
    "Sports & Outdoors": {"top": (236, 253, 245), "bottom": (110, 231, 183), "accent": (4, 120, 87), "icon": "ball"},
    "Toys & Games": {"top": (255, 241, 242), "bottom": (253, 164, 175), "accent": (190, 18, 60), "icon": "blocks"},
    "Beauty & Personal Care": {"top": (253, 242, 248), "bottom": (249, 168, 212), "accent": (157, 23, 77), "icon": "bottle"},
    "Automotive": {"top": (241, 245, 249), "bottom": (148, 163, 184), "accent": (15, 23, 42), "icon": "car"},
    "Garden & Outdoor": {"top": (240, 253, 244), "bottom": (134, 239, 172), "accent": (21, 128, 61), "icon": "leaf"},
    "Office Supplies": {"top": (255, 251, 235), "bottom": (252, 211, 77), "accent": (120, 53, 15), "icon": "pencil"},
    "Pet Supplies": {"top": (255, 247, 237), "bottom": (253, 164, 175), "accent": (154, 52, 18), "icon": "paw"},
    "Health & Wellness": {"top": (240, 253, 250), "bottom": (94, 234, 212), "accent": (15, 118, 110), "icon": "cross"},
    "Music & Instruments": {"top": (245, 243, 255), "bottom": (196, 181, 253), "accent": (91, 33, 182), "icon": "note"},
    "Grocery": {"top": (247, 254, 231), "bottom": (190, 242, 100), "accent": (63, 98, 18), "icon": "apple"},
    "Jewelry": {"top": (255, 251, 235), "bottom": (253, 224, 71), "accent": (133, 77, 14), "icon": "gem"},
}
DEFAULT_STYLE = {"top": (243, 244, 246), "bottom": (203, 213, 225), "accent": (71, 85, 105), "icon": "box"}


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _draw_gradient(draw, size, top_color, bottom_color):
    width, height = size
    for y in range(height):
        color = _lerp(top_color, bottom_color, y / height)
        draw.line([(0, y), (width, y)], fill=color)


def _draw_icon_badge(draw, cx, cy, radius, fill=(255, 255, 255)):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill + (235,) if len(fill) == 3 else fill)


# --- Per-category icon illustrations (drawn with plain PIL primitives) -----

def _icon_electronics(draw, cx, cy, s, color, w):
    bw, bh = s * 0.62, s * 0.46
    draw.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=s * 0.05, outline=color, width=w)
    draw.rounded_rectangle(
        [cx - bw / 2 + s * 0.06, cy - bh / 2 + s * 0.06, cx + bw / 2 - s * 0.06, cy + bh / 2 - s * 0.12],
        radius=s * 0.02, outline=color, width=max(1, w - 1),
    )
    draw.ellipse([cx - s * 0.025, cy + bh / 2 - s * 0.085, cx + s * 0.025, cy + bh / 2 - s * 0.035], outline=color, width=max(1, w - 1))


def _icon_mug(draw, cx, cy, s, color, w):
    bw, bh = s * 0.34, s * 0.4
    draw.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=s * 0.03, outline=color, width=w)
    draw.arc([cx + bw / 2 - s * 0.05, cy - bh * 0.18, cx + bw / 2 + s * 0.22, cy + bh * 0.18], start=280, end=80, fill=color, width=w)
    draw.line([(cx - bw / 2, cy - bh / 2 - s * 0.04), (cx - bw / 2, cy - bh / 2)], fill=color, width=w)


def _icon_book(draw, cx, cy, s, color, w):
    hw, hh = s * 0.34, s * 0.24
    draw.polygon([
        (cx - hw, cy - hh), (cx, cy - hh + s * 0.05), (cx + hw, cy - hh),
        (cx + hw, cy + hh), (cx, cy + hh - s * 0.05), (cx - hw, cy + hh),
    ], outline=color, width=w)
    draw.line([(cx, cy - hh + s * 0.05), (cx, cy + hh - s * 0.05)], fill=color, width=w)


def _icon_shirt(draw, cx, cy, s, color, w):
    hw, hh = s * 0.28, s * 0.3
    draw.polygon([
        (cx - hw * 0.55, cy - hh), (cx + hw * 0.55, cy - hh),
        (cx + hw * 0.55, cy - hh * 0.55), (cx + hw * 1.6, cy - hh * 0.25),
        (cx + hw * 1.05, cy + hh * 0.2), (cx + hw * 0.7, cy - hh * 0.1),
        (cx + hw * 0.7, cy + hh), (cx - hw * 0.7, cy + hh),
        (cx - hw * 0.7, cy - hh * 0.1), (cx - hw * 1.05, cy + hh * 0.2),
        (cx - hw * 1.6, cy - hh * 0.25), (cx - hw * 0.55, cy - hh * 0.55),
    ], outline=color, width=w)


def _icon_ball(draw, cx, cy, s, color, w):
    r = s * 0.28
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=200, end=340, fill=color, width=max(1, w - 1))
    draw.line([(cx - r * 0.55, cy - r * 0.35), (cx + r * 0.55, cy - r * 0.35)], fill=color, width=max(1, w - 1))


def _icon_blocks(draw, cx, cy, s, color, w):
    size = s * 0.2
    for dx, dy in [(-1, -0.55), (1, -0.55), (0, 0.55)]:
        x, y = cx + dx * size * 1.25, cy + dy * size * 1.25
        draw.rounded_rectangle([x - size / 2, y - size / 2, x + size / 2, y + size / 2], radius=size * 0.18, outline=color, width=w)


def _icon_bottle(draw, cx, cy, s, color, w):
    bw, bh = s * 0.26, s * 0.42
    draw.rounded_rectangle([cx - bw / 2, cy - bh / 2 + s * 0.08, cx + bw / 2, cy + bh / 2], radius=s * 0.04, outline=color, width=w)
    draw.rectangle([cx - bw * 0.22, cy - bh / 2 - s * 0.05, cx + bw * 0.22, cy - bh / 2 + s * 0.08], outline=color, width=w)


def _icon_car(draw, cx, cy, s, color, w):
    bw, bh = s * 0.58, s * 0.2
    draw.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=s * 0.06, outline=color, width=w)
    draw.arc([cx - bw * 0.3, cy - bh * 1.7, cx + bw * 0.05, cy], start=180, end=360, fill=color, width=w)
    r = s * 0.06
    for dx in (-0.28, 0.28):
        x = cx + dx * bw
        draw.ellipse([x - r, cy + bh / 2 - r, x + r, cy + bh / 2 + r], outline=color, width=max(1, w - 1))


def _icon_leaf(draw, cx, cy, s, color, w):
    draw.ellipse([cx - s * 0.22, cy - s * 0.3, cx + s * 0.22, cy + s * 0.12], outline=color, width=w)
    draw.line([(cx - s * 0.2, cy - s * 0.09), (cx + s * 0.2, cy - s * 0.09)], fill=color, width=max(1, w - 1))
    draw.line([(cx, cy + s * 0.12), (cx, cy + s * 0.3)], fill=color, width=w)


def _icon_pencil(draw, cx, cy, s, color, w):
    draw.line([(cx - s * 0.24, cy + s * 0.24), (cx + s * 0.2, cy - s * 0.2)], fill=color, width=int(s * 0.07))
    draw.polygon([(cx + s * 0.2, cy - s * 0.2), (cx + s * 0.3, cy - s * 0.3), (cx + s * 0.32, cy - s * 0.16)], outline=color, width=w)
    draw.line([(cx - s * 0.3, cy + s * 0.3), (cx - s * 0.24, cy + s * 0.24)], fill=color, width=int(s * 0.07))


def _icon_paw(draw, cx, cy, s, color, w):
    r = s * 0.16
    draw.ellipse([cx - r, cy - r * 0.2, cx + r, cy + r * 1.3], outline=color, width=w)
    for dx, dy in [(-0.75, -1.1), (-0.28, -1.5), (0.28, -1.5), (0.75, -1.1)]:
        rr = r * 0.42
        x, y = cx + dx * r, cy + dy * r
        draw.ellipse([x - rr, y - rr, x + rr, y + rr], outline=color, width=max(1, w - 1))


def _icon_cross(draw, cx, cy, s, color, w):
    hw = s * 0.28
    t = s * 0.11
    draw.rounded_rectangle([cx - t / 2, cy - hw, cx + t / 2, cy + hw], radius=t * 0.3, outline=color, width=w)
    draw.rounded_rectangle([cx - hw, cy - t / 2, cx + hw, cy + t / 2], radius=t * 0.3, outline=color, width=w)


def _icon_note(draw, cx, cy, s, color, w):
    r = s * 0.09
    draw.ellipse([cx - r * 1.6, cy + s * 0.12, cx + r * 0.4, cy + s * 0.12 + 2 * r], outline=color, width=w)
    stem_x = cx + r * 0.4 - 1
    draw.line([(stem_x, cy + s * 0.12 + r), (stem_x, cy - s * 0.28)], fill=color, width=max(1, w - 1))
    draw.line([(stem_x, cy - s * 0.28), (stem_x + r * 1.4, cy - s * 0.16)], fill=color, width=max(1, w - 1))


def _icon_apple(draw, cx, cy, s, color, w):
    r = s * 0.24
    draw.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 1.15], outline=color, width=w)
    draw.line([(cx, cy - r * 0.7), (cx + r * 0.25, cy - r * 1.15)], fill=color, width=max(1, w - 1))


def _icon_gem(draw, cx, cy, s, color, w):
    hw, hh = s * 0.22, s * 0.22
    top_l, top_r = (cx - hw / 2, cy - hh), (cx + hw / 2, cy - hh)
    left, right, bottom = (cx - hw, cy - hh * 0.35), (cx + hw, cy - hh * 0.35), (cx, cy + hh)
    draw.polygon([left, top_l, top_r, right, bottom], outline=color, width=w)
    for point in (left, top_l, top_r, right):
        draw.line([point, bottom], fill=color, width=max(1, w - 1))


def _icon_box(draw, cx, cy, s, color, w):
    hw = s * 0.26
    draw.rectangle([cx - hw, cy - hw, cx + hw, cy + hw], outline=color, width=w)
    draw.line([(cx - hw, cy - hw), (cx + hw, cy + hw)], fill=color, width=max(1, w - 1))
    draw.line([(cx - hw, cy + hw), (cx + hw, cy - hw)], fill=color, width=max(1, w - 1))


ICON_DRAWERS = {
    "electronics": _icon_electronics, "mug": _icon_mug, "book": _icon_book, "shirt": _icon_shirt,
    "ball": _icon_ball, "blocks": _icon_blocks, "bottle": _icon_bottle, "car": _icon_car,
    "leaf": _icon_leaf, "pencil": _icon_pencil, "paw": _icon_paw, "cross": _icon_cross,
    "note": _icon_note, "apple": _icon_apple, "gem": _icon_gem, "box": _icon_box,
}


def _load_font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def generate_product_image(title, collection_title, seed=None):
    """Return (filename, ContentFile) for a generated, category-matched product image."""
    rng = random.Random(seed)
    style = CATEGORY_STYLES.get(collection_title, DEFAULT_STYLE)

    image = Image.new("RGB", IMAGE_SIZE, color=style["top"])
    draw = ImageDraw.Draw(image)
    _draw_gradient(draw, IMAGE_SIZE, style["top"], style["bottom"])

    width, height = IMAGE_SIZE
    badge_cy = height * 0.42
    badge_r = min(width, height) * 0.26
    draw.ellipse(
        [width / 2 - badge_r, badge_cy - badge_r, width / 2 + badge_r, badge_cy + badge_r],
        fill=(255, 255, 255, 235),
    )

    icon_fn = ICON_DRAWERS.get(style["icon"], _icon_box)
    icon_size = badge_r * 1.7
    icon_fn(draw, width / 2, badge_cy, icon_size, style["accent"], max(3, int(icon_size * 0.045)))

    # Caption banner with the product title.
    font = _load_font(26)
    caption_y = height * 0.78
    draw.rectangle([0, caption_y, width, height], fill=(255, 255, 255))
    draw.line([(0, caption_y), (width, caption_y)], fill=(226, 232, 240), width=2)

    text = title if len(title) <= 28 else title[:25] + "..."
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((width - text_w) / 2, caption_y + (height - caption_y) / 2 - 16), text, fill=(51, 65, 85), font=font)

    small_font = _load_font(16)
    subtitle = collection_title
    bbox2 = draw.textbbox((0, 0), subtitle, font=small_font)
    sub_w = bbox2[2] - bbox2[0]
    draw.text(((width - sub_w) / 2, caption_y + (height - caption_y) / 2 + 14), subtitle, fill=(148, 163, 184), font=small_font)

    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(226, 232, 240), width=2)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    filename = f"{slugify(title)}-{rng.randint(1000, 9999)}.png"
    return filename, ContentFile(buffer.read())
