"""Rebuild all T YouTube branding art in the apktool tree (variant A: ring + T).

Layout follows Android adaptive-icon spec:
  canvas          108dp
  masked section   72dp   (outer 18dp per side is parallax bleed)
  safe zone        66dp   -> artwork must never cross this circle
"""
from PIL import Image, ImageDraw
import numpy as np
import os

SRC = r"C:\Users\pocot\Music\T YOUTUBE PRO\T_YouTubeLOGO.jpg"
RES = r"C:\Users\pocot\AppData\Local\Temp\opencode\ytpatch\dec59\res"

CANVAS_DP = 108
MASK_DP = 72
SAFE_DIAMETER_DP = 66.0
SAFE_RADIUS_DP = SAFE_DIAMETER_DP / 2.0   # artwork must stay inside this circle
LEGACY_RADIUS_DP = 20.0                    # legacy bitmap is only 48dp square

BG_COLOR = (0, 0, 0, 255)

DENSITIES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

FG_NAMES = [
    "adaptiveproduct_youtube_foreground_color_108.png",
    "adaptiveproduct_youtube_2024_q4_foreground_color_108.png",
]
BG_NAMES = [
    "adaptiveproduct_youtube_background_color_108.png",
    "adaptiveproduct_youtube_2024_q4_background_color_108.png",
]


# --------------------------------------------------------------------------
def load_art():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    lum = a.max(axis=2)
    alpha = np.clip((lum - 0.035) / 0.965, 0.0, 1.0)
    rgba = Image.fromarray((np.dstack([a, alpha]) * 255).astype(np.uint8), "RGBA")
    return crop_to_ink(rgba)


def crop_to_ink(rgba, thresh=0.5, pad_frac=0.02):
    a = np.asarray(rgba).astype(np.float32) / 255.0
    ys, xs = np.nonzero(a[..., 3] > thresh)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    px, py = int((x1 - x0) * pad_frac), int((y1 - y0) * pad_frac)
    return rgba.crop((max(0, x0 - px), max(0, y0 - py),
                      min(rgba.width, x1 + px), min(rgba.height, y1 + py)))


def ink_radius(rgba, thresh=0.5):
    a = np.asarray(rgba).astype(np.float32) / 255.0
    ys, xs = np.nonzero(a[..., 3] > thresh)
    cx = (xs.min() + xs.max()) / 2.0
    cy = (ys.min() + ys.max()) / 2.0
    return float(np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).max())


