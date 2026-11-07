"""Generates all binary assets: icon, default skin, backgrounds, installer art.
Run: python tools/gen-assets.py
Fonts (Inter woff2) are downloaded from Google Fonts if missing.
"""
import os
import sys
import math
import urllib.request
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "resources")
BUILD = os.path.join(ROOT, "build")
FONTS = os.path.join(RES, "fonts")
BG = os.path.join(RES, "backgrounds")
SKINS = os.path.join(RES, "skins")

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

CSS_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap"


def ensure_dirs():
    for d in (RES, BUILD, FONTS, BG, SKINS):
        os.makedirs(d, exist_ok=True)


def ensure_fonts():
    css = urllib.request.urlopen(urllib.request.Request(CSS_URL, headers=UA), timeout=30).read().decode()
    blocks = css.split("/* ")[1:]
    for block in blocks:
        subset = block.split(" */")[0].strip()
        if subset != "cyrillic":
            continue
        body = block.split(" */", 1)[1]
        weight = body.split("font-weight:")[1].split(";")[0].strip()
        url = body.split("url(")[1].split(")")[0]
        dest = os.path.join(FONTS, f"inter-{weight}.woff2")
        if os.path.exists(dest):
            continue
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        with open(dest, "wb") as f:
            f.write(data)
        print("font", weight, len(data))


def cube(draw, cx, cy, r, top, left, right):
    """Isometric cube centered at (cx, cy) with half-width r."""
    h = r * 0.58
    draw.polygon([(cx, cy - r), (cx + r, cy - h), (cx, cy), (cx - r, cy - h)], fill=top)
    draw.polygon([(cx - r, cy - h), (cx, cy), (cx, cy + r), (cx - r, cy + h)], fill=left)
    draw.polygon([(cx + r, cy - h), (cx, cy), (cx, cy + r), (cx + r, cy + h)], fill=right)


def make_icon():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=104, fill=(13, 17, 22, 255))
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=104, outline=(35, 43, 52, 255), width=6)
    # glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([120, 150, 400, 430], fill=(47, 111, 237, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)
    cube(d, 256, 268, 130, (64, 150, 255, 255), (28, 84, 190, 255), (18, 56, 130, 255))
    # outline edges
    d.line([(256, 138), (386, 213), (386, 343), (256, 418), (126, 343), (126, 213), (256, 138)],
           fill=(150, 200, 255, 220), width=7)
    d.line([(126, 213), (256, 288), (386, 213)], fill=(150, 200, 255, 220), width=7)
    d.line([(256, 288), (256, 418)], fill=(150, 200, 255, 220), width=7)
    img.save(os.path.join(RES, "icon.png"))
    img.save(os.path.join(BUILD, "icon.png"))
    img.save(os.path.join(BUILD, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                                     (64, 64), (128, 128), (256, 256)])
    print("icon ok")


