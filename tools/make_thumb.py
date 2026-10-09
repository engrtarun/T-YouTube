"""Generate the tutorial video poster/thumbnail (1280x720).

Designed, not a random frame grab: brand-consistent, readable at small size,
and it hides the "video still buffering" first-paint state.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import os

OUT = r"C:\Users\pocot\Music\T YOUTUBE PRO\repo\docs\assets\thumbnail.png"
ASSETS = r"C:\Users\pocot\Music\T YOUTUBE PRO\repo\docs\assets"

W, H = 1280, 720
CYAN = (0, 229, 255)
PINK = (255, 45, 120)
WHITE = (255, 255, 255)
DIM = (150, 156, 172)

F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
F_SEMI = r"C:\Windows\Fonts\seguisb.ttf"
F_REG = r"C:\Windows\Fonts\segoeui.ttf"


def font(p, s):
    return ImageFont.truetype(p, s)


def squircle(size):
    im = Image.open(os.path.join(ASSETS, "logo.png")).convert("RGBA")
    return im.resize((size, size), Image.LANCZOS)


def bg():
    img = Image.new("RGB", (W, H), (5, 6, 10))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(5 + 6 * t), int(6 + 6 * t), int(12 + 12 * t)))

    g = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse((W * 0.02, -H * 0.85, W * 0.46, H * 0.75), fill=(0, 78, 104))
    gd.ellipse((W * 0.58, H * 0.25, W * 1.08, H * 1.85), fill=(104, 12, 42))
    gd.ellipse((W * 0.30, H * 0.15, W * 0.72, H * 0.95), fill=(24, 10, 30))
    g = g.filter(ImageFilter.GaussianBlur(radius=170))
    return Image.blend(img, Image.blend(img, g, 0.6), 1.0)


def neon(d, xy, text, f, glow=True):
    x, y = xy
    if glow:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((x - 3, y), text, font=f, fill=CYAN + (190,))
        ld.text((x + 3, y), text, font=f, fill=PINK + (190,))
        d._image.alpha_composite(lay.filter(ImageFilter.GaussianBlur(11)))
    d.text((x, y), text, font=f, fill=WHITE)


def main():
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img)

    icon = squircle(150)
    img.alpha_composite(icon, (104, 150))

    x = 300
    d.text((x, 172), "INSTALL TUTORIAL", font=font(F_SEMI, 27), fill=CYAN)
    neon(d, (x, 214), "T YouTube", font(F_BOLD, 76))
    d.text((x, 318), "microG-RE  ·  4 steps  ·  2 minutes",
           font=font(F_REG, 30), fill=DIM)

    # play badge
    cx, cy, r = 1064, 360, 74
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 70), width=3)
    rd.ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16),
               outline=(255, 255, 255, 22), width=2)
    img.alpha_composite(ring.filter(ImageFilter.GaussianBlur(1)))
    # translucent plate: on a dark thumbnail a solid white disc blows out,
    # so the badge is a dark disc with a light rim instead.
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 26))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(2)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(10, 12, 18, 205))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 210), width=5)
    tri = [(cx - 19, cy - 30), (cx - 19, cy + 30), (cx + 33, cy)]
    d.polygon(tri, fill=WHITE)

    # bottom chips
    bx, by = 104, 560
    for label, col in (("Video walkthrough", CYAN), ("Step-by-step", PINK)):
        f = font(F_SEMI, 25)
        tw = d.textlength(label, font=f)
        d.rounded_rectangle((bx, by, bx + tw + 34, by + 46), radius=23,
                            fill=(16, 18, 26), outline=col + (120,), width=2)
        d.text((bx + 17, by + 9), label, font=f, fill=col)
        bx += tw + 34 + 14

    d.line([(104, 512), (W - 104, 512)], fill=(255, 255, 255, 26), width=1)
    d.text((104, 640), "engrtarun.github.io/T-YouTube",
           font=font(F_REG, 24), fill=(120, 126, 142))

    img.convert("RGB").save(OUT, "PNG", optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()