def fit_art(art, canvas_px, canvas_dp, radius_dp):
    """Scale + centre `art` so its ink sits inside a circle of radius_dp
    on a canvas that is canvas_dp wide (canvas_px pixels)."""
    want_px = radius_dp / canvas_dp * canvas_px
    factor = want_px / ink_radius(art)
    nw = max(1, int(round(art.width * factor)))
    nh = max(1, int(round(art.height * factor)))
    small = art.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (canvas_px, canvas_px), (0, 0, 0, 0))
    out.paste(small, ((canvas_px - nw) // 2, (canvas_px - nh) // 2), small)
    return out


# --------------------------------------------------------------------------
def build_adaptive(art):
    """Write every adaptive + legacy launcher png for all densities."""
    for bucket, legacy_dp in DENSITIES.items():
        outdir = os.path.join(RES, bucket)
        os.makedirs(outdir, exist_ok=True)

        canvas_px = int(round(_ss(bucket) * legacy_dp * CANVAS_DP / MASK_DP))

        fg = fit_art(art, canvas_px, CANVAS_DP, SAFE_RADIUS_DP)
        bg = Image.new("RGBA", (canvas_px, canvas_px), BG_COLOR)

        for n in FG_NAMES:
            fg.save(os.path.join(outdir, n), "PNG", optimize=True)
        for n in BG_NAMES:
            bg.save(os.path.join(outdir, n), "PNG", optimize=True)

        # legacy bitmap: flat square, artwork kept inside the same safe circle
        legacy_px = int(round(_ss(bucket) * legacy_dp))
        lf = fit_art(art, legacy_px, 48.0, LEGACY_RADIUS_DP)
        lb = Image.new("RGBA", (legacy_px, legacy_px), BG_COLOR)
        Image.alpha_composite(lb, lf).save(
            os.path.join(outdir, "ic_launcher.png"), "PNG", optimize=True)

        print(f"  {bucket:16s} adaptive {canvas_px}px   legacy {legacy_px}px")


def _ss(bucket):
    return {"mipmap-mdpi": 1, "mipmap-hdpi": 1.5, "mipmap-xhdpi": 2,
            "mipmap-xxhdpi": 3, "mipmap-xxxhdpi": 4}[bucket]


# --------------------------------------------------------------------------
# Vector "T" mark (matches the raster logo: cyan top-left, pink bottom-right)
T_BASE = [(32, 35), (76, 35), (76, 49), (60.5, 49), (60.5, 73),
          (47.5, 73), (47.5, 49), (32, 49)]
T_OFF = 3.5

MONO_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector android:height="108.0dip" android:width="108.0dip" android:viewportWidth="108.0" android:viewportHeight="108.0"
  xmlns:android="http://schemas.android.com/apk/res/android">
    <path android:fillColor="#ff00e5ff" android:pathData="{cyan}" />
    <path android:fillColor="#ffff2d78" android:pathData="{pink}" />
    <path android:fillColor="#ffffffff" android:pathData="{base}" />
</vector>
"""


def _shift(poly, dx, dy):
    return [(round(x + dx, 2), round(y + dy, 2)) for x, y in poly]


def _pd(poly):
    d = f"M{round(poly[0][0], 2)},{round(poly[0][1], 2)}"
    for x, y in poly[1:]:
        d += f"L{x},{y}"
    return d + "Z"


def write_monochrome():
    out = MONO_XML.format(
        cyan=_pd(_shift(T_BASE, -T_OFF, -T_OFF)),
        pink=_pd(_shift(T_BASE, T_OFF, T_OFF)),
        base=_pd(T_BASE))
    for name in ("adaptive_monochrome_ic_youtube_launcher.xml",
                 "ringo2_adaptive_monochrome_ic_youtube_launcher.xml"):
        p = os.path.join(RES, "drawable", name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(out)
        print("  wrote", name)


def write_actionbar_logo():
    for bucket, w, h in (("drawable-mdpi", 38, 32),
                         ("drawable-hdpi", 57, 48),
                         ("drawable-xhdpi", 76, 64)):
        d = os.path.join(RES, bucket)
        os.makedirs(d, exist_ok=True)
        span_x = (76 - 32) + 2 * T_OFF
        span_y = (73 - 35) + 2 * T_OFF
        s = min(w * 0.92 / span_x, h * 0.92 / span_y)
        cw = span_x * s
        ch = span_y * s
        ox = (w - cw) / 2 - (32 - T_OFF) * s
        oy = (h - ch) / 2 - (35 - T_OFF) * s

        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        for pts, col in (((T_BASE, -T_OFF, -T_OFF), (0, 229, 255, 255)),
                         ((T_BASE, T_OFF, T_OFF), (255, 45, 120, 255)),
                         ((T_BASE, 0, 0), (255, 255, 255, 255))):
            poly, dx, dy = pts
            dr.polygon([(ox + (x + dx) * s, oy + (y + dy) * s) for x, y in poly],
                       fill=col)
        im.save(os.path.join(d, "ringo2_action_bar_logo_release.webp"),
                "WEBP", lossless=True, quality=100)
        print(f"  {bucket}: action bar logo {w}x{h}")


if __name__ == "__main__":
    print("adaptive + legacy launcher icons:")
    art = load_art()
    print(f"  source art {art.width}x{art.height}px, ink r={ink_radius(art):.0f}px")
    build_adaptive(art)
    print("monochrome (themed) icons:")
    write_monochrome()
    print("in-app action bar logo:")
    write_actionbar_logo()
    print("done")