def make_default_skin():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    skin = (208, 148, 106, 255)
    skin_dark = (176, 120, 84, 255)
    hair = (46, 34, 24, 255)
    jacket = (46, 56, 66, 255)
    jacket_hi = (58, 70, 82, 255)
    vest = (224, 123, 57, 255)
    pants = (35, 42, 51, 255)
    shoe = (20, 24, 29, 255)

    def rect(x, y, w, h, c):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

    # head: top/bottom, sides, face
    rect(8, 0, 8, 8, hair)
    rect(16, 0, 8, 8, skin_dark)
    rect(0, 8, 8, 8, hair)
    rect(8, 8, 8, 8, skin)
    rect(16, 8, 8, 8, skin)
    rect(24, 8, 8, 8, hair)
    rect(8, 16, 8, 8, skin_dark)
    rect(8, 8, 8, 2, hair)          # fringe
    rect(8, 10, 1, 2, hair)
    rect(15, 10, 1, 2, hair)
    rect(10, 12, 1, 1, (240, 240, 240, 255))
    rect(11, 12, 1, 1, (58, 44, 90, 255))
    rect(13, 12, 1, 1, (58, 44, 90, 255))
    rect(14, 12, 1, 1, (240, 240, 240, 255))
    rect(11, 15, 3, 1, skin_dark)   # mouth
    # body: top/bottom, sides, front with hi-vis stripe
    rect(20, 16, 8, 4, jacket_hi)
    rect(28, 16, 8, 4, jacket)
    rect(16, 20, 4, 12, jacket)
    rect(20, 20, 8, 12, jacket)
    rect(28, 20, 4, 12, jacket)
    rect(32, 20, 4, 12, jacket)
    rect(20, 20, 8, 3, vest)
    rect(23, 23, 2, 9, vest)
    # right arm
    rect(44, 16, 4, 4, jacket_hi)
    rect(52, 16, 4, 4, jacket)
    rect(40, 20, 4, 8, jacket)
    rect(44, 20, 4, 8, jacket)
    rect(48, 20, 4, 8, jacket)
    rect(52, 20, 4, 8, jacket)
    rect(40, 28, 4, 4, skin)
    rect(44, 28, 4, 4, skin)
    rect(48, 28, 4, 4, skin)
    rect(52, 28, 4, 4, skin)
    # left arm
    rect(36, 48, 4, 4, jacket_hi)
    rect(44, 48, 4, 4, jacket)
    rect(32, 52, 4, 8, jacket)
    rect(36, 52, 4, 8, jacket)
    rect(40, 52, 4, 8, jacket)
    rect(44, 52, 4, 8, jacket)
    rect(32, 60, 4, 4, skin)
    rect(36, 60, 4, 4, skin)
    rect(40, 60, 4, 4, skin)
    rect(44, 60, 4, 4, skin)
    # right leg
    rect(4, 16, 4, 4, pants)
    rect(12, 16, 4, 4, pants)
    rect(0, 20, 4, 8, pants)
    rect(4, 20, 4, 8, pants)
    rect(8, 20, 4, 8, pants)
    rect(12, 20, 4, 8, pants)
    rect(0, 28, 4, 4, shoe)
    rect(4, 28, 4, 4, shoe)
    rect(8, 28, 4, 4, shoe)
    rect(12, 28, 4, 4, shoe)
    # left leg
    rect(20, 48, 4, 4, pants)
    rect(28, 48, 4, 4, pants)
    rect(16, 52, 4, 8, pants)
    rect(20, 52, 4, 8, pants)
    rect(24, 52, 4, 8, pants)
    rect(28, 52, 4, 8, pants)
    rect(16, 60, 4, 4, shoe)
    rect(20, 60, 4, 4, shoe)
    rect(24, 60, 4, 4, shoe)
    rect(28, 60, 4, 4, shoe)
    img.save(os.path.join(SKINS, "default.png"))
    print("skin ok")


def gradient(size, c1, c2, angle=0):
    g = Image.linear_gradient("L").resize(size)
    if angle:
        g = g.rotate(angle, expand=False, fillcolor=0)
    return ImageOps.colorize(g, black=c2, white=c1)


def add_noise(img, sigma=14, opacity=0.16):
    noise = Image.effect_noise(img.size, sigma).convert("L")
    noise = ImageChops.subtract(noise, Image.new("L", img.size, 128), 1.0, 0)
    layer = Image.merge("RGBA", (noise, noise, noise, Image.new("L", img.size, int(255 * opacity))))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def vignette(img, strength=0.55):
    mask = Image.radial_gradient("L").resize(img.size)
    mask = ImageOps.invert(mask).point(lambda v: int(v * strength))
    black = Image.new("RGBA", img.size, (0, 0, 0, 255))
    out = img.convert("RGBA").copy()
    out.paste(black, (0, 0), mask)
    return out


def bokeh(img, spots, color, blur=26):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for (x, y, r, a) in spots:
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def vgrad(w, h, top, bottom, stop=0.68):
    """Vertical sky gradient: top color at y=0 reaching bottom at y=h*stop."""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    sy = max(1, int(h * stop))
    for y in range(h):
        t = min(1.0, y / sy)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def glow(img, boxes, blur=120):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for (x0, y0, x1, y1, color, a) in boxes:
        d.ellipse([x0, y0, x1, y1], fill=color + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def haze(img, color, alpha, y0, y1, blur=50):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, y0, img.width, y1], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def crane(d, x, base_y, height, jib, color, counter=80):
    top = base_y - height
    d.rectangle([x - 6, top, x + 6, base_y], fill=color)
    d.polygon([(x - 4, top + 2), (x + jib, top + 10), (x + jib, top + 18), (x - 4, top + 18)], fill=color)
    d.polygon([(x + 4, top + 2), (x - counter, top + 12), (x - counter, top + 20), (x + 4, top + 20)], fill=color)
    d.polygon([(x - 7, top + 2), (x + 7, top + 2), (x, top - 40)], fill=color)
    d.line([(x, top - 38), (x + int(jib * 0.78), top + 10)], fill=color, width=3)
    d.line([(x, top - 38), (x - int(counter * 0.85), top + 12)], fill=color, width=3)
    tx = x + int(jib * 0.6)
    d.line([(tx, top + 18), (tx, top + 150)], fill=color, width=3)
    d.rectangle([tx - 12, top + 150, tx + 12, top + 172], fill=color)


