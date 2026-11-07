"""Новые фоны MineDash Launcher: ocean, desert, space, city, jungle, snow.
Запуск: python tools/gen-bg2.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")

W, H = 1920, 1080


def vgrad(w, h, top, bottom, stop=0.65):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(int(h * stop), h):
        t = (y - h * stop) / (h * (1 - stop))
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def hgrad(w, h, left, right):
    img = Image.new("RGB", (w, h), left)
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / w
        c = tuple(int(left[i] + (right[i] - left[i]) * t) for i in range(3))
        d.line([(x, 0), (x, h)], fill=c)
    return img


def add_noise(img, sigma=10, opacity=0.08):
    noise = Image.effect_noise((img.width, img.height), sigma).convert("RGBA")
    noise.putalpha(int(255 * opacity))
    return Image.alpha_composite(img.convert("RGBA"), noise)


def vignette(img, strength=0.38):
    mask = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(mask).ellipse(
        [-int(img.width * 0.25), -int(img.height * 0.25),
         int(img.width * 1.25), int(img.height * 1.25)], fill=255)
    black = Image.new("RGBA", (img.width, img.height), (0, 0, 0, int(255 * strength)))
    return Image.composite(img.convert("RGBA"), black, mask)


def glow_blob(img, cx, cy, rx, ry, col, alpha, blur=80):
    layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img, layer)


def stars(d, rng, count, ymax, bright=230):
    for _ in range(count):
        x, y = rng.randint(0, W), rng.randint(0, ymax)
        b = rng.randint(60, bright)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 25)))


# ─── OCEAN: подводный мир ───────────────────────────────────────────────────
def ocean():
    rng = random.Random(42)
    img = vgrad(W, H, (4, 28, 52), (2, 10, 24)).convert("RGBA")
    # лучи света сверху
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(7):
        x0 = rng.randint(100, W - 100)
        spread = rng.randint(80, 200)
        a = rng.randint(18, 42)
        dr.polygon([(x0 - 20, 0), (x0 + 20, 0), (x0 + spread, H), (x0 - spread, H)],
                   fill=(120, 210, 255, a))
    rays = rays.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img, rays)
    # пузыри
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    for _ in range(60):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(2, 14)
        a = rng.randint(30, 90)
        db.ellipse([x - r, y - r, x + r, y + r], outline=(160, 220, 255, a), width=1)
        if r > 5:
            db.ellipse([x - r + 2, y - r + 2, x - r + 4, y - r + 4], fill=(200, 240, 255, a))
    img = Image.alpha_composite(img, bub)
    # силуэты рыб
    fish = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(fish)
    for _ in range(12):
        x, y = rng.randint(0, W), rng.randint(int(H * 0.2), int(H * 0.8))
        s = rng.randint(12, 40)
        flip = rng.choice([1, -1])
        # тело
        df.ellipse([x, y, x + s * 2, y + s], fill=(8, 20, 40, rng.randint(80, 160)))
        # хвост
        df.polygon([(x + s * 2, y + s // 2), (x + s * 2 + s * 0.7, y - s * 0.3),
                    (x + s * 2 + s * 0.7, y + s * 1.3)], fill=(8, 20, 40, 120))
    img = Image.alpha_composite(img, fish)
    # дно с водорослями
    d = ImageDraw.Draw(img)
    for x in range(0, W, 60):
        hgt = rng.randint(40, 140)
        sway = rng.randint(-15, 15)
        pts = [(x, H)]
        for k in range(5):
            yy = H - int(hgt * k / 5)
            pts.append((x + int(sway * math.sin(k * 1.2)), yy))
        d.line(pts, fill=(10, 50, 40, 120), width=rng.choice([3, 4, 5]))
    img = glow_blob(img, W // 3, 0, 400, 200, (80, 180, 255), 40, 100)
    img = add_noise(img)
    vignette(img, 0.4).save(os.path.join(BG, "ocean.png"))
    print("ocean ok")


# ─── DESERT: пустыня на закате ──────────────────────────────────────────────
def desert():
    rng = random.Random(88)
    img = vgrad(W, H, (60, 20, 10), (255, 140, 60)).convert("RGBA")
    # огромное солнце
    sx, sy, sr = int(W * 0.5), int(H * 0.52), 160
    img = glow_blob(img, sx, sy, sr * 2.5, sr * 2.5, (255, 160, 60), 80, 120)
    d = ImageDraw.Draw(img)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 210, 120))
    # мираж — горизонтальная полоса
    mirage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(mirage).rectangle([0, int(H * 0.55), W, int(H * 0.58)], fill=(255, 230, 180, 50))
    img = Image.alpha_composite(img, mirage.filter(ImageFilter.GaussianBlur(8)))
    # дюны — 4 слоя плавных волн (ниже, чтобы солнце было видно)
    for i, (col, base, amp, freq, phase) in enumerate([
        ((210, 130, 65), 68, 40, 2.2, 0.0), ((180, 105, 50), 74, 32, 1.8, 1.5),
        ((140, 78, 38), 80, 24, 2.6, 3.0), ((95, 55, 28), 86, 16, 2.0, 4.5),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        pts = [(0, H)]
        for x in range(0, W + 10, 10):
            t = x / W
            y = int(H * base / 100) - int(
                H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase))
            )
            pts.append((x, y))
        pts += [(W, H)]
        dl.polygon(pts, fill=col + (255,))
        # блик на гребне (верхняя кромка)
        if i < 2:
            crest = []
            for x in range(0, W + 10, 10):
                t = x / W
                y = int(H * base / 100) - int(
                    H * amp / 100 * (0.5 + 0.5 * math.sin(t * math.pi * freq + phase))
                )
                crest.append((x, y))
            dl.line(crest, fill=(255, 200, 120, 90), width=3)
        img = Image.alpha_composite(img, layer)
    # кактусы на переднем плане
    d = ImageDraw.Draw(img)
    for cx in [int(W * 0.12), int(W * 0.85)]:
        cy = int(H * 0.88)
        d.rectangle([cx - 8, cy - 80, cx + 8, cy], fill=(30, 50, 30))
        d.rectangle([cx - 30, cy - 60, cx - 8, cy - 50], fill=(30, 50, 30))
        d.rectangle([cx - 30, cy - 80, cx - 20, cy - 60], fill=(30, 50, 30))
        d.rectangle([cx + 8, cy - 50, cx + 28, cy - 40], fill=(30, 50, 30))
        d.rectangle([cx + 20, cy - 70, cx + 28, cy - 50], fill=(30, 50, 30))
    img = add_noise(img)
    vignette(img, 0.35).save(os.path.join(BG, "desert.png"))
    print("desert ok")


# ─── SPACE: космос с планетой ───────────────────────────────────────────────
def space():
    rng = random.Random(99)
    img = Image.new("RGBA", (W, H), (3, 4, 12))
    d = ImageDraw.Draw(img)
    stars(d, rng, 500, H)
    # яркие звёзды с крестами
    for _ in range(30):
        x, y = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(200, 255)
        d.ellipse([x, y, x + 2, y + 2], fill=(b, b, 255))
        d.line([(x - 4, y + 1), (x + 6, y + 1)], fill=(b, b, 255, 80))
        d.line([(x + 1, y - 4), (x + 1, y + 6)], fill=(b, b, 255, 80))
    # туманности
    img = glow_blob(img, int(W * 0.2), int(H * 0.3), 350, 250, (120, 40, 180), 35, 130)
    img = glow_blob(img, int(W * 0.75), int(H * 0.6), 300, 200, (30, 80, 180), 30, 120)
    img = glow_blob(img, int(W * 0.5), int(H * 0.15), 250, 150, (180, 60, 80), 25, 100)
    # планета с кольцами
    px, py, pr = int(W * 0.62), int(H * 0.45), 130
    # гало планеты
    img = glow_blob(img, px, py, pr * 1.8, pr * 1.8, (60, 120, 200), 50, 60)
    d = ImageDraw.Draw(img)
    # задняя часть кольца
    d.ellipse([px - pr * 1.7, py - pr * 0.35, px + pr * 1.7, py + pr * 0.35],
              outline=(140, 160, 200, 100), width=8)
    # планета
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(40, 70, 130))
    # полосы на планете
    for k in range(5):
        yy = py - pr + int(2 * pr * (k + 0.5) / 5)
        half_w = int(pr * math.sqrt(1 - ((yy - py) / pr) ** 2))
        d.line([(px - half_w, yy), (px + half_w, yy)], fill=(60, 100, 170, 150), width=6)
    # тень на планете
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([px - pr, py - pr, px + pr, py + pr], fill=(0, 0, 20, 120))
    shadow_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow_mask).ellipse([px - pr, py - pr, px + pr, py + pr], fill=255)
    ImageDraw.Draw(shadow_mask).ellipse([px - pr - 40, py - pr, px + pr - 40, py + pr], fill=0)
    shadow.putalpha(Image.composite(shadow.split()[3], Image.new("L", (W, H), 0), shadow_mask))
    img = Image.alpha_composite(img, shadow)
    # передняя часть кольца
    d = ImageDraw.Draw(img)
    d.arc([px - pr * 1.7, py - pr * 0.35, px + pr * 1.7, py + pr * 0.35],
          start=20, end=160, fill=(160, 180, 220, 140), width=10)
    # маленькая луна
    mx, my, mr = int(W * 0.25), int(H * 0.25), 22
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(180, 180, 190))
    d.ellipse([mx - mr + 4, my - mr + 4, mx - mr + 10, my - mr + 10], fill=(150, 150, 160))
    img = add_noise(img)
    vignette(img, 0.35).save(os.path.join(BG, "space.png"))
    print("space ok")


# ─── CITY: ночной город под дождём ──────────────────────────────────────────
def city():
    rng = random.Random(55)
    img = vgrad(W, H, (8, 10, 18), (16, 18, 30)).convert("RGBA")
    d = ImageDraw.Draw(img)
    stars(d, rng, 80, int(H * 0.3), 140)
    # дальний силуэт города
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(far)
    x = 0
    while x < W:
        bw = rng.randint(40, 100)
        bh = rng.randint(100, 300)
        df.rectangle([x, int(H * 0.55) - bh, x + bw, int(H * 0.55)], fill=(14, 18, 30, 255))
        # окна
        for wy in range(int(H * 0.55) - bh + 8, int(H * 0.55) - 8, 14):
            for wx in range(x + 6, x + bw - 6, 12):
                if rng.random() > 0.6:
                    col = rng.choice([(255, 200, 80), (100, 180, 255), (255, 120, 80)])
                    df.rectangle([wx, wy, wx + 5, wy + 7], fill=col + (rng.randint(60, 180),))
        x += bw + rng.randint(4, 20)
    far = far.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, far)
    # ближний ряд зданий (крупнее, темнее)
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    x = -30
    while x < W + 30:
        bw = rng.randint(80, 180)
        bh = rng.randint(200, 500)
        dn.rectangle([x, H - bh, x + bw, H], fill=(10, 12, 20, 255))
        for wy in range(H - bh + 12, H - 20, 18):
            for wx in range(x + 8, x + bw - 8, 16):
                if rng.random() > 0.5:
                    col = rng.choice([(255, 190, 70), (80, 160, 255), (255, 100, 60), (180, 255, 120)])
                    dn.rectangle([wx, wy, wx + 7, wy + 9], fill=col + (rng.randint(80, 220),))
        x += bw + rng.randint(6, 30)
    img = Image.alpha_composite(img, near)
    # неоновые вывески
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dne = ImageDraw.Draw(neon)
    for _ in range(8):
        x = rng.randint(100, W - 200)
        y = rng.randint(int(H * 0.4), int(H * 0.75))
        nw, nh = rng.randint(60, 160), rng.randint(14, 30)
        col = rng.choice([(255, 50, 120), (50, 200, 255), (255, 200, 50), (120, 255, 80)])
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=4, outline=col + (200,), width=3)
        dne.rounded_rectangle([x, y, x + nw, y + nh], radius=4, fill=col + (30,))
    neon = neon.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, neon)
    # свечение от неона
    for _ in range(5):
        x = rng.randint(100, W - 100)
        y = rng.randint(int(H * 0.4), int(H * 0.7))
        col = rng.choice([(255, 50, 120), (50, 200, 255), (255, 200, 50)])
        img = glow_blob(img, x, y, 120, 80, col, 25, 60)
    # дождь
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drn = ImageDraw.Draw(rain)
    for _ in range(300):
        x, y = rng.randint(0, W), rng.randint(0, H)
        ln = rng.randint(12, 35)
        drn.line([(x, y), (x - 3, y + ln)], fill=(150, 180, 220, rng.randint(25, 70)), width=1)
    img = Image.alpha_composite(img, rain)
    # мокрый асфальт с отражениями
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.88), W, H], fill=(8, 10, 16))
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dref = ImageDraw.Draw(refl)
    for _ in range(40):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.89), H)
        ww = rng.randint(10, 60)
        col = rng.choice([(255, 190, 70), (80, 160, 255), (255, 50, 120)])
        dref.ellipse([x - ww, y, x + ww, y + 3], fill=col + (rng.randint(15, 40),))
    refl = refl.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, refl)
    img = add_noise(img)
    vignette(img, 0.4).save(os.path.join(BG, "city.png"))
    print("city ok")


# ─── JUNGLE: тропические джунгли ────────────────────────────────────────────
def jungle():
    rng = random.Random(33)
    img = vgrad(W, H, (20, 50, 24), (35, 75, 38)).convert("RGBA")
    # тёплый свет сквозь кроны (ярче)
    img = glow_blob(img, int(W * 0.35), int(H * 0.05), 600, 350, (220, 255, 160), 50, 140)
    img = glow_blob(img, int(W * 0.7), int(H * 0.15), 350, 220, (255, 230, 120), 35, 100)
    # дальние деревья — толстые стволы, компактные кроны
    far = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    df = ImageDraw.Draw(far)
    for _ in range(10):
        x = rng.randint(0, W)
        bh = rng.randint(200, 420)
        tw = rng.randint(70, 110)
        base_y = int(H * 0.7)
        # ствол (тёмный, контрастный, с текстурой)
        df.polygon([(x, base_y), (x + tw, base_y), (x + int(tw * 0.75), base_y - bh),
                    (x + int(tw * 0.25), base_y - bh)], fill=(12, 28, 14, 255))
        # текстура коры
        for k in range(3):
            lx = x + int(tw * (0.3 + k * 0.2))
            df.line([(lx, base_y - 20), (lx, base_y - bh + 20)], fill=(8, 20, 10, 180), width=2)
        # крона — компактная, из 3-4 эллипсов
        cx, cy = x + tw // 2, base_y - bh
        for _ in range(4):
            ox = rng.randint(-tw, tw)
            oy = rng.randint(-40, 20)
            rw = rng.randint(int(tw * 0.8), int(tw * 1.5))
            rh = rng.randint(int(rw * 0.6), int(rw * 0.9))
            df.ellipse([cx + ox - rw, cy + oy - rh, cx + ox + rw, cy + oy + rh],
                       fill=(40, 95, 45, rng.randint(180, 230)))
    far = far.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, far)
    # световые лучи (god rays) — поверх крон
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    for i in range(5):
        x0 = rng.randint(200, W - 200)
        spread = rng.randint(100, 250)
        a = rng.randint(30, 55)
        dr.polygon([(x0 - 30, 0), (x0 + 30, 0), (x0 + spread, H), (x0 - spread, H)],
                   fill=(220, 255, 170, a))
    rays = rays.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, rays)
    # лианы
    vines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vines)
    for _ in range(14):
        x = rng.randint(0, W)
        ln = rng.randint(150, 450)
        pts = [(x, 0)]
        for k in range(1, 8):
            pts.append((x + int(20 * math.sin(k * 0.8)), int(ln * k / 8)))
        dv.line(pts, fill=(20, 60, 25, rng.randint(100, 200)), width=rng.choice([2, 3, 4]))
        # листья на лиане
        for k in range(2, 7, 2):
            lx, ly = pts[k]
            dv.ellipse([lx - 8, ly - 4, lx + 8, ly + 4], fill=(30, 80, 30, 150))
    img = Image.alpha_composite(img, vines)
    # крупные листья на переднем плане (ярче)
    leaves = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(leaves)
    for _ in range(10):
        x = rng.randint(-50, W)
        y = rng.choice([rng.randint(0, int(H * 0.3)), rng.randint(int(H * 0.7), H)])
        s = rng.randint(60, 160)
        ang = rng.uniform(0, math.pi * 2)
        pts = []
        for k in range(12):
            t = k / 12
            r = s * math.sin(t * math.pi)
            pts.append((x + int(r * math.cos(ang + t * 0.5)), y + int(r * math.sin(ang + t * 0.5))))
        dl.polygon(pts, fill=(25, 70, 30, rng.randint(160, 230)))
        # прожилка
        dl.line([(x, y), (x + int(s * math.cos(ang)), y + int(s * math.sin(ang)))],
                fill=(35, 90, 40, 200), width=2)
    leaves = leaves.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, leaves)
    # светлячки / пыльца (ярче)
    spark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(spark)
    for _ in range(35):
        x, y = rng.randint(0, W), rng.randint(int(H * 0.3), int(H * 0.8))
        r = rng.choice([1, 2, 3])
        ds.ellipse([x - r, y - r, x + r, y + r], fill=(240, 255, 180, rng.randint(80, 200)))
    spark = spark.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, spark)
    # туман внизу (ярче)
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mist)
    for _ in range(8):
        x = rng.randint(-100, W)
        y = rng.randint(int(H * 0.7), int(H * 0.9))
        dm.rounded_rectangle([x, y, x + rng.randint(300, 700), y + rng.randint(30, 80)],
                             radius=40, fill=(140, 220, 160, rng.randint(30, 60)))
    mist = mist.filter(ImageFilter.GaussianBlur(50))
    img = Image.alpha_composite(img, mist)
    img = add_noise(img)
    vignette(img, 0.35).save(os.path.join(BG, "jungle.png"))
    print("jungle ok")


# ─── SNOW: зимняя деревня ───────────────────────────────────────────────────
def snow():
    rng = random.Random(11)
    img = vgrad(W, H, (10, 16, 30), (20, 30, 50)).convert("RGBA")
    d = ImageDraw.Draw(img)
    stars(d, rng, 150, int(H * 0.4), 180)
    # луна
    mx, my, mr = int(W * 0.8), int(H * 0.12), 40
    img = glow_blob(img, mx, my, mr * 3, mr * 3, (200, 210, 255), 50, 70)
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(220, 230, 250))
    # дальние ели
    for i in range(15):
        x = rng.randint(0, W)
        th = rng.randint(80, 200)
        base_y = int(H * 0.6)
        col = (15, 25, 35, 200)
        pts = [(x, base_y)]
        for s in range(1, 6):
            ww = int(14 * s / 5)
            yy = base_y - int(th * (1 - s / 6))
            pts += [(x + ww, yy + 10), (x + int(ww * 0.4), yy)]
        pts += [(x + 14, base_y)]
        d.polygon(pts, fill=col)
    # дома — крупные, яркие, с тёплыми окнами
    for hx, hw, hh in [(int(W * 0.1), 180, 130), (int(W * 0.35), 220, 160),
                        (int(W * 0.62), 160, 120), (int(W * 0.82), 200, 140)]:
        hy = int(H * 0.72)
        # стена (светлее для контраста)
        d.rectangle([hx, hy - hh, hx + hw, hy], fill=(70, 55, 45))
        # брёвна
        for ly in range(hy - hh + 10, hy, 18):
            d.line([(hx, ly), (hx + hw, ly)], fill=(55, 42, 35), width=2)
        # крыша со снегом
        d.polygon([(hx - 20, hy - hh), (hx + hw // 2, hy - hh - 60), (hx + hw + 20, hy - hh)],
                  fill=(60, 50, 45))
        d.polygon([(hx - 20, hy - hh), (hx + hw // 2, hy - hh - 60), (hx + hw + 20, hy - hh),
                   (hx + hw + 20, hy - hh + 10), (hx + hw // 2, hy - hh - 50), (hx - 20, hy - hh + 10)],
                  fill=(230, 240, 250))
        # окна с тёплым светом (ярче)
        for wx in range(hx + 20, hx + hw - 20, 50):
            for wy in range(hy - hh + 25, hy - 20, 55):
                # свечение вокруг окна
                img = glow_blob(img, wx + 14, wy + 16, 40, 35, (255, 180, 60), 35, 25)
                d = ImageDraw.Draw(img)
                d.rectangle([wx, wy, wx + 28, wy + 32], fill=(255, 200, 90))
                d.rectangle([wx + 3, wy + 3, wx + 25, wy + 29], fill=(255, 220, 130))
                # рама
                d.line([(wx + 14, wy), (wx + 14, wy + 32)], fill=(90, 60, 40), width=3)
                d.line([(wx, wy + 16), (wx + 28, wy + 16)], fill=(90, 60, 40), width=3)
        # дверь
        d.rectangle([hx + hw // 2 - 15, hy - 50, hx + hw // 2 + 15, hy], fill=(80, 55, 35))
        d.ellipse([hx + hw // 2 + 6, hy - 30, hx + hw // 2 + 10, hy - 26], fill=(200, 180, 100))
    # снег на земле
    d.rectangle([0, int(H * 0.72), W, H], fill=(200, 215, 235))
    # сугробы
    for _ in range(20):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.73), H)
        w2 = rng.randint(40, 150)
        d.ellipse([x - w2, y - 10, x + w2, y + 15], fill=(210, 225, 245))
    # падающий снег
    snowfl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsf = ImageDraw.Draw(snowfl)
    for _ in range(200):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.choice([1, 2, 2, 3])
        dsf.ellipse([x, y, x + r, y + r], fill=(240, 245, 255, rng.randint(100, 220)))
    img = Image.alpha_composite(img, snowfl)
    img = add_noise(img)
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
    print("all new backgrounds ok")
