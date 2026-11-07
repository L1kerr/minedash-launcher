"""Фоны MineDash Launcher v5 — 9 тем, hand-crafted painterly look.
Оставлены: space, desert, city. Добавлены: volcano, aurora, canyon, autumn, storm, ruins.
Запуск: python tools/gen-bg5.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")
W, H = 1920, 1080


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, t))
    return img


def glow(img, cx, cy, rx, ry, col, alpha, blur=80):
    layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (alpha,))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


def grain(img, sigma=14, opacity=0.05):
    noise = Image.effect_noise((img.width, img.height), sigma).convert("RGBA")
    noise.putalpha(int(255 * opacity))
    return Image.alpha_composite(img.convert("RGBA"), noise)


def vignette(img, strength=0.35):
    mask = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(mask).ellipse(
        [-int(img.width * 0.25), -int(img.height * 0.25),
         int(img.width * 1.25), int(img.height * 1.25)], fill=255)
    black = Image.new("RGBA", (img.width, img.height), (0, 0, 0, int(255 * strength)))
    return Image.composite(img.convert("RGBA"), black, mask)


def blob(d, cx, cy, rx, ry, col, rng, irr=0.3, n=None):
    n = n or rng.randint(12, 20)
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        r = 1 + rng.uniform(-irr, irr)
        pts.append((cx + int(rx * r * math.cos(ang)), cy + int(ry * r * math.sin(ang))))
    d.polygon(pts, fill=col)


def brush(d, x1, y1, x2, y2, col, w, rng, jit=2):
    steps = max(3, int(math.hypot(x2 - x1, y2 - y1) / 6))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((int(x1 + (x2 - x1) * t + rng.uniform(-jit, jit)),
                    int(y1 + (y2 - y1) * t + rng.uniform(-jit, jit))))
    d.line(pts, fill=col, width=w)


def save(img, name):
    img = grain(img)
    vignette(img, 0.36).save(os.path.join(BG, name + ".png"))
    print(name, "ok")


# ─── SPACE ─────────────────────────────────────────────────────────────────
def space():
    rng = random.Random(42)
    img = Image.new("RGBA", (W, H), (3, 4, 12))
    d = ImageDraw.Draw(img)
    for _ in range(450):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(60, 245)
        sz = rng.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + sz, y + sz], fill=(b, b, min(255, b + 25)))
    for _ in range(18):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(210, 255)
        d.ellipse([x, y, x + 2, y + 2], fill=(b, b, 255))
        ln = rng.randint(3, 7)
        d.line([(x - ln, y + 1), (x + ln + 2, y + 1)], fill=(b, b, 255, 70))
        d.line([(x + 1, y - ln), (x + 1, y + ln + 2)], fill=(b, b, 255, 70))
    for cx, cy, rx, ry, col, a in [
        (int(W * 0.18), int(H * 0.28), 400, 280, (115, 38, 175), 32),
        (int(W * 0.78), int(H * 0.58), 340, 240, (28, 75, 175), 30),
        (int(W * 0.48), int(H * 0.1), 280, 180, (175, 58, 80), 24),
    ]:
        neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dn = ImageDraw.Draw(neb)
        blob(dn, cx, cy, rx, ry, col + (a,), rng, 0.4)
        neb = neb.filter(ImageFilter.GaussianBlur(65))
        img = Image.alpha_composite(img, neb)
    px, py, pr = int(W * 0.62), int(H * 0.4), 115
    img = glow(img, px, py, pr * 2, pr * 2, (55, 115, 195), 48, 70)
    d = ImageDraw.Draw(img)
    d.ellipse([px - int(pr * 1.7), py - int(pr * 0.35), px + int(pr * 1.7), py + int(pr * 0.35)],
              outline=(135, 155, 200, 95), width=8)
    planet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(planet)
    for r in range(pr, 0, -2):
        t = r / pr
        col = lerp((25, 45, 90), (65, 105, 175), 1 - t)
        dp.ellipse([px - r, py - r, px + r, py + r], fill=col + (255,))
    img = Image.alpha_composite(img, planet)
    d = ImageDraw.Draw(img)
    d.arc([px - int(pr * 1.7), py - int(pr * 0.35), px + int(pr * 1.7), py + int(pr * 0.35)],
          start=20, end=160, fill=(155, 175, 220, 135), width=10)
    mx, my, mr = int(W * 0.2), int(H * 0.2), 22
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(180, 180, 190))
    d.ellipse([mx - 6, my - 5, mx - 2, my - 1], fill=(150, 150, 160))
    save(img, "space")


# ─── DESERT ─────────────────────────────────────────────────────────────────
def desert():
    rng = random.Random(21)
    img = vgrad(W, H, (60, 20, 10), (245, 135, 58)).convert("RGBA")
    sx, sy, sr = int(W * 0.48), int(H * 0.48), 130
    img = glow(img, sx, sy, sr * 3, sr * 3, (250, 155, 55), 75, 140)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    for _ in range(5):
        ox, oy = rng.randint(-8, 8), rng.randint(-8, 8)
        ds.ellipse([sx + ox - sr, sy + oy - sr, sx + ox + sr, sy + oy + sr],
                   fill=(255, 208, 118, 60))
    sun = sun.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, sun)
    for i, (col, base, amp, freq, phase) in enumerate([
        ((208, 128, 64), 65, 42, 2.0, 0.2), ((178, 102, 50), 72, 34, 1.6, 1.7),
        ((138, 78, 38), 79, 26, 2.4, 3.1), ((95, 55, 28), 86, 18, 1.8, 4.6),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 6):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase)))
            y += rng.randint(-1, 1)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        if i < 2:
            crest = [(x, y) for x, y in pts[1:-1]]
            dl.line(crest, fill=(252, 198, 118, 90), width=2)
        img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)
    for cx in [int(W * 0.09), int(W * 0.89)]:
        cy = int(H * 0.91)
        brush(d, cx, cy, cx, cy - 80, (30, 52, 30), 16, rng, 2)
        brush(d, cx, cy - 55, cx - 28, cy - 55, (30, 52, 30), 12, rng, 2)
        brush(d, cx - 28, cy - 55, cx - 28, cy - 78, (30, 52, 30), 10, rng, 2)
        brush(d, cx, cy - 42, cx + 25, cy - 42, (30, 52, 30), 12, rng, 2)
        brush(d, cx + 25, cy - 42, cx + 25, cy - 62, (30, 52, 30), 10, rng, 2)
    save(img, "desert")


# ─── CITY ───────────────────────────────────────────────────────────────────
def city():
    rng = random.Random(63)
    img = vgrad(W, H, (8, 10, 18), (16, 18, 28)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for _ in range(70):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.28))
        b = rng.randint(70, 160)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 18)))
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(far)
    x = 0
    while x < W:
        bw = rng.randint(45, 110)
        bh = rng.randint(100, 320)
        df.rectangle([x, int(H * 0.54) - bh, x + bw, int(H * 0.54)], fill=(13, 17, 27, 255))
        x += bw + rng.randint(5, 22)
    far = far.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, far)
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    x = -30
    while x < W + 30:
        bw = rng.randint(90, 210)
        bh = rng.randint(220, 560)
        dn.rectangle([x, H - bh, x + bw, H], fill=(11, 13, 21, 255))
        for wy in range(H - bh + 14, H - 22, 20):
            for wx in range(x + 10, x + bw - 10, 18):
                if rng.random() > 0.78:
                    col = rng.choice([(250, 185, 65), (75, 155, 245), (250, 95, 55), (170, 245, 110)])
                    a = rng.randint(40, 140)
                    dn.rectangle([wx, wy, wx + 6, wy + 8], fill=col + (a,))
        x += bw + rng.randint(8, 35)
    img = Image.alpha_composite(img, near)
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dne = ImageDraw.Draw(neon)
    for _ in range(5):
        x = rng.randint(100, W - 220)
        y = rng.randint(int(H * 0.42), int(H * 0.68))
        nw, nh = rng.randint(70, 180), rng.randint(16, 32)
        col = rng.choice([(250, 45, 115), (45, 195, 250), (250, 195, 45), (110, 250, 75)])
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=4, outline=col + (180,), width=2)
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=4, fill=col + (22,))
    neon = neon.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, neon)
    for _ in range(3):
        x = rng.randint(130, W - 130)
        y = rng.randint(int(H * 0.42), int(H * 0.62))
        col = rng.choice([(250, 45, 115), (45, 195, 250), (250, 195, 45)])
        img = glow(img, x, y, 130, 85, col, 28, 65)
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drn = ImageDraw.Draw(rain)
    for _ in range(320):
        x, y = rng.randint(0, W), rng.randint(0, H)
        ln = rng.randint(14, 38)
        lean = rng.uniform(-5, -1)
        drn.line([(x, y), (x + lean, y + ln)], fill=(148, 183, 223, rng.randint(28, 75)), width=1)
    img = Image.alpha_composite(img, rain)
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.88), W, H], fill=(9, 11, 17))
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dref = ImageDraw.Draw(refl)
    for _ in range(40):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.89), H)
        ww = rng.randint(12, 65)
        col = rng.choice([(250, 185, 65), (75, 155, 245), (250, 45, 115)])
        dref.ellipse([x - ww, y, x + ww, y + 2], fill=col + (rng.randint(18, 45),))
    refl = refl.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, refl)
    save(img, "city")


# ─── VOLCANO: ночное извержение ─────────────────────────────────────────────
def volcano():
    rng = random.Random(99)
    img = vgrad(W, H, (12, 6, 10), (35, 12, 8)).convert("RGBA")

    # звёзды
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.3))
        b = rng.randint(60, 150)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 15)))

    # свечение вулкана
    vx = int(W * 0.5)
    img = glow(img, vx, int(H * 0.45), 500, 350, (250, 90, 20), 55, 160)
    img = glow(img, vx, int(H * 0.5), 250, 180, (255, 160, 40), 65, 90)

    # гора — неровный силуэт
    mtn = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mtn)
    pts = [(0, H)]
    for x in range(0, W + 20, 12):
        t = x / W
        # форма вулкана: подъём к центру, кратер
        base = int(H * 0.92)
        peak = int(H * 0.38)
        dist = abs(t - 0.5) * 2
        y = int(base - (base - peak) * max(0.0, 1 - dist) ** 1.6)
        # кратер — провал в центре
        if dist < 0.08:
            y += int(30 * (1 - dist / 0.08))
        y += rng.randint(-3, 3)
        pts.append((x, y))
    pts += [(W, H)]
    dm.polygon(pts, fill=(18, 10, 12, 255))
    # текстура склонов — штрихи
    for _ in range(40):
        x1 = rng.randint(int(W * 0.2), int(W * 0.8))
        y1 = rng.randint(int(H * 0.5), int(H * 0.85))
        x2 = x1 + rng.randint(-40, 40)
        y2 = y1 + rng.randint(20, 60)
        brush(dm, x1, y1, x2, y2, (28, 16, 18, 140), 2, rng, 2)
    img = Image.alpha_composite(img, mtn)

    # лава из кратера — потоки вниз
    lava = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lava)
    for _ in range(6):
        x0 = vx + rng.randint(-60, 60)
        y0 = int(H * 0.42)
        pts = [(x0, y0)]
        x, y = x0, y0
        for _ in range(12):
            x += rng.randint(-25, 25)
            y += rng.randint(25, 55)
            pts.append((x, y))
        dl.line(pts, fill=(255, 120, 25, rng.randint(150, 230)), width=rng.choice([3, 4, 5]))
        dl.line(pts, fill=(255, 200, 60, rng.randint(80, 140)), width=1)
    lava = lava.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, lava)

    # искры и пепел
    sparks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sparks)
    for _ in range(60):
        x = vx + rng.randint(-200, 200)
        y = rng.randint(int(H * 0.1), int(H * 0.5))
        r = rng.choice([1, 2, 2, 3])
        col = rng.choice([(255, 140, 30), (255, 200, 60), (200, 200, 200)])
        ds.ellipse([x, y, x + r, y + r], fill=col + (rng.randint(80, 220),))
    sparks = sparks.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, sparks)

    # дым
    for _ in range(8):
        x = vx + rng.randint(-120, 120)
        y = rng.randint(int(H * 0.05), int(H * 0.35))
        r = rng.randint(40, 110)
        smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(smoke).ellipse([x - r, y - r, x + r, y + r],
                                      fill=(60, 40, 45, rng.randint(30, 70)))
        smoke = smoke.filter(ImageFilter.GaussianBlur(30))
        img = Image.alpha_composite(img, smoke)

    # передний план — тёмная земля
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.9), W, H], fill=(10, 6, 8))
    save(img, "volcano")


# ─── AURORA: северное сияние ────────────────────────────────────────────────
def aurora():
    rng = random.Random(33)
    img = vgrad(W, H, (4, 8, 22), (10, 18, 38)).convert("RGBA")

    # звёзды
    d = ImageDraw.Draw(img)
    for _ in range(200):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.55))
        b = rng.randint(80, 230)
        sz = rng.choice([1, 1, 2])
        d.ellipse([x, y, x + sz, y + sz], fill=(b, b, min(255, b + 20)))

    # сияние — вертикальные ленты
    aur = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(aur)
    for i in range(5):
        x0 = rng.randint(100, W - 100)
        lean = rng.randint(-100, 100)
        w_band = rng.randint(60, 160)
        col = rng.choice([(40, 220, 140), (60, 180, 220), (120, 220, 100), (80, 200, 180)])
        a = rng.randint(25, 55)
        # лента — изогнутая
        pts = []
        for k in range(14):
            t = k / 13
            y = int(H * 0.05 + t * H * 0.5)
            x = x0 + int(lean * t) + int(40 * math.sin(t * 4 + i))
            pts.append((x - w_band // 2, y))
        for k in range(13, -1, -1):
            t = k / 13
            y = int(H * 0.05 + t * H * 0.5)
            x = x0 + int(lean * t) + int(40 * math.sin(t * 4 + i))
            pts.append((x + w_band // 2, y))
        da.polygon(pts, fill=col + (a,))
    aur = aur.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, aur)

    # горы — снежные вершины
    for i, (col, base, amp, freq, phase) in enumerate([
        ((30, 40, 60), 62, 30, 2.2, 0.5), ((22, 30, 48), 72, 22, 1.8, 2.0),
        ((15, 22, 36), 82, 14, 2.6, 3.5),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 8):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase)))
            y += rng.randint(-2, 2)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        # снег на вершинах
        if i < 2:
            crest = [(x, y) for x, y in pts[1:-1]]
            dl.line(crest, fill=(200, 215, 235, 120), width=3)
        img = Image.alpha_composite(img, layer)

    # луна
    mx, my, mr = int(W * 0.82), int(H * 0.12), 30
    img = glow(img, mx, my, mr * 3, mr * 3, (200, 210, 250), 45, 70)
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(215, 225, 245))
    d.ellipse([mx - 7, my - 5, mx - 3, my - 1], fill=(185, 195, 215))

    save(img, "aurora")


# ─── CANYON: закат в каньоне ────────────────────────────────────────────────
def canyon():
    rng = random.Random(77)
    img = vgrad(W, H, (180, 80, 30), (240, 150, 70)).convert("RGBA")

    # солнце низко
    sx, sy = int(W * 0.5), int(H * 0.55)
    img = glow(img, sx, sy, 300, 200, (255, 200, 100), 60, 120)

    # слои скал — от дальних к ближним
    layers = [
        ((200, 110, 55), 55, 25, 2.0, 0.3),
        ((170, 85, 42), 63, 30, 1.7, 1.5),
        ((140, 68, 34), 71, 22, 2.3, 2.8),
        ((110, 52, 28), 79, 16, 1.9, 4.0),
        ((80, 40, 22), 87, 10, 2.5, 5.2),
    ]
    for i, (col, base, amp, freq, phase) in enumerate(layers):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 6):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase)))
            y += rng.randint(-2, 2)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        # текстура скал — горизонтальные штрихи
        for _ in range(15):
            x1 = rng.randint(0, W - 100)
            y1 = rng.randint(int(H * base / 100) - 20, int(H * base / 100) + 40)
            brush(dl, x1, y1, x1 + rng.randint(40, 120), y1 + rng.randint(-3, 3),
                  (col[0] - 20, col[1] - 15, col[2] - 10, 100), 2, rng, 1)
        img = Image.alpha_composite(img, layer)

    save(img, "canyon")


# ─── AUTUMN: осенний лес ────────────────────────────────────────────────────
def autumn():
    rng = random.Random(55)
    img = vgrad(W, H, (120, 70, 25), (180, 110, 45)).convert("RGBA")

    # тёплый свет
    img = glow(img, int(W * 0.4), int(H * 0.1), 500, 300, (250, 200, 100), 50, 140)

    # деревья — массивные, с широкими кронами
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(trees)
    for _ in range(12):
        x = rng.randint(-60, W)
        tw = rng.randint(80, 160)  # толстые стволы
        base_y = int(H * 0.88)
        top_y = rng.randint(int(H * 0.25), int(H * 0.42))  # кроны ниже
        # ствол — широкий, сужающийся
        dt.polygon([(x, base_y), (x + tw, base_y),
                    (x + int(tw * 0.72), top_y), (x + int(tw * 0.28), top_y)],
                   fill=(65, 42, 26, 255))
        # текстура коры
        for k in range(4):
            lx = x + int(tw * (0.2 + k * 0.2))
            brush(dt, lx, base_y - 20, lx, top_y + 25, (48, 32, 20, 160), 2, rng, 1)
        # крона — большая, многослойная, широкая
        cx, cy = x + tw // 2, top_y
        for _ in range(7):
            ox = rng.randint(-int(tw * 2), int(tw * 2))
            oy = rng.randint(-80, 40)
            rw = rng.randint(int(tw * 1.5), int(tw * 2.8))
            rh = rng.randint(int(rw * 0.5), int(rw * 0.7))
            col = rng.choice([(205, 125, 32), (225, 155, 42), (185, 95, 28), (245, 175, 52)])
            blob(dt, cx + ox, cy + oy, rw, rh, col + (rng.randint(170, 230),), rng, 0.32)
    img = Image.alpha_composite(img, trees)

    # падающие листья
    leaves = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(leaves)
    for _ in range(80):
        x, y = rng.randint(0, W), rng.randint(0, H)
        s = rng.randint(3, 8)
        ang = rng.uniform(0, math.pi * 2)
        col = rng.choice([(220, 140, 35), (240, 160, 45), (200, 100, 25)])
        dl.ellipse([x - s, y - int(s * 0.6), x + s, y + int(s * 0.6)],
                   fill=col + (rng.randint(120, 220),))
    img = Image.alpha_composite(img, leaves)

    # земля — опавшие листья
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.88), W, H], fill=(90, 55, 25))
    for _ in range(120):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.89), H)
        s = rng.randint(2, 6)
        col = rng.choice([(180, 100, 30), (200, 120, 35), (160, 85, 25)])
        d.ellipse([x - s, y - 2, x + s, y + 2], fill=col)

    save(img, "autumn")


# ─── STORM: гроза над морем ─────────────────────────────────────────────────
def storm():
    rng = random.Random(88)
    img = vgrad(W, H, (15, 18, 28), (35, 42, 55)).convert("RGBA")

    # тучи — тёмные массы
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(clouds)
    for _ in range(15):
        x = rng.randint(-100, W)
        y = rng.randint(-50, int(H * 0.35))
        rw = rng.randint(150, 400)
        rh = rng.randint(60, 150)
        blob(dc, x, y, rw, rh, (20, 24, 35, rng.randint(150, 220)), rng, 0.35)
    clouds = clouds.filter(ImageFilter.GaussianBlur(15))
    img = Image.alpha_composite(img, clouds)

    # молнии
    for _ in range(3):
        x0 = rng.randint(int(W * 0.2), int(W * 0.8))
        y0 = rng.randint(int(H * 0.1), int(H * 0.3))
        pts = [(x0, y0)]
        x, y = x0, y0
        for _ in range(8):
            x += rng.randint(-40, 40)
            y += rng.randint(40, 80)
            pts.append((x, y))
        # свечение
        img = glow(img, x0, y0 + 150, 120, 200, (180, 200, 255), 40, 60)
        # сама молния
        bolt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(bolt)
        db.line(pts, fill=(220, 235, 255, 230), width=3)
        db.line(pts, fill=(255, 255, 255, 120), width=1)
        # ветви
        for k in range(2, 6, 2):
            bx, by = pts[k]
            branch = [(bx, by)]
            for _ in range(3):
                bx += rng.randint(-30, 30)
                by += rng.randint(20, 40)
                branch.append((bx, by))
            db.line(branch, fill=(200, 220, 255, 150), width=2)
        bolt = bolt.filter(ImageFilter.GaussianBlur(1))
        img = Image.alpha_composite(img, bolt)

    # море — волны
    for i, (col, base, amp, freq, phase) in enumerate([
        ((25, 35, 50), 68, 8, 3.0, 0.5), ((20, 28, 42), 76, 6, 2.5, 1.8),
        ((15, 22, 34), 84, 4, 3.5, 3.0),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 8):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase)))
            y += rng.randint(-2, 2)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        # блики на волнах
        if i == 0:
            crest = [(x, y) for x, y in pts[1:-1]]
            dl.line(crest, fill=(80, 100, 140, 80), width=2)
        img = Image.alpha_composite(img, layer)

    # дождь
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drn = ImageDraw.Draw(rain)
    for _ in range(400):
        x, y = rng.randint(0, W), rng.randint(0, H)
        ln = rng.randint(15, 40)
        lean = rng.uniform(-8, -3)
        drn.line([(x, y), (x + lean, y + ln)], fill=(150, 170, 200, rng.randint(30, 80)), width=1)
    img = Image.alpha_composite(img, rain)

    save(img, "storm")


# ─── RUINS: древние руины ───────────────────────────────────────────────────
def ruins():
    rng = random.Random(44)
    img = vgrad(W, H, (45, 55, 50), (70, 85, 75)).convert("RGBA")

    # туман
    img = glow(img, int(W * 0.5), int(H * 0.6), 600, 300, (120, 140, 130), 35, 150)

    # колонны — разрушенные
    cols = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cols)
    for i in range(6):
        x = int(W * (0.1 + i * 0.15)) + rng.randint(-20, 20)
        cw = rng.randint(50, 80)
        ch = rng.randint(200, 450)
        base_y = int(H * 0.75)
        # колонна — неровная, с обломанным верхом
        top_y = base_y - ch
        dc.polygon([(x, base_y), (x + cw, base_y),
                    (x + cw + rng.randint(-8, 8), top_y + rng.randint(0, 30)),
                    (x + rng.randint(-8, 8), top_y + rng.randint(0, 30))],
                   fill=(95, 105, 95, 255))
        # каннелюры — вертикальные борозды
        for k in range(4):
            lx = x + int(cw * (0.2 + k * 0.2))
            brush(dc, lx, base_y - 10, lx, top_y + 20, (75, 85, 75, 160), 2, rng, 1)
        # трещины
        for _ in range(3):
            cx = x + rng.randint(5, cw - 5)
            cy = rng.randint(top_y + 30, base_y - 30)
            brush(dc, cx, cy, cx + rng.randint(-15, 15), cy + rng.randint(20, 50),
                  (60, 70, 60, 180), 2, rng, 2)
    img = Image.alpha_composite(img, cols)

    # арка — разрушенная
    ax, ay = int(W * 0.5), int(H * 0.35)
    arch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(arch)
    # левая опора
    da.rectangle([ax - 180, ay, ax - 120, int(H * 0.75)], fill=(90, 100, 90, 255))
    # правая опора (обломанная)
    da.rectangle([ax + 120, ay + 80, ax + 180, int(H * 0.75)], fill=(90, 100, 90, 255))
    # верхняя часть арки — неровная
    pts = []
    for k in range(16):
        t = k / 15
        ang = math.pi * t
        r = 180 + rng.randint(-10, 10)
        pts.append((ax + int(r * math.cos(ang)), ay - int(r * 0.5 * math.sin(ang))))
    da.polygon(pts + [(ax + 180, ay + 80), (ax - 180, ay)], fill=(95, 105, 95, 255))
    img = Image.alpha_composite(img, arch)

    # плющ и мох
    ivy = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    di = ImageDraw.Draw(ivy)
    for _ in range(20):
        x = rng.randint(int(W * 0.2), int(W * 0.8))
        y = rng.randint(int(H * 0.3), int(H * 0.7))
        for _ in range(8):
            blob(di, x, y, rng.randint(8, 20), rng.randint(6, 15),
                 (45, 85, 40, rng.randint(120, 200)), rng, 0.4)
            x += rng.randint(-15, 15)
            y += rng.randint(10, 25)
    img = Image.alpha_composite(img, ivy)

    # земля — трава и камни
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.75), W, H], fill=(55, 70, 50))
    for _ in range(40):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.76), H)
        s = rng.randint(5, 20)
        col = rng.choice([(70, 90, 60), (60, 80, 55), (80, 100, 65)])
        blob(d, x, y, s, int(s * 0.6), col, rng, 0.3)
    # трава
    for _ in range(150):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.76), H)
        h = rng.randint(8, 20)
        lean = rng.randint(-5, 5)
        d.line([(x, y), (x + lean, y - h)], fill=(50, 95, 45, rng.randint(100, 200)), width=1)

    save(img, "ruins")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    space()
    desert()
    city()
    volcano()
    aurora()
    canyon()
    autumn()
    storm()
    ruins()
    print("all backgrounds v5 ok (9 themes)")