def containers(d, x, base_y, cols, rows, color, cw=88, ch=34):
    for r in range(rows):
        for c in range(cols):
            bx = x + c * (cw + 8)
            d.rectangle([bx, base_y - (r + 1) * ch, bx + cw, base_y - r * ch - 2], fill=color)


def tanks(d, x, base_y, color, specs):
    for (tw, th) in specs:
        d.rectangle([x, base_y - th, x + tw, base_y], fill=color)
        d.pieslice([x, base_y - th - tw // 2, x + tw, base_y - th + tw // 2], 180, 360, fill=color)
        x += tw + 30


def pipes(d, x, y, length, color, n=3, r=13):
    for i in range(n):
        yy = y - i * (r * 2 + 10)
        d.rounded_rectangle([x, yy - r, x + length, yy + r], r, fill=color)


def skyline(d, w, base_y, color, seed, lit=None, lit_limit=0):
    rnd = random.Random(seed)
    x = -60
    lights = []
    while x < w + 60:
        bw = rnd.randint(90, 230)
        bh = rnd.randint(40, 150)
        d.rectangle([x, base_y - bh, x + bw, base_y + 4], fill=color)
        if rnd.random() < 0.4:
            hw = rnd.randint(8, 14)
            hh = rnd.randint(24, 70)
            d.rectangle([x + bw // 3, base_y - bh - hh, x + bw // 3 + hw, base_y - bh], fill=color)
        if lit:
            for _ in range(rnd.randint(0, 4)):
                lights.append((rnd.randint(x + 8, max(x + 9, x + bw - 8)),
                               rnd.randint(base_y - bh + 8, max(base_y - bh + 9, base_y - 8))))
        x += bw + rnd.randint(14, 70)
    if lit and lit_limit:
        for (lx, ly) in lights[:lit_limit]:
            d.rectangle([lx, ly, lx + 3, ly + 4], fill=lit)


def scene(w, h, top, horizon, ground, glow_boxes, far_c, mid_c, near_c, seed, lit=None, haze_c=None):
    img = vgrad(w, h, top, horizon)
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(h * 0.68), w, h], fill=ground)
    img = glow(img, glow_boxes)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    skyline(ImageDraw.Draw(layer), w, int(h * 0.68), far_c, seed, lit, 26)
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, layer)
    if haze_c:
        img = haze(img, haze_c, 46, int(h * 0.58), int(h * 0.74))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    tanks(dl, int(w * 0.06), int(h * 0.82), mid_c, [(150, 120), (110, 90)])
    pipes(dl, int(w * 0.30), int(h * 0.80), int(w * 0.22), mid_c)
    containers(dl, int(w * 0.62), int(h * 0.82), 4, 2, mid_c)
    layer = layer.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, layer)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    crane(dl, int(w * 0.74), int(h * 1.02), int(h * 0.62), int(w * 0.24), near_c)
    crane(dl, int(w * 0.46), int(h * 1.05), int(h * 0.46), -int(w * 0.20), near_c, counter=60)
    containers(dl, -30, int(h * 1.02), 5, 3, near_c)
    img = Image.alpha_composite(img, layer)
    return img


