"""Фоны MineDash Launcher v3 — органичный, «ручной» вид.
Запуск: python tools/gen-bg3.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")
W, H = 1920, 1080


# ─── утилиты ────────────────────────────────────────────────────────────────
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(w, h, top, bottom, stop=0.7):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(int(h * stop), h):
        t = (y - h * stop) / (h * (1 - stop))
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, t))
    return img


def glow(img, cx, cy, rx, ry, col, alpha, blur=80):
    layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (alpha,))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


def grain(img, sigma=12, opacity=0.06):
    noise = Image.effect_noise((img.width, img.height), sigma).convert("RGBA")
    noise.putalpha(int(255 * opacity))
    return Image.alpha_composite(img.convert("RGBA"), noise)


def vignette(img, strength=0.35):
    mask = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(mask).ellipse(
        [-int(img.width * 0.2), -int(img.height * 0.2),
         int(img.width * 1.2), int(img.height * 1.2)], fill=255)
    black = Image.new("RGBA", (img.width, img.height), (0, 0, 0, int(255 * strength)))
    return Image.composite(img.convert("RGBA"), black, mask)


def organic_blob(d, cx, cy, rx, ry, col, rng, irregularity=0.3):
    """Неровный органичный blob вместо идеального эллипса."""
    pts = []
    n = rng.randint(10, 16)
    for i in range(n):
        ang = 2 * math.pi * i / n
        r_var = 1 + rng.uniform(-irregularity, irregularity)
        px = cx + int(rx * r_var * math.cos(ang))
        py = cy + int(ry * r_var * math.sin(ang))
        pts.append((px, py))
    d.polygon(pts, fill=col)


def rough_line(d, p1, p2, col, width, rng, jitter=3):
    """Линия с лёгким дрожанием — как нарисованная от руки."""
    x1, y1 = p1
    x2, y2 = p2
    steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / 8))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t + rng.uniform(-jitter, jitter)
        y = y1 + (y2 - y1) * t + rng.uniform(-jitter, jitter)
        pts.append((int(x), int(y)))
    d.line(pts, fill=col, width=width)


# ─── OCEAN: глубоководный мир ───────────────────────────────────────────────
def ocean():
    rng = random.Random(7)
    img = vgrad(W, H, (3, 22, 42), (1, 8, 18)).convert("RGBA")

    # мягкие световые столбы — не прямые, а слегка изогнутые
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(5):
        x0 = rng.randint(150, W - 150)
        lean = rng.randint(-60, 60)
        spread = rng.randint(60, 180)
        a = rng.randint(14, 32)
        pts = [(x0 - 15, 0), (x0 + 15, 0),
               (x0 + lean + spread, H), (x0 + lean - spread, H)]
        dr.polygon(pts, fill=(100, 190, 240, a))
    rays = rays.filter(ImageFilter.GaussianBlur(35))
    img = Image.alpha_composite(img, rays)

    # пузыри — разного размера, не идеальные круги
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    for _ in range(45):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(2, 12)
        a = rng.randint(25, 80)
        # слегка сплюснутые
        db.ellipse([x - r, y - int(r * 0.85), x + r, y + int(r * 0.85)],
                   outline=(140, 210, 250, a), width=1)
        if r > 6:
            db.ellipse([x - r + 3, y - r + 2, x - r + 5, y - r + 4],
                       fill=(190, 235, 255, a))
    img = Image.alpha_composite(img, bub)

    # рыбы — силуэты с неровными краями
    fish = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(fish)
    for _ in range(10):
        x, y = rng.randint(50, W - 50), rng.randint(int(H * 0.25), int(H * 0.75))
        s = rng.randint(14, 38)
        flip = rng.choice([1, -1])
        a = rng.randint(60, 140)
        # тело — неровный овал
        organic_blob(df, x, y, s, int(s * 0.45), (6, 16, 34, a), rng, 0.25)
        # хвост
        tx = x + flip * s
        df.polygon([(tx, y), (tx + flip * int(s * 0.6), y - int(s * 0.35)),
                    (tx + flip * int(s * 0.6), y + int(s * 0.35))],
                   fill=(6, 16, 34, a))
    img = Image.alpha_composite(img, fish)

    # водоросли — изогнутые, разной толщины
    d = ImageDraw.Draw(img)
    for x in range(0, W, rng.randint(50, 90)):
        hgt = rng.randint(50, 160)
        sway = rng.randint(-20, 20)
        thick = rng.choice([2, 3, 4, 5])
        pts = [(x, H)]
        for k in range(6):
            yy = H - int(hgt * k / 6)
            xx = x + int(sway * math.sin(k * 1.1 + rng.uniform(0, 0.5)))
            pts.append((xx, yy))
        d.line(pts, fill=(8, 45, 38, rng.randint(80, 140)), width=thick)

    img = glow(img, W // 3, 0, 450, 220, (70, 170, 240), 35, 110)
    img = grain(img)
    vignette(img, 0.42).save(os.path.join(BG, "ocean.png"))
    print("ocean ok")


# ─── DESERT: закатные дюны ──────────────────────────────────────────────────
def desert():
    rng = random.Random(21)
    img = vgrad(W, H, (55, 18, 8), (240, 130, 55)).convert("RGBA")

    # солнце — не идеальный круг, с неровным краем
    sx, sy, sr = int(W * 0.48), int(H * 0.5), 140
    img = glow(img, sx, sy, sr * 2.8, sr * 2.8, (250, 150, 50), 70, 130)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    organic_blob(ds, sx, sy, sr, sr, (255, 205, 115, 255), rng, 0.06)
    img = Image.alpha_composite(img, sun)

    # дюны — плавные, но с лёгкой неровностью
    for i, (col, base, amp, freq, phase) in enumerate([
        ((205, 125, 62), 66, 38, 2.1, 0.3), ((175, 100, 48), 73, 30, 1.7, 1.8),
        ((135, 75, 36), 80, 22, 2.5, 3.2), ((92, 52, 26), 87, 14, 1.9, 4.8),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 8):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase))
            )
            # лёгкий шум на кромке
            y += rng.randint(-2, 2)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        if i < 2:
            crest = [(x, y) for x, y in pts[1:-1]]
            dl.line(crest, fill=(250, 195, 115, 85), width=2)
        img = Image.alpha_composite(img, layer)

    # кактусы — неровные, с текстурой
    d = ImageDraw.Draw(img)
    for cx in [int(W * 0.1), int(W * 0.88)]:
        cy = int(H * 0.9)
        # ствол
        rough_line(d, (cx, cy), (cx, cy - 75), (28, 48, 28), 14, rng, 2)
        # ветки
        rough_line(d, (cx, cy - 50), (cx - 25, cy - 50), (28, 48, 28), 10, rng, 2)
        rough_line(d, (cx - 25, cy - 50), (cx - 25, cy - 70), (28, 48, 28), 8, rng, 2)
        rough_line(d, (cx, cy - 40), (cx + 22, cy - 40), (28, 48, 28), 10, rng, 2)
        rough_line(d, (cx + 22, cy - 40), (cx + 22, cy - 58), (28, 48, 28), 8, rng, 2)

    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, "desert.png"))
    print("desert ok")


# ─── SPACE: глубокий космос ─────────────────────────────────────────────────
def space():
    rng = random.Random(42)
    img = Image.new("RGBA", (W, H), (2, 3, 10))
    d = ImageDraw.Draw(img)

    # звёзды — разной яркости, некоторые с лёгким свечением
    for _ in range(400):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(50, 240)
        sz = rng.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + sz, y + sz], fill=(b, b, min(255, b + 20)))
    # яркие звёзды с лучами
    for _ in range(20):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(200, 255)
        d.ellipse([x, y, x + 2, y + 2], fill=(b, b, 255))
        ln = rng.randint(3, 6)
        d.line([(x - ln, y + 1), (x + ln + 2, y + 1)], fill=(b, b, 255, 60))
        d.line([(x + 1, y - ln), (x + 1, y + ln + 2)], fill=(b, b, 255, 60))

    # туманности — органичные, не идеальные круги
    for cx, cy, rx, ry, col, a in [
        (int(W * 0.2), int(H * 0.3), 380, 260, (110, 35, 170), 30),
        (int(W * 0.75), int(H * 0.55), 320, 220, (25, 70, 170), 28),
        (int(W * 0.5), int(H * 0.12), 260, 160, (170, 55, 75), 22),
    ]:
        neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dn = ImageDraw.Draw(neb)
        organic_blob(dn, cx, cy, rx, ry, col + (a,), rng, 0.35)
        neb = neb.filter(ImageFilter.GaussianBlur(60))
        img = Image.alpha_composite(img, neb)

    # планета с кольцами — с текстурой поверхности
    px, py, pr = int(W * 0.6), int(H * 0.42), 120
    img = glow(img, px, py, pr * 1.9, pr * 1.9, (50, 110, 190), 45, 65)
    d = ImageDraw.Draw(img)
    # заднее кольцо
    d.ellipse([px - int(pr * 1.65), py - int(pr * 0.32), px + int(pr * 1.65), py + int(pr * 0.32)],
              outline=(130, 150, 195, 90), width=7)
    # планета
    organic_blob(d, px, py, pr, pr, (38, 65, 125, 255), rng, 0.04)
    # полосы на планете — неровные
    for k in range(5):
        yy = py - pr + int(2 * pr * (k + 0.5) / 5)
        half_w = int(pr * math.sqrt(max(0, 1 - ((yy - py) / pr) ** 2)))
        rough_line(d, (px - half_w, yy), (px + half_w, yy), (55, 95, 165, 140), 5, rng, 2)
    # переднее кольцо
    d.arc([px - int(pr * 1.65), py - int(pr * 0.32), px + int(pr * 1.65), py + int(pr * 0.32)],
          start=25, end=155, fill=(150, 170, 215, 130), width=9)
    # луна
    mx, my, mr = int(W * 0.22), int(H * 0.22), 20
    organic_blob(d, mx, my, mr, mr, (175, 175, 185, 255), rng, 0.08)
    organic_blob(d, mx - 5, my - 4, 5, 4, (145, 145, 155, 200), rng, 0.15)

    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, "space.png"))
    print("space ok")


# ─── CITY: ночной мегаполис ─────────────────────────────────────────────────
def city():
    rng = random.Random(63)
    img = vgrad(W, H, (7, 9, 16), (14, 16, 26)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # редкие звёзды
    for _ in range(60):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.25))
        b = rng.randint(60, 150)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 15)))

    # дальний город — силуэты разной высоты
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(far)
    x = 0
    while x < W:
        bw = rng.randint(35, 90)
        bh = rng.randint(80, 280)
        df.rectangle([x, int(H * 0.55) - bh, x + bw, int(H * 0.55)], fill=(12, 16, 26, 255))
        # окна — не все горят, разные цвета
        for wy in range(int(H * 0.55) - bh + 6, int(H * 0.55) - 6, 12):
            for wx in range(x + 5, x + bw - 5, 10):
                if rng.random() > 0.65:
                    col = rng.choice([(250, 195, 75), (90, 170, 245), (250, 115, 75)])
                    df.rectangle([wx, wy, wx + 4, wy + 6], fill=col + (rng.randint(50, 170),))
        x += bw + rng.randint(3, 18)
    far = far.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, far)

    # ближний ряд — крупнее, темнее
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    x = -20
    while x < W + 20:
        bw = rng.randint(70, 170)
        bh = rng.randint(180, 480)
        dn.rectangle([x, H - bh, x + bw, H], fill=(9, 11, 18, 255))
        for wy in range(H - bh + 10, H - 18, 16):
            for wx in range(x + 7, x + bw - 7, 14):
                if rng.random() > 0.55:
                    col = rng.choice([(250, 185, 65), (75, 155, 245), (250, 95, 55), (170, 245, 110)])
                    dn.rectangle([wx, wy, wx + 6, wy + 8], fill=col + (rng.randint(70, 210),))
        x += bw + rng.randint(5, 28)
    img = Image.alpha_composite(img, near)

    # неон — неровные вывески
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dne = ImageDraw.Draw(neon)
    for _ in range(7):
        x = rng.randint(80, W - 180)
        y = rng.randint(int(H * 0.42), int(H * 0.72))
        nw, nh = rng.randint(55, 150), rng.randint(12, 28)
        col = rng.choice([(250, 45, 115), (45, 195, 250), (250, 195, 45), (110, 250, 75)])
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=3, outline=col + (190,), width=2)
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=3, fill=col + (25,))
    neon = neon.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, neon)
    # свечение от неона
    for _ in range(4):
        x = rng.randint(100, W - 100)
        y = rng.randint(int(H * 0.42), int(H * 0.68))
        col = rng.choice([(250, 45, 115), (45, 195, 250), (250, 195, 45)])
        img = glow(img, x, y, 110, 75, col, 22, 55)

    # дождь — разной длины и наклона
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drn = ImageDraw.Draw(rain)
    for _ in range(280):
        x, y = rng.randint(0, W), rng.randint(0, H)
        ln = rng.randint(10, 32)
        lean = rng.uniform(-4, -1)
        drn.line([(x, y), (x + lean, y + ln)], fill=(140, 175, 215, rng.randint(20, 65)), width=1)
    img = Image.alpha_composite(img, rain)

    # мокрый асфальт с размытыми отражениями
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.88), W, H], fill=(7, 9, 14))
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dref = ImageDraw.Draw(refl)
    for _ in range(35):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.89), H)
        ww = rng.randint(8, 55)
        col = rng.choice([(250, 185, 65), (75, 155, 245), (250, 45, 115)])
        dref.ellipse([x - ww, y, x + ww, y + 2], fill=col + (rng.randint(12, 35),))
    refl = refl.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, refl)

    img = grain(img)
    vignette(img, 0.42).save(os.path.join(BG, "city.png"))
    print("city ok")


# ─── JUNGLE: тропики ────────────────────────────────────────────────────────
def jungle():
    rng = random.Random(17)
    img = vgrad(W, H, (18, 46, 22), (32, 70, 36)).convert("RGBA")

    # тёплый свет
    img = glow(img, int(W * 0.32), int(H * 0.04), 620, 360, (215, 250, 155), 45, 145)
    img = glow(img, int(W * 0.68), int(H * 0.14), 360, 230, (250, 225, 115), 32, 105)

    # деревья — толстые стволы с текстурой, компактные кроны
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(far)
    for _ in range(9):
        x = rng.randint(0, W)
        bh = rng.randint(190, 400)
        tw = rng.randint(65, 105)
        base_y = int(H * 0.7)
        # ствол — неровный
        df.polygon([(x, base_y), (x + tw, base_y),
                    (x + int(tw * 0.78), base_y - bh), (x + int(tw * 0.22), base_y - bh)],
                   fill=(11, 26, 13, 255))
        # текстура коры
        for k in range(3):
            lx = x + int(tw * (0.28 + k * 0.22))
            rough_line(df, (lx, base_y - 15), (lx, base_y - bh + 15), (7, 18, 9, 170), 2, rng, 1)
        # крона — органичные blob-ы
        cx, cy = x + tw // 2, base_y - bh
        for _ in range(4):
            ox = rng.randint(-tw, tw)
            oy = rng.randint(-45, 25)
            rw = rng.randint(int(tw * 0.7), int(tw * 1.4))
            rh = rng.randint(int(rw * 0.55), int(rw * 0.85))
            organic_blob(df, cx + ox, cy + oy, rw, rh, (38, 90, 42, rng.randint(170, 225)), rng, 0.25)
    far = far.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, far)

    # световые лучи
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(4):
        x0 = rng.randint(180, W - 180)
        lean = rng.randint(-40, 40)
        spread = rng.randint(90, 220)
        a = rng.randint(28, 50)
        dr.polygon([(x0 - 25, 0), (x0 + 25, 0),
                    (x0 + lean + spread, H), (x0 + lean - spread, H)],
                   fill=(215, 250, 165, a))
    rays = rays.filter(ImageFilter.GaussianBlur(38))
    img = Image.alpha_composite(img, rays)

    # лианы
    vines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vines)
    for _ in range(12):
        x = rng.randint(0, W)
        ln = rng.randint(140, 420)
        pts = [(x, 0)]
        for k in range(1, 8):
            pts.append((x + int(18 * math.sin(k * 0.75 + rng.uniform(0, 0.4))), int(ln * k / 8)))
        dv.line(pts, fill=(18, 55, 23, rng.randint(90, 190)), width=rng.choice([2, 3, 4]))
        for k in range(2, 7, 2):
            lx, ly = pts[k]
            organic_blob(dv, lx, ly, 7, 4, (28, 75, 28, 140), rng, 0.3)
    img = Image.alpha_composite(img, vines)

    # крупные листья
    leaves = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(leaves)
    for _ in range(9):
        x = rng.randint(-40, W)
        y = rng.choice([rng.randint(0, int(H * 0.28)), rng.randint(int(H * 0.72), H)])
        s = rng.randint(55, 150)
        ang = rng.uniform(0, math.pi * 2)
        pts = []
        for k in range(12):
            t = k / 12
            r = s * math.sin(t * math.pi)
            pts.append((x + int(r * math.cos(ang + t * 0.45)), y + int(r * math.sin(ang + t * 0.45))))
        dl.polygon(pts, fill=(22, 65, 28, rng.randint(150, 220)))
        dl.line([(x, y), (x + int(s * math.cos(ang)), y + int(s * math.sin(ang)))],
                fill=(32, 85, 38, 190), width=2)
    leaves = leaves.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, leaves)

    # светлячки
    spark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(spark)
    for _ in range(30):
        x, y = rng.randint(0, W), rng.randint(int(H * 0.3), int(H * 0.78))
        r = rng.choice([1, 2, 3])
        ds.ellipse([x - r, y - r, x + r, y + r], fill=(235, 250, 175, rng.randint(70, 190)))
    spark = spark.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, spark)

    # туман
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mist)
    for _ in range(7):
        x = rng.randint(-80, W)
        y = rng.randint(int(H * 0.72), int(H * 0.88))
        dm.rounded_rectangle([x, y, x + rng.randint(280, 650), y + rng.randint(28, 75)],
                             radius=35, fill=(130, 210, 150, rng.randint(28, 55)))
    mist = mist.filter(ImageFilter.GaussianBlur(48))
    img = Image.alpha_composite(img, mist)

    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, "jungle.png"))
    print("jungle ok")


# ─── SNOW: зимняя ночь ──────────────────────────────────────────────────────
def snow():
    rng = random.Random(5)
    img = vgrad(W, H, (9, 14, 28), (18, 28, 46)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # звёзды
    for _ in range(130):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.38))
        b = rng.randint(70, 190)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 15)))
    # луна
    mx, my, mr = int(W * 0.78), int(H * 0.11), 38
    img = glow(img, mx, my, mr * 3, mr * 3, (195, 205, 250), 48, 72)
    d = ImageDraw.Draw(img)
    organic_blob(d, mx, my, mr, mr, (215, 225, 248, 255), rng, 0.05)
    organic_blob(d, mx - 8, my - 6, 7, 6, (185, 195, 215, 180), rng, 0.15)

    # ели — неровные, разной высоты
    for i in range(13):
        x = rng.randint(0, W)
        th = rng.randint(70, 190)
        base_y = int(H * 0.6)
        col = (13, 23, 33, 190)
        pts = [(x, base_y)]
        for s in range(1, 6):
            ww = int(13 * s / 5) + rng.randint(-2, 2)
            yy = base_y - int(th * (1 - s / 6))
            pts += [(x + ww, yy + 8), (x + int(ww * 0.4), yy)]
        pts += [(x + 13, base_y)]
        d.polygon(pts, fill=col)

    # дома — брёвна, окна, дым
    for hx, hw, hh in [(int(W * 0.08), 175, 125), (int(W * 0.33), 215, 155),
                        (int(W * 0.6), 155, 115), (int(W * 0.8), 195, 135)]:
        hy = int(H * 0.72)
        d.rectangle([hx, hy - hh, hx + hw, hy], fill=(65, 50, 42))
        # брёвна
        for ly in range(hy - hh + 8, hy, 16):
            rough_line(d, (hx, ly), (hx + hw, ly), (50, 38, 32), 2, rng, 1)
        # крыша со снегом
        d.polygon([(hx - 18, hy - hh), (hx + hw // 2, hy - hh - 55), (hx + hw + 18, hy - hh)],
                  fill=(55, 46, 42))
        d.polygon([(hx - 18, hy - hh), (hx + hw // 2, hy - hh - 55), (hx + hw + 18, hy - hh),
                   (hx + hw + 18, hy - hh + 9), (hx + hw // 2, hy - hh - 46), (hx - 18, hy - hh + 9)],
                  fill=(225, 235, 248))
        # окна
        for wx in range(hx + 18, hx + hw - 18, 48):
            for wy in range(hy - hh + 22, hy - 18, 52):
                img = glow(img, wx + 13, wy + 15, 38, 32, (250, 175, 55), 32, 22)
                d = ImageDraw.Draw(img)
                d.rectangle([wx, wy, wx + 26, wy + 30], fill=(250, 195, 85))
                d.rectangle([wx + 3, wy + 3, wx + 23, wy + 27], fill=(250, 215, 125))
                d.line([(wx + 13, wy), (wx + 13, wy + 30)], fill=(85, 55, 38), width=3)
                d.line([(wx, wy + 15), (wx + 26, wy + 15)], fill=(85, 55, 38), width=3)
        # дверь
        d.rectangle([hx + hw // 2 - 14, hy - 48, hx + hw // 2 + 14, hy], fill=(75, 52, 33))
        d.ellipse([hx + hw // 2 + 5, hy - 28, hx + hw // 2 + 9, hy - 24], fill=(195, 175, 95))
        # дым из трубы
        cx = hx + int(hw * 0.7)
        cy = hy - hh - 50
        for k in range(5):
            ox = rng.randint(-8, 8)
            oy = -k * 14
            r = 6 + k * 3
            a = max(20, 60 - k * 10)
            smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(smoke).ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r],
                                          fill=(180, 185, 195, a))
            smoke = smoke.filter(ImageFilter.GaussianBlur(6))
            img = Image.alpha_composite(img, smoke)
            d = ImageDraw.Draw(img)

    # снег
    d.rectangle([0, int(H * 0.72), W, H], fill=(195, 210, 230))
    for _ in range(18):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.73), H)
        w2 = rng.randint(35, 140)
        d.ellipse([x - w2, y - 8, x + w2, y + 12], fill=(205, 220, 240))
    # падающий снег
    snowfl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsf = ImageDraw.Draw(snowfl)
    for _ in range(180):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.choice([1, 2, 2, 3])
        dsf.ellipse([x, y, x + r, y + r], fill=(235, 240, 250, rng.randint(90, 210)))
    img = Image.alpha_composite(img, snowfl)

    img = grain(img)
    vignette(img, 0.4).save(os.path.join(BG, "snow.png"))
    print("snow ok")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    ocean()
    desert()
    space()
    city()
    jungle()
    snow()
    print("all backgrounds v3 ok")
