"""Премиальные фоны MineDash Launcher: aurora, mountains, forest, cyber.
Запуск: python tools/gen-bg-premium.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")

W, H = 1920, 1080


def vgrad(w, h, top, bottom, stop=0.68):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(int(h * stop), h):
        t = (y - h * stop) / (h * (1 - stop))
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def stars(d, rng, count, ymax, bright=230):
    for _ in range(count):
        x, y = rng.randint(0, W), rng.randint(0, ymax)
        b = rng.randint(60, bright)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, min(255, b + 25)))


def add_noise(img, sigma=12, opacity=0.1):
    rng = random.Random(9)
    noise = Image.effect_noise((img.width, img.height), sigma).convert("RGBA")
    noise.putalpha(int(255 * opacity))
    return Image.alpha_composite(img.convert("RGBA"), noise)


def vignette(img, strength=0.4):
    mask = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(mask).ellipse(
        [-int(img.width * 0.25), -int(img.height * 0.25),
         int(img.width * 1.25), int(img.height * 1.25)], fill=255)
    black = Image.new("RGBA", (img.width, img.height), (0, 0, 0, int(255 * strength)))
    return Image.composite(img.convert("RGBA"), black, mask)


def ridge(img, rng, col, base, amp, blur, snow=None, step=150, snow_p=0.75):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(layer)
    pts = [(0, H)]
    x = -60
    while x < W + 60:
        peak = int(H * base / 100) - rng.randint(0, int(H * amp / 100))
        pts += [(x, peak), (x + step, int(H * base / 100) + rng.randint(0, 45))]
        x += step
    pts += [(W, H)]
    dm.polygon(pts, fill=col + (255,))
    if snow:
        for j in range(1, len(pts) - 2, 2):
            px, py = pts[j]
            if rng.random() > (1 - snow_p):
                sw = 22 + rng.randint(0, 18)
                dm.polygon([(px - sw, py + 34), (px, py), (px + sw, py + 34),
                            (px + int(sw * 0.6), py + 52), (px - int(sw * 0.6), py + 52)],
                           fill=snow + (200,))
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img, layer)


def aurora():
    rng = random.Random(57)
    img = vgrad(W, H, (3, 6, 16), (10, 26, 44)).convert("RGBA")
    d = ImageDraw.Draw(img)
    stars(d, rng, 420, int(H * 0.55))
    # млечный путь
    mw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dmw = ImageDraw.Draw(mw)
    for _ in range(900):
        t = rng.random()
        x = int(W * (0.9 - 0.8 * t))
        y = int(H * 0.5 * t)
        b = rng.randint(40, 110)
        dmw.ellipse([x, y, x + 2, y + 2], fill=(b, b, min(255, b + 40), rng.randint(60, 140)))
    img = Image.alpha_composite(img, mw.filter(ImageFilter.GaussianBlur(3)))
    # луна с гало
    mx, my, mr = int(W * 0.78), int(H * 0.15), 58
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([mx - mr * 3.6, my - mr * 3.6, mx + mr * 3.6, my + mr * 3.6],
                                 fill=(170, 200, 255, 70))
    img = Image.alpha_composite(img, halo.filter(ImageFilter.GaussianBlur(85)))
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(225, 235, 250))
    d.ellipse([mx - 18, my - 30, mx - 2, my - 14], fill=(200, 212, 235))
    d.ellipse([mx + 8, my + 10, mx + 26, my + 28], fill=(198, 210, 233))
    # сияние: 4 ленты + лучи
    au = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(au)
    for col, base_y, amp, ph in [
        ((70, 255, 200, 120), int(H * 0.18), 120, 0),
        ((60, 220, 255, 90), int(H * 0.24), 95, 2.2),
        ((90, 160, 255, 75), int(H * 0.29), 85, 4.1),
        ((190, 100, 255, 55), int(H * 0.36), 70, 5.5),
    ]:
        pts = [(x, base_y + int(amp * math.sin(x / 280 + ph))) for x in range(-100, W + 200, 100)]
        da.polygon(pts + [(W + 200, base_y + 400), (-100, base_y + 400)], fill=col)
    for x in range(0, W, 30):
        ln = rng.randint(80, 240)
        a = rng.randint(18, 55)
        col = rng.choice([(90, 255, 210, a), (120, 220, 255, a)])
        da.line([(x, int(H * 0.14) + rng.randint(-50, 50)),
                 (x + rng.randint(-20, 20), int(H * 0.14) + ln)], fill=col, width=rng.choice([2, 3, 4]))
    img = Image.alpha_composite(img, au.filter(ImageFilter.GaussianBlur(30)))
    # фьорд
    img = ridge(img, rng, (36, 56, 84), 60, 150, 3, (140, 190, 230))
    img = ridge(img, rng, (26, 40, 62), 70, 120, 1, (110, 160, 210))
    img = ridge(img, rng, (16, 24, 38), 79, 95, 0, (70, 110, 170))
    img = ridge(img, rng, (9, 13, 22), 86, 65, 0)
    # вода + отражения
    lake_y = int(H * 0.87)
    lake = vgrad(W, H - lake_y, (18, 30, 48), (8, 13, 24)).convert("RGBA")
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    water.paste(lake, (0, lake_y))
    water.putalpha(235)
    img = Image.alpha_composite(img, water)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(refl)
    for k in range(12):
        yy = lake_y + 8 + k * 18
        ww = 100 - k * 6
        dr.ellipse([mx - ww, yy, mx + ww, yy + 6], fill=(210, 225, 255, max(5, 46 - k * 3)))
    for _ in range(16):
        x = rng.randint(0, W)
        yy = lake_y + rng.randint(4, H - lake_y - 8)
        ww = rng.randint(20, 90)
        col = rng.choice([(90, 255, 210), (120, 220, 255), (190, 120, 255)])
        dr.ellipse([x - ww, yy, x + ww, yy + 4], fill=col + (rng.randint(18, 40),))
    img = Image.alpha_composite(img, refl.filter(ImageFilter.GaussianBlur(4)))
    img = add_noise(img)
    vignette(img, 0.36).save(os.path.join(BG, "aurora.png"))
    print("aurora ok")


def mountains():
    rng = random.Random(23)
    img = vgrad(W, H, (30, 18, 56), (255, 138, 84)).convert("RGBA")
    # полосы облаков
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(clouds)
    for _ in range(14):
        x = rng.randint(-200, W)
        yy = int(H * (0.18 + rng.random() * 0.28))
        cw = rng.randint(280, 700)
        ch = rng.randint(8, 26)
        warm = rng.random() > 0.4
        col = (255, 180, 120, rng.randint(50, 110)) if warm else (90, 70, 130, rng.randint(40, 80))
        dc.rounded_rectangle([x, yy, x + cw, yy + ch], radius=ch // 2, fill=col)
    img = Image.alpha_composite(img, clouds.filter(ImageFilter.GaussianBlur(16)))
    # солнце
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sx, sy, sr = int(W * 0.64), int(H * 0.46), 90
    ImageDraw.Draw(sun).ellipse([sx - sr * 2.6, sy - sr * 2.6, sx + sr * 2.6, sy + sr * 2.6],
                                fill=(255, 160, 80, 90))
    img = Image.alpha_composite(img, sun.filter(ImageFilter.GaussianBlur(110)))
    d = ImageDraw.Draw(img)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 225, 160))
    # бог-rays
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dray = ImageDraw.Draw(rays)
    for _ in range(12):
        ang = math.radians(rng.randint(-70, 70))
        ln = rng.randint(500, 900)
        dray.line([(sx, sy), (sx + int(ln * math.sin(ang)), sy - int(ln * math.cos(ang)))],
                  fill=(255, 200, 130, rng.randint(14, 34)), width=rng.randint(8, 30))
    img = Image.alpha_composite(img, rays.filter(ImageFilter.GaussianBlur(30)))
    # 5 слоёв пиков
    for col, base, amp, snow in [
        ((150, 92, 128), 44, 160, (255, 205, 175)),
        ((116, 70, 106), 53, 130, (240, 175, 150)),
        ((84, 50, 84), 62, 100, (200, 150, 140)),
        ((52, 32, 58), 71, 75, None),
        ((24, 15, 33), 80, 55, None),
    ]:
        img = ridge(img, rng, col, base, amp, 1 if base < 70 else 0, snow, step=230, snow_p=0.8)
    # тёплая дымка у горизонта
    haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(haze).rectangle([0, int(H * 0.48), W, int(H * 0.72)], fill=(230, 120, 75, 55))
    img = Image.alpha_composite(img, haze.filter(ImageFilter.GaussianBlur(60)))
    img = add_noise(img)
    vignette(img, 0.34).save(os.path.join(BG, "mountains.png"))
    print("mountains ok")


def forest():
    rng = random.Random(77)
    img = vgrad(W, H, (6, 13, 18), (22, 42, 34)).convert("RGBA")
    d = ImageDraw.Draw(img)
    stars(d, rng, 180, int(H * 0.4), 180)
    # луна за деревьями
    fx, fy, fr = int(W * 0.72), int(H * 0.13), 44
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(fg).ellipse([fx - fr * 3, fy - fr * 3, fx + fr * 3, fy + fr * 3], fill=(160, 230, 200, 60))
    img = Image.alpha_composite(img, fg.filter(ImageFilter.GaussianBlur(80)))
    d = ImageDraw.Draw(img)
    d.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=(215, 240, 225))
    # 6 слоёв елей
    for layer_i in range(6):
        shade = [(34, 58, 50, 38), (28, 50, 42, 80), (22, 42, 36, 125),
                 (16, 32, 27, 165), (10, 22, 18, 210), (5, 12, 10, 240)][layer_i]
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        x = -80
        while x < W + 60:
            tw = int(34 * (1.7 - layer_i * 0.27))
            th = int(420 * (1.18 - layer_i * 0.19))
            base_y = int(H * (0.64 + layer_i * 0.072))
            top_y = base_y - th
            lean = rng.randint(-6, 6)
            pts = [(x, base_y)]
            steps = 9
            for s in range(1, steps + 1):
                ww = int(tw * (s / steps))
                yy = top_y + int((base_y - top_y) * (1 - s / steps))
                xx = x + int(lean * (1 - s / steps))
                pts += [(xx + ww, yy + 16), (xx + int(tw * 0.4), yy - rng.randint(0, 8))]
            pts += [(x + tw, base_y)]
            dl.polygon(pts, fill=shade)
            dl.rectangle([x + tw // 2 - 2, base_y - 26, x + tw // 2 + 2, base_y], fill=shade)
            x += tw + int(74 * (1.25 - layer_i * 0.2))
        img = Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(4 - layer_i * 0.65)))
        # светлячки в средних слоях
        if 1 <= layer_i <= 3:
            fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dfl = ImageDraw.Draw(fl)
            for _ in range(9):
                x = rng.randint(0, W)
                yy = rng.randint(int(H * 0.5), int(H * 0.85))
                r = rng.choice([2, 3])
                dfl.ellipse([x - r, yy - r, x + r, yy + r], fill=(190, 255, 130, rng.randint(70, 150)))
            img = Image.alpha_composite(img, fl.filter(ImageFilter.GaussianBlur(2.5)))
    # стелющийся туман
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dms = ImageDraw.Draw(mist)
    for _ in range(10):
        x = rng.randint(-150, W)
        yy = int(H * (0.66 + rng.random() * 0.2))
        cw = rng.randint(300, 800)
        dms.rounded_rectangle([x, yy, x + cw, yy + rng.randint(20, 60)], radius=30,
                              fill=(150, 200, 180, rng.randint(28, 55)))
    img = Image.alpha_composite(img, mist.filter(ImageFilter.GaussianBlur(40)))
    # общий зелёный хейз
    haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(haze).rectangle([0, int(H * 0.5), W, int(H * 0.8)], fill=(60, 115, 100, 42))
    img = Image.alpha_composite(img, haze.filter(ImageFilter.GaussianBlur(50)))
    img = add_noise(img)
    vignette(img, 0.4).save(os.path.join(BG, "forest.png"))
    print("forest ok")


def cyber():
    rng = random.Random(1337)
    img = vgrad(W, H, (5, 8, 18), (30, 10, 50)).convert("RGBA")
    d = ImageDraw.Draw(img)
    stars(d, rng, 240, int(H * 0.5))
    # туманности
    neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(neb)
    dn.ellipse([int(W * 0.05), int(H * 0.02), int(W * 0.55), int(H * 0.35)], fill=(140, 60, 200, 34))
    dn.ellipse([int(W * 0.6), int(H * 0.1), int(W * 0.95), int(H * 0.4)], fill=(50, 130, 220, 30))
    img = Image.alpha_composite(img, neb.filter(ImageFilter.GaussianBlur(120)))
    horizon = int(H * 0.58)
    # полосатое ретро-солнце
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsn = ImageDraw.Draw(sun)
    cx, cy, cr = W // 2, horizon + 10, 210
    for g in range(26):
        t = g / 26
        col = (int(255 - 20 * t), int(190 - 40 * t), int(40 + 130 * t), 255)
        yy = cy - cr + int(2 * cr * t)
        dsn.rectangle([cx - cr, yy, cx + cr, yy + max(1, int(2 * cr / 26)) + 1], fill=col)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=255)
    for k, y_off in enumerate(range(0, cr * 2, 24)):
        yy = cy - cr + y_off
        ImageDraw.Draw(mask).rectangle([0, yy + k * 4, W, yy + k * 4 + 5 + k], fill=0)
    sun.putalpha(Image.composite(sun.split()[3], Image.new("L", (W, H), 0), mask))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - cr * 1.7, cy - cr * 1.7, cx + cr * 1.7, cy + cr * 1.7],
                                  fill=(255, 80, 160, 75))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(120)))
    # хромовые горы на горизонте
    chrom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dch = ImageDraw.Draw(chrom)
    x = -40
    while x < W + 40:
        peak = horizon - rng.randint(30, 110)
        dch.polygon([(x, horizon), (x + 80, peak), (x + 170, horizon)], fill=(24, 12, 40, 255))
        dch.polygon([(x + 80, peak), (x + 120, horizon), (x + 80, horizon)], fill=(90, 40, 90, 120))
        x += 130
    img = Image.alpha_composite(img, chrom.filter(ImageFilter.GaussianBlur(1)))
    img = Image.alpha_composite(img, sun)
    d = ImageDraw.Draw(img)
    d.rectangle([0, horizon, W, H], fill=(8, 6, 20))
    # сетка
    for gx in range(-W, W * 2, 80):
        d.line([(W // 2 + (gx - W // 2), horizon), (W // 2 + (gx - W // 2) * 4, H)],
               fill=(255, 60, 180, 42), width=2)
    for gy in range(horizon, H, 28):
        t = (gy - horizon) / (H - horizon)
        d.line([(0, gy), (W, gy)], fill=(255, 60, 180, int(30 + 120 * t)), width=1)
    # неоновая линия горизонта
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(neon).rectangle([0, horizon - 4, W, horizon], fill=(120, 240, 255, 170))
    img = Image.alpha_composite(img, neon.filter(ImageFilter.GaussianBlur(3)))
    # сканлайны
    d = ImageDraw.Draw(img)
    for sy in range(0, H, 4):
        d.line([(0, sy), (W, sy)], fill=(0, 0, 0, 20), width=1)
    img = add_noise(img)
    vignette(img, 0.4).save(os.path.join(BG, "cyber.png"))
    print("cyber ok")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    aurora()
    mountains()
    forest()
    cyber()
    print("premium backgrounds ok")