def make_backgrounds():
    w, h = 1920, 1080
    # night: cold blue harbor
    img = scene(w, h, (7, 11, 19), (34, 56, 84), (9, 13, 19),
                [(300, 480, 1800, 900, (70, 130, 200), 120), (1100, 560, 2200, 1000, (53, 182, 217), 70)],
                (26, 38, 56), (16, 24, 36), (8, 12, 18), 11, lit=(150, 210, 245), haze_c=(46, 82, 128))
    img = bokeh(img, [(1480, 320, 150, 20), (1180, 640, 90, 16), (420, 780, 190, 12)], (90, 160, 230))
    img = add_noise(img)
    vignette(img, 0.42).save(os.path.join(BG, "night.png"))
    # dusk: teal sky with warm horizon
    img = scene(w, h, (14, 26, 34), (86, 62, 44), (12, 12, 14),
                [(0, 520, 1600, 950, (224, 123, 57), 130), (1000, 580, 2300, 1000, (53, 150, 190), 60)],
                (38, 42, 46), (23, 25, 28), (11, 12, 13), 23, lit=(255, 195, 125), haze_c=(170, 100, 55))
    img = bokeh(img, [(340, 300, 120, 14), (1620, 420, 150, 12)], (200, 170, 140))
    img = add_noise(img)
    vignette(img, 0.42).save(os.path.join(BG, "dusk.png"))
    # ember: amber industrial night
    img = scene(w, h, (24, 12, 8), (96, 44, 18), (12, 8, 7),
                [(400, 500, 1900, 980, (224, 110, 40), 125), (1200, 160, 2200, 700, (150, 70, 25), 70)],
                (42, 24, 16), (26, 15, 12), (12, 8, 7), 37, lit=(255, 175, 95), haze_c=(140, 70, 30))
    img = bokeh(img, [(520, 700, 50, 30), (780, 560, 26, 26), (1450, 320, 80, 18)], (255, 150, 60))
    img = add_noise(img)
    vignette(img, 0.42).save(os.path.join(BG, "ember.png"))

    # aurora: полярное сияние, луна и её отражение в ледяном озере
    img = vgrad(w, h, (4, 8, 20), (14, 30, 48)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = random.Random(57)
    for i in range(260):  # плотное звёздное небо
        x, y = rng.randint(0, w), rng.randint(0, int(h * 0.55))
        b = rng.randint(70, 230)
        r = rng.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + r, y + r], fill=(b, b, min(255, b + 25)))
    # луна с гало
    mx, my, mr = int(w * 0.78), int(h * 0.16), 58
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([mx - mr * 3, my - mr * 3, mx + mr * 3, my + mr * 3], fill=(190, 215, 255, 60))
    halo = halo.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, halo)
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(225, 235, 250))
    d.ellipse([mx - 18, my - 30, mx - 2, my - 14], fill=(200, 212, 235))
    d.ellipse([mx + 8, my + 10, mx + 26, my + 28], fill=(198, 210, 233))
    # сияние: 3 волнистые ленты
    aurora = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    da = ImageDraw.Draw(aurora)
    for band, (col, base_y, amp) in enumerate([
        ((60, 240, 190, 110), int(h * 0.20), 110),
        ((70, 160, 255, 80), int(h * 0.26), 90),
        ((180, 90, 255, 60), int(h * 0.33), 70),
    ]):
        pts = []
        for x in range(-100, w + 200, 100):
            pts.append((x, base_y + int(amp * math.sin(x / 300 + band * 2))))
        da.polygon(pts + [(w + 200, base_y + 400), (-100, base_y + 400)], fill=col)
    # вертикальные лучи сияния
    for x in range(0, w, 44):
        ln = rng.randint(60, 190)
        a = rng.randint(20, 60)
        da.line([(x, int(h * 0.18) + rng.randint(-40, 40)), (x, int(h * 0.18) + ln)], fill=(90, 240, 200, a), width=3)
    aurora = aurora.filter(ImageFilter.GaussianBlur(38))
    img = Image.alpha_composite(img, aurora)
    # снежные горы (3 слоя с подсветкой от сияния)
    for i, (col, base, amp, blur) in enumerate([
        ((34, 52, 78), 62, 130, 3), ((22, 34, 52), 72, 110, 1), ((12, 18, 30), 82, 80, 0),
    ]):
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dm = ImageDraw.Draw(layer)
        pts = [(0, h)]
        x = -50
        while x < w + 50:
            peak = int(h * base / 100) - rng.randint(0, int(h * amp / 100))
            pts += [(x, peak), (x + 170, int(h * base / 100) + rng.randint(0, 40))]
            x += 170
        pts += [(w, h)]
        dm.polygon(pts, fill=col)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img = Image.alpha_composite(img, layer)
    # ледяное озеро с отражением луны
    d = ImageDraw.Draw(img)
    lake_y = int(h * 0.87)
    d.rectangle([0, lake_y, w, h], fill=(16, 26, 42))
    refl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(refl)
    for k in range(9):
        yy = lake_y + 10 + k * 24
        ww = 120 - k * 8
        dr.ellipse([mx - ww, yy, mx + ww, yy + 8], fill=(200, 220, 255, 40 - k * 3))
    refl = refl.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, refl)
    img = add_noise(img)
    vignette(img, 0.4).save(os.path.join(BG, "aurora.png"))

    # mountains: закатные пики, солнце с лучами, дымка
    img = vgrad(w, h, (28, 16, 52), (255, 130, 80)).convert("RGBA")
    # солнце и гало
    sun = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    sx, sy, sr = int(w * 0.64), int(h * 0.48), 90
    ds.ellipse([sx - sr * 2, sy - sr * 2, sx + sr * 2, sy + sr * 2], fill=(255, 170, 90, 110))
    sun = sun.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img, sun)
    d = ImageDraw.Draw(img)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 225, 160))
    # пики: 4 слоя, дальние подсвечены закатом
    ridge_colors = [(120, 70, 110), (86, 50, 86), (54, 32, 60), (26, 16, 34)]
    for i, (col, base, amp) in enumerate(zip(ridge_colors, [46, 56, 66, 76], [150, 120, 90, 70])):
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dm = ImageDraw.Draw(layer)
        pts = [(0, h)]
        x = -50
        while x < w + 60:
            peak = int(h * base / 100) - rng.randint(0, int(h * amp / 100))
            pts += [(x, peak), (x + 230, int(h * base / 100) + rng.randint(0, 50))]
            x += 230
        pts += [(w, h)]
        dm.polygon(pts, fill=col + (255,))
        # снежные шапки на дальних пиках
        if i < 2:
            dm2 = ImageDraw.Draw(layer)
            px_pts = pts[1:-1]
            for j in range(0, len(px_pts) - 1, 2):
                peak_x, peak_y = px_pts[j]
                if rng.random() > 0.35:
                    dm2.polygon([(peak_x - 26, peak_y + 30), (peak_x, peak_y), (peak_x + 26, peak_y + 30),
                                 (peak_x + 16, peak_y + 46), (peak_x - 16, peak_y + 46)],
                                fill=(255, 200, 170, 180) if i == 0 else (210, 150, 140, 120))
        if i < 2:
            layer = layer.filter(ImageFilter.GaussianBlur(1.5))
        img = Image.alpha_composite(img, layer)
    img = haze(img, (220, 110, 70), 50, int(h * 0.5), int(h * 0.7))
    img = add_noise(img)
    vignette(img, 0.38).save(os.path.join(BG, "mountains.png"))

    # forest: туманные ели с мягким лунным светом
    img = vgrad(w, h, (8, 16, 22), (26, 46, 38)).convert("RGBA")
    moon_glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(moon_glow).ellipse(
        [int(w * 0.15), int(h * 0.05), int(w * 0.15) + 900, int(h * 0.05) + 700],
        fill=(150, 220, 190, 55))
    moon_glow = moon_glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.alpha_composite(img, moon_glow)
    # 5 слоёв елей с растущей непрозрачностью
    for layer_i in range(5):
        shade = [(30, 52, 46, 45), (24, 44, 38, 90), (18, 34, 30, 140), (12, 24, 20, 195), (6, 14, 12, 235)][layer_i]
        layer2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer2)
        x = -70
        while x < w + 60:
            tw = int(30 * (1.6 - layer_i * 0.28))
            th = int(380 * (1.15 - layer_i * 0.2))
            base_y = int(h * (0.66 + layer_i * 0.085))
            top_y = base_y - th
            pts = [(x, base_y)]
            steps = 8
            for s in range(1, steps + 1):
                ww = int(tw * (s / steps))
                yy = top_y + int((base_y - top_y) * (1 - s / steps))
                pts += [(x + ww, yy + 18), (x + int(tw * 0.4), yy)]
            pts += [(x + tw, base_y)]
            dl.polygon(pts, fill=shade)
            x += tw + int(70 * (1.2 - layer_i * 0.2))
        layer2 = layer2.filter(ImageFilter.GaussianBlur(3.5 - layer_i * 0.7))
        img = Image.alpha_composite(img, layer2)
    img = haze(img, (70, 130, 110), 46, int(h * 0.52), int(h * 0.78))
    img = add_noise(img)
    vignette(img, 0.42).save(os.path.join(BG, "forest.png"))

    # cyber: synthwave — солнце с полосами, сетка, сканлайны
    img = vgrad(w, h, (5, 8, 18), (28, 10, 46)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng2 = random.Random(1337)
    for i in range(200):
        x, y = rng2.randint(0, w), rng2.randint(0, int(h * 0.45))
        b = rng2.randint(120, 230)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, b))
    horizon = int(h * 0.58)
    # ретро-солнце с горизонтальными вырезами
    sun2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dsn = ImageDraw.Draw(sun2)
    cx2, cy2, cr2 = w // 2, horizon - 10, 190
    grad_steps = 22
    for g in range(grad_steps):
        t = g / grad_steps
        col = (int(255 - 40 * t), int(120 + 100 * t), int(80 + 120 * t), 255)
        yy = cy2 - cr2 + int(2 * cr2 * t)
        hh = max(1, int(2 * cr2 / grad_steps) + 1)
        dsn.rectangle([cx2 - cr2, yy, cx2 + cr2, yy + hh], fill=col)
    dsn.ellipse([cx2 - cr2, cy2 - cr2, cx2 + cr2, cy2 + cr2], fill=None)
    # вырезаем полосы из солнца (маска)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([cx2 - cr2, cy2 - cr2, cx2 + cr2, cy2 + cr2], fill=255)
    for k, y_off in enumerate(range(0, cr2 * 2, 26)):
        yy = cy2 + y_off - cr2 // 2
        ImageDraw.Draw(mask).rectangle([0, yy + k * 3, w, yy + k * 3 + 6 + k], fill=0)
    sun2.putalpha(Image.composite(sun2.split()[3], Image.new("L", (w, h), 0), mask))
    sun_glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sun_glow).ellipse([cx2 - cr2 * 1.6, cy2 - cr2 * 1.6, cx2 + cr2 * 1.6, cy2 + cr2 * 1.6], fill=(255, 90, 160, 70))
    sun_glow = sun_glow.filter(ImageFilter.GaussianBlur(100))
    img = Image.alpha_composite(img, sun_glow)
    img = Image.alpha_composite(img, sun2)
    d = ImageDraw.Draw(img)
    d.rectangle([0, horizon, w, h], fill=(8, 6, 20))
    for gx in range(-w, w * 2, 90):  # сетка перспективой из центра
        d.line([(w // 2 + (gx - w // 2), horizon), (w // 2 + (gx - w // 2) * 4, h)], fill=(255, 60, 180, 40), width=2)
    for gy in range(horizon, h, 30):
        t = (gy - horizon) / (h - horizon)
        a = int(35 + 110 * t)
        d.line([(0, gy), (w, gy)], fill=(255, 60, 180, a), width=1)
    neon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dn = ImageDraw.Draw(neon)
    dn.rectangle([0, horizon - 3, w, horizon], fill=(120, 240, 255, 160))
    neon = neon.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, neon)
    # сканлайны
    d = ImageDraw.Draw(img)
    for sy2 in range(0, h, 4):
        d.line([(0, sy2), (w, sy2)], fill=(0, 0, 0, 22), width=1)
    img = add_noise(img)
    vignette(img, 0.42).save(os.path.join(BG, "cyber.png"))
    print("backgrounds ok")


def sys_font(bold=False, size=20):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def make_installer_art():
    # sidebar 164x314
    img = gradient((164, 314), (18, 30, 46), (7, 10, 14), angle=18).convert("RGB")
    img = add_noise(img, sigma=10, opacity=0.10).convert("RGB")
    d = ImageDraw.Draw(img)
    cube(d, 82, 96, 44, (64, 150, 255), (28, 84, 190), (18, 56, 130))
    d.line([(82, 52), (126, 77), (126, 121), (82, 146), (38, 121), (38, 77), (82, 52)],
           fill=(150, 200, 255), width=2)
    d.line([(38, 77), (82, 102), (126, 77)], fill=(150, 200, 255), width=2)
    d.line([(82, 102), (82, 146)], fill=(150, 200, 255), width=2)
    f1 = sys_font(bold=True, size=17)
    f2 = sys_font(size=11)
    d.text((82, 236), "MineDash", font=f1, fill=(238, 242, 245), anchor="mm")
    d.text((82, 256), "Launcher", font=f2, fill=(125, 136, 145), anchor="mm")
    d.rectangle([62, 276, 102, 278], fill=(53, 182, 217))
    img.save(os.path.join(BUILD, "installer-sidebar.bmp"))
    # header 150x57
    img = gradient((150, 57), (16, 26, 40), (8, 11, 15), angle=10).convert("RGB")
    d = ImageDraw.Draw(img)
    cube(d, 26, 28, 15, (64, 150, 255), (28, 84, 190), (18, 56, 130))
    f = sys_font(bold=True, size=14)
    d.text((46, 28), "MineDash", font=f, fill=(238, 242, 245), anchor="lm")
    img.save(os.path.join(BUILD, "installer-header.bmp"))
    print("installer art ok")


if __name__ == "__main__":
    ensure_dirs()
    ensure_fonts()
    make_icon()
    make_default_skin()
    make_backgrounds()
    make_installer_art()
    print("all assets generated")
