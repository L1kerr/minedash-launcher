"""Фоны MineDash Launcher v4 — painterly, hand-crafted look.
Запуск: python tools/gen-bg4.py
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
    """Organic blob with irregular edges."""
    n = n or rng.randint(12, 20)
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        r = 1 + rng.uniform(-irr, irr)
        pts.append((cx + int(rx * r * math.cos(ang)), cy + int(ry * r * math.sin(ang))))
    d.polygon(pts, fill=col)


def brush(d, x1, y1, x2, y2, col, w, rng, jit=2):
    """Rough brush stroke."""
    steps = max(3, int(math.hypot(x2 - x1, y2 - y1) / 6))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((int(x1 + (x2 - x1) * t + rng.uniform(-jit, jit)),
                    int(y1 + (y2 - y1) * t + rng.uniform(-jit, jit))))
    d.line(pts, fill=col, width=w)


# ─── OCEAN ──────────────────────────────────────────────────────────────────
def ocean():
    rng = random.Random(7)
    img = vgrad(W, H, (8, 42, 72), (2, 12, 24)).convert("RGBA")

    # световые столбы — широкие, мягкие
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(4):
        x0 = rng.randint(200, W - 200)
        lean = rng.randint(-80, 80)
        spread = rng.randint(120, 280)
        a = rng.randint(18, 38)
        dr.polygon([(x0 - 40, 0), (x0 + 40, 0),
                    (x0 + lean + spread, H), (x0 + lean - spread, H)],
                   fill=(120, 200, 250, a))
    rays = rays.filter(ImageFilter.GaussianBlur(50))
    img = Image.alpha_composite(img, rays)

    # пузыри
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    for _ in range(50):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(2, 14)
        a = rng.randint(30, 90)
        db.ellipse([x - r, y - int(r * 0.8), x + r, y + int(r * 0.8)],
                   outline=(150, 215, 255, a), width=1)
        if r > 7:
            db.ellipse([x - r + 3, y - r + 2, x - r + 6, y - r + 5],
                       fill=(200, 240, 255, a))
    img = Image.alpha_composite(img, bub)

    # рыбы — силуэты
    fish = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(fish)
    for _ in range(12):
        x, y = rng.randint(60, W - 60), rng.randint(int(H * 0.2), int(H * 0.7))
        s = rng.randint(16, 42)
        flip = rng.choice([1, -1])
        a = rng.randint(70, 150)
        blob(df, x, y, s, int(s * 0.4), (8, 20, 40, a), rng, 0.2)
        tx = x + flip * s
        df.polygon([(tx, y), (tx + flip * int(s * 0.5), y - int(s * 0.3)),
                    (tx + flip * int(s * 0.5), y + int(s * 0.3))],
                   fill=(8, 20, 40, a))
    img = Image.alpha_composite(img, fish)

    # водоросли
    d = ImageDraw.Draw(img)
    for x in range(0, W, rng.randint(45, 85)):
        hgt = rng.randint(60, 180)
        sway = rng.randint(-25, 25)
        thick = rng.choice([2, 3, 4, 5, 6])
        pts = [(x, H)]
        for k in range(7):
            yy = H - int(hgt * k / 7)
            xx = x + int(sway * math.sin(k * 1.0 + rng.uniform(0, 0.6)))
            pts.append((xx, yy))
        d.line(pts, fill=(10, 55, 45, rng.randint(90, 160)), width=thick)

    img = glow(img, W // 3, 0, 500, 250, (80, 180, 250), 40, 120)
    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, "ocean.png"))
    print("ocean ok")


# ─── DESERT ─────────────────────────────────────────────────────────────────
def desert():
    rng = random.Random(21)
    img = vgrad(W, H, (60, 20, 10), (245, 135, 58)).convert("RGBA")

    # солнце — мягкое свечение, не идеальный круг
    sx, sy, sr = int(W * 0.48), int(H * 0.48), 130
    img = glow(img, sx, sy, sr * 3, sr * 3, (250, 155, 55), 75, 140)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    # несколько перекрывающихся кругов для мягкости
    for _ in range(5):
        ox, oy = rng.randint(-8, 8), rng.randint(-8, 8)
        ds.ellipse([sx + ox - sr, sy + oy - sr, sx + ox + sr, sy + oy + sr],
                   fill=(255, 208, 118, 60))
    sun = sun.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, sun)

    # дюны — плавные волны с текстурой
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
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase))
            )
            y += rng.randint(-1, 1)
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        # блик на гребне
        if i < 2:
            crest = [(x, y) for x, y in pts[1:-1]]
            dl.line(crest, fill=(252, 198, 118, 90), width=2)
        img = Image.alpha_composite(img, layer)

    # кактусы — грубые, с ветками
    d = ImageDraw.Draw(img)
    for cx in [int(W * 0.09), int(W * 0.89)]:
        cy = int(H * 0.91)
        brush(d, cx, cy, cx, cy - 80, (30, 52, 30), 16, rng, 2)
        brush(d, cx, cy - 55, cx - 28, cy - 55, (30, 52, 30), 12, rng, 2)
        brush(d, cx - 28, cy - 55, cx - 28, cy - 78, (30, 52, 30), 10, rng, 2)
        brush(d, cx, cy - 42, cx + 25, cy - 42, (30, 52, 30), 12, rng, 2)
        brush(d, cx + 25, cy - 42, cx + 25, cy - 62, (30, 52, 30), 10, rng, 2)

    img = grain(img)
    vignette(img, 0.36).save(os.path.join(BG, "desert.png"))
    print("desert ok")


# ─── SPACE ─────────────────────────────────────────────────────────────────
def space():
    rng = random.Random(42)
    img = Image.new("RGBA", (W, H), (3, 4, 12))
    d = ImageDraw.Draw(img)

    # звёзды — разной яркости
    for _ in range(450):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(60, 245)
        sz = rng.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + sz, y + sz], fill=(b, b, min(255, b + 25)))
    # яркие звёзды
    for _ in range(18):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(210, 255)
        d.ellipse([x, y, x + 2, y + 2], fill=(b, b, 255))
        ln = rng.randint(3, 7)
        d.line([(x - ln, y + 1), (x + ln + 2, y + 1)], fill=(b, b, 255, 70))
        d.line([(x + 1, y - ln), (x + 1, y + ln + 2)], fill=(b, b, 255, 70))

    # туманности — органичные
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

    # планета — градиентная, без полос
    px, py, pr = int(W * 0.62), int(H * 0.4), 115
    img = glow(img, px, py, pr * 2, pr * 2, (55, 115, 195), 48, 70)
    # заднее кольцо
    d = ImageDraw.Draw(img)
    d.ellipse([px - int(pr * 1.7), py - int(pr * 0.35), px + int(pr * 1.7), py + int(pr * 0.35)],
              outline=(135, 155, 200, 95), width=8)
    # планета — градиент через слои
    planet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(planet)
    for r in range(pr, 0, -2):
        t = r / pr
        col = lerp((25, 45, 90), (65, 105, 175), 1 - t)
        dp.ellipse([px - r, py - r, px + r, py + r], fill=col + (255,))
    img = Image.alpha_composite(img, planet)
    # переднее кольцо
    d = ImageDraw.Draw(img)
    d.arc([px - int(pr * 1.7), py - int(pr * 0.35), px + int(pr * 1.7), py + int(pr * 0.35)],
          start=20, end=160, fill=(155, 175, 220, 135), width=10)
    # луна
    mx, my, mr = int(W * 0.2), int(H * 0.2), 22
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(180, 180, 190))
    d.ellipse([mx - 6, my - 5, mx - 2, my - 1], fill=(150, 150, 160))

    img = grain(img)
    vignette(img, 0.36).save(os.path.join(BG, "space.png"))
    print("space ok")


# ─── CITY ───────────────────────────────────────────────────────────────────
def city():
    rng = random.Random(63)
    img = vgrad(W, H, (8, 10, 18), (16, 18, 28)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # звёзды
    for _ in range(70):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.28))
        b = rng.randint(70, 160)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 18)))

    # дальний город — силуэты без окон
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

    # ближний ряд — здания с редкими окнами
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    x = -30
    while x < W + 30:
        bw = rng.randint(90, 210)
        bh = rng.randint(220, 560)
        # здание — не идеально прямоугольное
        dn.rectangle([x, H - bh, x + bw, H], fill=(11, 13, 21, 255))
        # окна — редкие, тусклые, разные цвета
        for wy in range(H - bh + 14, H - 22, 20):
            for wx in range(x + 10, x + bw - 10, 18):
                if rng.random() > 0.78:  # только 22% окон горят
                    col = rng.choice([(250, 185, 65), (75, 155, 245), (250, 95, 55), (170, 245, 110)])
                    a = rng.randint(40, 140)  # тусклее
                    dn.rectangle([wx, wy, wx + 6, wy + 8], fill=col + (a,))
        x += bw + rng.randint(8, 35)
    img = Image.alpha_composite(img, near)

    # неон — несколько вывесок
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

    # дождь
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drn = ImageDraw.Draw(rain)
    for _ in range(320):
        x, y = rng.randint(0, W), rng.randint(0, H)
        ln = rng.randint(14, 38)
        lean = rng.uniform(-5, -1)
        drn.line([(x, y), (x + lean, y + ln)], fill=(148, 183, 223, rng.randint(28, 75)), width=1)
    img = Image.alpha_composite(img, rain)

    # асфальт с отражениями
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

    img = grain(img)
    vignette(img, 0.4).save(os.path.join(BG, "city.png"))
    print("city ok")


# ─── JUNGLE ─────────────────────────────────────────────────────────────────
def jungle():
    rng = random.Random(17)
    img = vgrad(W, H, (20, 52, 26), (36, 78, 40)).convert("RGBA")

    # свет
    img = glow(img, int(W * 0.3), int(H * 0.03), 650, 380, (218, 252, 158), 48, 150)
    img = glow(img, int(W * 0.7), int(H * 0.12), 380, 250, (252, 228, 118), 35, 110)

    # дальний план — сплошная стена листвы (как настоящая стена джунглей)
    wall = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(wall)
    # заполняем верхнюю половину неровными массами зелени
    for _ in range(40):
        x = rng.randint(-100, W)
        y = rng.randint(-50, int(H * 0.45))
        rw = rng.randint(80, 250)
        rh = rng.randint(60, 180)
        blob(dw, x, y, rw, rh, (28, 68, 32, rng.randint(120, 200)), rng, 0.4)
    wall = wall.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, wall)

    # деревья — толстые стволы, уходящие вверх за кадр
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(trees)
    for _ in range(7):
        x = rng.randint(-30, W)
        tw = rng.randint(50, 110)
        base_y = H
        top_y = rng.randint(int(H * 0.05), int(H * 0.25))
        # ствол — широкий, сужающийся кверху, неровный
        lean = rng.randint(-15, 15)
        dt.polygon([(x, base_y), (x + tw, base_y),
                    (x + int(tw * 0.7) + lean, top_y), (x + int(tw * 0.3) + lean, top_y)],
                   fill=(18, 35, 18, 255))
        # текстура коры — вертикальные штрихи
        for k in range(4):
            lx = x + int(tw * (0.2 + k * 0.2))
            brush(dt, lx, base_y - 20, lx + lean // 2, top_y + 30, (12, 25, 12, 160), 2, rng, 1)
        # крона — большая масса наверху, выходит за кадр
        cx = x + tw // 2 + lean
        for _ in range(5):
            ox = rng.randint(-int(tw * 2), int(tw * 2))
            oy = rng.randint(-80, 30)
            rw = rng.randint(int(tw * 1.5), int(tw * 3))
            rh = rng.randint(int(rw * 0.4), int(rw * 0.65))
            blob(dt, cx + ox, top_y + oy, rw, rh, (35, 82, 38, rng.randint(160, 220)), rng, 0.35)
    img = Image.alpha_composite(img, trees)

    # лучи
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(4):
        x0 = rng.randint(200, W - 200)
        lean = rng.randint(-50, 50)
        spread = rng.randint(100, 240)
        a = rng.randint(30, 55)
        dr.polygon([(x0 - 30, 0), (x0 + 30, 0),
                    (x0 + lean + spread, H), (x0 + lean - spread, H)],
                   fill=(218, 252, 168, a))
    rays = rays.filter(ImageFilter.GaussianBlur(42))
    img = Image.alpha_composite(img, rays)

    # лианы
    vines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vines)
    for _ in range(11):
        x = rng.randint(0, W)
        ln = rng.randint(150, 440)
        pts = [(x, 0)]
        for k in range(1, 8):
            pts.append((x + int(20 * math.sin(k * 0.7 + rng.uniform(0, 0.5))), int(ln * k / 8)))
        dv.line(pts, fill=(20, 58, 25, rng.randint(100, 200)), width=rng.choice([2, 3, 4]))
        for k in range(2, 7, 2):
            lx, ly = pts[k]
            blob(dv, lx, ly, 8, 5, (30, 78, 30, 150), rng, 0.3)
    img = Image.alpha_composite(img, vines)

    # листья на переднем плане
    leaves = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(leaves)
    for _ in range(8):
        x = rng.randint(-40, W)
        y = rng.choice([rng.randint(0, int(H * 0.25)), rng.randint(int(H * 0.75), H)])
        s = rng.randint(60, 160)
        ang = rng.uniform(0, math.pi * 2)
        pts = []
        for k in range(12):
            t = k / 12
            r = s * math.sin(t * math.pi)
            pts.append((x + int(r * math.cos(ang + t * 0.4)), y + int(r * math.sin(ang + t * 0.4))))
        dl.polygon(pts, fill=(25, 70, 30, rng.randint(160, 230)))
        dl.line([(x, y), (x + int(s * math.cos(ang)), y + int(s * math.sin(ang)))],
                fill=(35, 90, 40, 200), width=2)
    leaves = leaves.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, leaves)

    # светлячки
    spark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(spark)
    for _ in range(32):
        x, y = rng.randint(0, W), rng.randint(int(H * 0.28), int(H * 0.75))
        r = rng.choice([1, 2, 3])
        ds.ellipse([x - r, y - r, x + r, y + r], fill=(238, 252, 178, rng.randint(75, 200)))
    spark = spark.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, spark)

    # туман внизу
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mist)
    for _ in range(6):
        x = rng.randint(-80, W)
        y = rng.randint(int(H * 0.74), int(H * 0.86))
        dm.rounded_rectangle([x, y, x + rng.randint(300, 680), y + rng.randint(30, 80)],
                             radius=38, fill=(135, 215, 155, rng.randint(30, 58)))
    mist = mist.filter(ImageFilter.GaussianBlur(50))
    img = Image.alpha_composite(img, mist)

    img = grain(img)
    vignette(img, 0.36).save(os.path.join(BG, "jungle.png"))
    print("jungle ok")


# ─── SNOW ───────────────────────────────────────────────────────────────────
def snow():
    rng = random.Random(5)
    img = vgrad(W, H, (10, 16, 32), (20, 30, 50)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # звёзды
    for _ in range(140):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.36))
        b = rng.randint(80, 200)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 18)))
    # луна
    mx, my, mr = int(W * 0.78), int(H * 0.1), 40
    img = glow(img, mx, my, mr * 3, mr * 3, (198, 208, 252), 50, 75)
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(218, 228, 250))
    d.ellipse([mx - 9, my - 7, mx - 4, my - 2], fill=(188, 198, 218))

    # ели
    for i in range(14):
        x = rng.randint(0, W)
        th = rng.randint(75, 200)
        base_y = int(H * 0.6)
        col = (14, 25, 36, 195)
        pts = [(x, base_y)]
        for s in range(1, 6):
            ww = int(14 * s / 5) + rng.randint(-2, 2)
            yy = base_y - int(th * (1 - s / 6))
            pts += [(x + ww, yy + 9), (x + int(ww * 0.4), yy)]
        pts += [(x + 14, base_y)]
        d.polygon(pts, fill=col)

    # дома
    for hx, hw, hh in [(int(W * 0.07), 180, 130), (int(W * 0.32), 220, 160),
                        (int(W * 0.59), 160, 120), (int(W * 0.79), 200, 140)]:
        hy = int(H * 0.72)
        d.rectangle([hx, hy - hh, hx + hw, hy], fill=(68, 53, 44))
        # брёвна
        for ly in range(hy - hh + 9, hy, 17):
            brush(d, hx, ly, hx + hw, ly, (53, 40, 34), 2, rng, 1)
        # крыша
        d.polygon([(hx - 20, hy - hh), (hx + hw // 2, hy - hh - 58), (hx + hw + 20, hy - hh)],
                  fill=(58, 48, 44))
        d.polygon([(hx - 20, hy - hh), (hx + hw // 2, hy - hh - 58), (hx + hw + 20, hy - hh),
                   (hx + hw + 20, hy - hh + 10), (hx + hw // 2, hy - hh - 48), (hx - 20, hy - hh + 10)],
                  fill=(228, 238, 250))
        # окна
        for wx in range(hx + 20, hx + hw - 20, 50):
            for wy in range(hy - hh + 24, hy - 20, 54):
                img = glow(img, wx + 14, wy + 16, 40, 34, (252, 178, 58), 34, 24)
                d = ImageDraw.Draw(img)
                d.rectangle([wx, wy, wx + 28, wy + 32], fill=(252, 198, 88))
                d.rectangle([wx + 3, wy + 3, wx + 25, wy + 29], fill=(252, 218, 128))
                d.line([(wx + 14, wy), (wx + 14, wy + 32)], fill=(88, 58, 40), width=3)
                d.line([(wx, wy + 16), (wx + 28, wy + 16)], fill=(88, 58, 40), width=3)
        # дверь
        d.rectangle([hx + hw // 2 - 15, hy - 50, hx + hw // 2 + 15, hy], fill=(78, 55, 35))
        d.ellipse([hx + hw // 2 + 6, hy - 30, hx + hw // 2 + 10, hy - 26], fill=(198, 178, 98))
        # дым
        cx = hx + int(hw * 0.7)
        cy = hy - hh - 52
        for k in range(5):
            ox = rng.randint(-9, 9)
            oy = -k * 15
            r = 7 + k * 3
            a = max(22, 65 - k * 11)
            smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(smoke).ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r],
                                          fill=(185, 190, 200, a))
            smoke = smoke.filter(ImageFilter.GaussianBlur(7))
            img = Image.alpha_composite(img, smoke)
            d = ImageDraw.Draw(img)

    # снег
    d.rectangle([0, int(H * 0.72), W, H], fill=(198, 213, 233))
    for _ in range(19):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.73), H)
        w2 = rng.randint(38, 145)
        d.ellipse([x - w2, y - 9, x + w2, y + 13], fill=(208, 223, 243))
    # падающий снег
    snowfl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsf = ImageDraw.Draw(snowfl)
    for _ in range(190):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.choice([1, 2, 2, 3])
        dsf.ellipse([x, y, x + r, y + r], fill=(238, 243, 252, rng.randint(95, 215)))
    img = Image.alpha_composite(img, snowfl)

    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, "snow.png"))
    print("snow ok")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    ocean()
    desert()
    space()
    city()
    jungle()
    snow()
    print("all backgrounds v4 ok")
