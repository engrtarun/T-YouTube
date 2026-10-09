"""Generate all GitHub repo artwork for T YouTube (no external deps beyond Pillow)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

REPO = r"C:\Users\pocot\Music\T YOUTUBE PRO\repo"
ASSETS = os.path.join(REPO, "assets")
SHOTS = os.path.join(ASSETS, "screenshots")
RES = r"C:\Users\pocot\AppData\Local\Temp\opencode\ytpatch\dec59\res"

CYAN = (0, 229, 255)
PINK = (255, 45, 120)
WHITE = (255, 255, 255)
GREY = (150, 155, 165)
DIM = (92, 96, 108)

F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
F_SEMI = r"C:\Windows\Fonts\seguisb.ttf"
F_REG = r"C:\Windows\Fonts\segoeui.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def load_icon(size=512):
    d = os.path.join(RES, "mipmap-xxxhdpi")
    bg = Image.open(os.path.join(
        d, "adaptiveproduct_youtube_2024_q4_background_color_108.png")).convert("RGBA")
    fg = Image.open(os.path.join(
        d, "adaptiveproduct_youtube_2024_q4_foreground_color_108.png")).convert("RGBA")
    icon = Image.alpha_composite(bg, fg)
    res = icon.width
    vis = int(res * 72 / 108)
    off = (res - vis) // 2
    crop = icon.crop((off, off, off + vis, off + vis))
    m = Image.new("L", (vis, vis), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, vis - 1, vis - 1),
                                       radius=int(vis * 0.28), fill=255)
    al = crop.split()[3]
    crop.putalpha(Image.composite(al, Image.new("L", al.size, 0), m))
    return crop.resize((size, size), Image.LANCZOS)


def glow_bg(w, h):
    """Dark backdrop with a soft cyan/pink brand glow behind the mark."""
    bg = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=(int(4 + 8 * t), int(4 + 8 * t), int(9 + 16 * t)))
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((w * 0.02, -h * 0.55, w * 0.52, h * 0.95), fill=(0, 70, 95))
    gd.ellipse((w * 0.55, h * 0.05, w * 1.12, h * 1.55), fill=(95, 12, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=h * 0.28))
    return Image.blend(bg, Image.blend(bg, glow, 0.55), 1.0)


def neon_text(draw, xy, text, fnt, glow=True, radius=14):
    """Text with a cyan left / pink right chromatic split - matches the logo."""
    x, y = xy
    if glow:
        for dx, col, a in ((-3, CYAN, 150), (3, PINK, 150)):
            layer = Image.new("RGBA", draw.im.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).text((x + dx, y), text, font=fnt, fill=col + (a,))
            draw._image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius / 2)))
    draw.text((x, y), text, font=fnt, fill=WHITE)


# ----------------------------------------------------------------- banner
def banner():
    W, H = 1280, 320
    img = glow_bg(W, H).convert("RGBA")
    d = ImageDraw.Draw(img)

    icon = load_icon(196)
    img.alpha_composite(icon, (72, (H - 196) // 2))

    x = 316
    neon_text(d, (x, 74), "T YouTube", font(F_BOLD, 74))
    d.text((x, 166), "YouTube, minus the noise.", font=font(F_REG, 28), fill=GREY)

    bx, by = x, 214
    for label, col in (("Ad-free", CYAN), ("Rebranded", PINK), ("microG", DIM)):
        f = font(F_SEMI, 22)
        tw = d.textlength(label, font=f)
        d.rounded_rectangle((bx, by, bx + tw + 30, by + 38), radius=19,
                            outline=col + (170,), width=2)
        d.text((bx + 15, by + 8), label, font=f, fill=col)
        bx += tw + 30 + 16

    img.convert("RGB").save(os.path.join(ASSETS, "banner.png"), quality=95)
    print("  banner.png", img.size)


# ------------------------------------------------------------- og image
def og_image():
    W, H = 1200, 630
    img = glow_bg(W, H).convert("RGBA")
    d = ImageDraw.Draw(img)

    icon = load_icon(200)
    img.alpha_composite(icon, ((W - 200) // 2, 78))

    t = "T YouTube"
    f = font(F_BOLD, 86)
    tw = d.textlength(t, font=f)
    neon_text(d, ((W - tw) / 2, 306), t, f)

    s = "Startup promo removed  ·  Fully rebranded  ·  Powered by microG"
    fs = font(F_REG, 26)
    d.text(((W - d.textlength(s, font=fs)) / 2, 420), s, font=fs, fill=GREY)

    v = "v1.0.0  ·  Android 10+"
    fv = font(F_SEMI, 24)
    d.text(((W - d.textlength(v, font=fv)) / 2, 476), v, font=fv, fill=CYAN)

    img.convert("RGB").save(os.path.join(ASSETS, "og-image.png"), quality=95)
    print("  og-image.png", img.size)


# -------------------------------------------------------- feature strip
def feature_strip():
    W, H = 1200, 200
    img = Image.new("RGBA", (W, H), (11, 12, 16, 255))
    d = ImageDraw.Draw(img)
    items = [
        ("STARTUP POPUP", "REMOVED", CYAN),
        ("82 LOCALES", "REBRANDED", PINK),
        ("5 DENSITIES", "ICON REBUILT", WHITE),
    ]
    w = W / len(items)
    for i, (a, b, col) in enumerate(items):
        cx = w * i + w / 2
        d.text((cx, 62), a, font=font(F_SEMI, 21), fill=DIM, anchor="mm")
        d.text((cx, 104), b, font=font(F_BOLD, 34), fill=col, anchor="mm")
        if i:
            d.line([(w * i, 52), (w * i, H - 52)], fill=(38, 40, 48), width=2)
    img.convert("RGB").save(os.path.join(ASSETS, "feature-strip.png"), quality=95)
    print("  feature-strip.png", img.size)


# ------------------------------------------------------- screenshot slots
SLOTS = [
    ("home.jpg", "Home feed", "screen 1"),
    ("player.jpg", "Player", "screen 2"),
    ("settings.jpg", "Settings", "proof of rebrand"),
    ("downloader.jpg", "Downloads", "base features intact"),
    ("no-popup.jpg", "No promo popup", "headline feature"),
]


def slots():
    os.makedirs(SHOTS, exist_ok=True)
    W, H = 720, 1560
    icon = load_icon(180)
    for fn, title, sub in SLOTS:
        img = Image.new("RGBA", (W, H), (16, 17, 21, 255))
        d = ImageDraw.Draw(img)
        for y in range(0, H, 8):                       # faint grid = "empty" feel
            d.line([(0, y), (W, y)], fill=(20, 21, 26, 255))

        d.rounded_rectangle((2, 2, W - 3, H - 3), radius=54,
                            outline=(46, 49, 58), width=4)

        img.alpha_composite(icon, ((W - 180) // 2, 300))
        d.text((W / 2, 570), "SCREENSHOT", font=font(F_BOLD, 46), fill=(64, 68, 78), anchor="mm")
        d.text((W / 2, 628), "PLACEHOLDER", font=font(F_BOLD, 46), fill=(64, 68, 78), anchor="mm")

        d.line([((W - 120) / 2, 676), ((W + 120) / 2, 676)], fill=(52, 55, 64), width=2)

        d.text((W / 2, 730), title, font=font(F_SEMI, 32), fill=CYAN, anchor="mm")
        d.text((W / 2, 774), sub, font=font(F_REG, 24), fill=(88, 93, 104), anchor="mm")

        f = font(F_REG, 22)
        d.text((W / 2, H - 150), "replace with your capture:",
               font=f, fill=(72, 76, 86), anchor="mm")
        d.text((W / 2, H - 112), f"assets/screenshots/{fn}",
               font=font(F_SEMI, 22), fill=(104, 110, 122), anchor="mm")

        img.convert("RGB").save(os.path.join(SHOTS, fn.replace(".jpg", ".png")),
                                quality=95)
    print(f"  screenshots/: {len(SLOTS)} placeholder slots")


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    print("generating repo artwork...")
    banner()
    og_image()
    feature_strip()
    slots()
    print("done")