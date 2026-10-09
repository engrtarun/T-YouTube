"""Rebuild the in-app 'YouTube Pro' wordmark images as 'T YouTube'.

The old branding was baked into PNG/WebP pixels, not stored as strings, so a
string scan cannot find it. Each asset = [app logo] + ['YouTube Pro' text].
We keep the exact pixel size and layout, swap the logo for the T mark and
re-render the text.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

RES = r"C:\Users\pocot\AppData\Local\Temp\opencode\ytpatch\dec59\res"
ICON_SRC = os.path.join(RES, "mipmap-xxxhdpi",
                        "adaptiveproduct_youtube_2024_q4_background_color_108.png")
ICON_FG = os.path.join(RES, "mipmap-xxxhdpi",
                       "adaptiveproduct_youtube_2024_q4_foreground_color_108.png")

F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
TEXT = "T YouTube"

BASENAMES = [
    "yt_wordmark_header_dark.png",
    "yt_wordmark_header_light.png",
    "yt_premium_wordmark_header_dark.png",
    "yt_premium_wordmark_header_light.png",
    "yt_ringo2_wordmark_header_dark.webp",
    "yt_ringo2_wordmark_header_light.webp",
    "yt_ringo2_premium_wordmark_header_dark.webp",
    "yt_ringo2_premium_wordmark_header_light.webp",
]

DARK_TEXT = (255, 255, 255, 255)     # "_dark"  = glyph white (shown on dark UI)
LIGHT_TEXT = (0, 0, 0, 255)          # "_light" = glyph black (shown on light UI)

_icon_cache = {}


def app_icon(px):
    """Squircle app icon at px, matching the launcher look."""
    if px in _icon_cache:
        return _icon_cache[px]
    bg = Image.open(ICON_SRC).convert("RGBA")
    fg = Image.open(ICON_FG).convert("RGBA")
    ic = Image.alpha_composite(bg, fg)
    res = ic.width
    vis = int(res * 72 / 108)
    off = (res - vis) // 2
    crop = ic.crop((off, off, off + vis, off + vis)).convert("RGBA")
    m = Image.new("L", (vis, vis), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, vis - 1, vis - 1),
                                       radius=int(vis * 0.28), fill=255)
    al = crop.split()[3]
    crop.putalpha(Image.composite(al, Image.new("L", al.size, 0), m))
    out = crop.resize((px, px), Image.LANCZOS)
    _icon_cache[px] = out
    return out


def measure(src):
    """Return (logo_box, text_box, size) by splitting saturated logo pixels
    from unsaturated wordmark glyph pixels."""
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    alpha = a[..., 3] / 255.0
    rgb = a[..., :3] / 255.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    logo_m = (alpha > 0.35) & (sat > 0.30) & (mx > 0.25)
    text_m = (alpha > 0.35) & ~logo_m

    def bbox(m):
        if not m.any():
            return None
        ys, xs = np.nonzero(m)
        return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

    return im, bbox(logo_m), bbox(text_m)


def render_text(height, color):
    """Render TEXT at natural aspect ratio, ink height == `height` px."""
    probe = ImageFont.truetype(F_BOLD, 200)
    layer = Image.new("RGBA", (2400, 500), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((20, 20), TEXT, font=probe, fill=color)
    layer = layer.crop(layer.split()[3].getbbox())
    w = max(1, int(round(layer.width * height / layer.height)))
    return layer.resize((w, height), Image.LANCZOS)


def rebuild(path):
    im, logo_box, text_box = measure(path)
    W, H = im.size
    if logo_box is None or text_box is None:
        return None

    lw, lh = logo_box[2] - logo_box[0], logo_box[3] - logo_box[1]
    th = text_box[3] - text_box[1]

    side = int(round(max(lw, lh)))
    lx = logo_box[0] + (lw - side) // 2
    ly = logo_box[1] + (lh - side) // 2
    lx = max(0, min(lx, W - side))
    ly = max(0, min(ly, H - side))

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(app_icon(side), (lx, ly))

    # natural gap, then the wordmark at the original cap height
    gap = max(3, int(round(side * 0.20)))
    color = LIGHT_TEXT if "light" in os.path.basename(path) else DARK_TEXT

    # cap height: keep it proportional to the logo so the pair looks balanced
    target_h = min(th, int(round(side * 0.60)))
    txt = render_text(target_h, color)

    # must fit the canvas: tx .. W - right margin
    right_pad = max(2, int(round(side * 0.06)))
    avail = W - (lx + side + gap) - right_pad
    if txt.width > avail:
        sc = avail / txt.width
        txt = txt.resize((max(1, avail), max(1, int(round(txt.height * sc)))),
                         Image.LANCZOS)

    tx = lx + side + gap
    ty = ly + (side - txt.height) // 2
    out.alpha_composite(txt, (tx, ty))
    return out


def main():
    total = 0
    for base in BASENAMES:
        for dp, dn, fn in os.walk(RES):
            if "drawable" not in dp:
                continue
            if base not in fn:
                continue
            p = os.path.join(dp, base)
            out = rebuild(p)
            if out is None:
                print(f"  SKIP (no logo/text split): {p}")
                continue
            if p.lower().endswith(".webp"):
                out.save(p, "WEBP", quality=95, method=6)
            else:
                out.save(p, "PNG", optimize=True)
            total += 1
    print(f"rebuilt {total} wordmark assets")


if __name__ == "__main__":
    main()