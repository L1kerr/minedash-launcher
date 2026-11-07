"""Фоны MineDash Launcher v6 — 6 тем в стиле Create (индустриальный стимпанк).
factory, gears, steam, workshop, foundry, blueprint.
Запуск: python tools/gen-bg6.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")
W, H = 1920, 1080

# палитра Create: латунь, медь, тёмное железо
BRASS = (196, 150, 62)
BRASS_L = (228, 185, 95)
BRASS_D = (140, 102, 40)
COPPER = (178, 108, 60)
IRON = (58, 62, 70)
IRON_D = (38, 42, 48)
STEEL = (95, 105, 118)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, y / h))
    return img


def glow(img, cx, cy, rx, ry, col, alpha, blur=80):
    layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (alpha,))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


def grain(img, sigma=14, opacity=0.05):
    noise = Image.effect_noise((img.width, img.height), sigma).convert("RGBA")
    noise.putalpha(int(255 * opacity))
    return Image.alpha_composite(img.convert("RGBA"), noise)


def vignette(img, strength=0.36):
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


def gear(d, cx, cy, r, teeth, col, col_d, rng):
    """Зубчатое колесо."""
    # тело
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], outline=col_d, width=3)
    # зубья
    for i in range(teeth):
        ang = 2 * math.pi * i / teeth
        tw = r * 0.28
        th = r * 0.22
        x1 = cx + int((r - 2) * math.cos(ang - 0.12))
        y1 = cy + int((r - 2) * math.sin(ang - 0.12))
        x2 = cx + int((r + th) * math.cos(ang))
        y2 = cy + int((r + th) * math.sin(ang))
        x3 = cx + int((r - 2) * math.cos(ang + 0.12))
        y3 = cy + int((r - 2) * math.sin(ang + 0.12))
        d.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=col)
    # ступица
    hr = int(r * 0.32)
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=col_d)
    d.ellipse([cx - int(hr * 0.5), cy - int(hr * 0.5), cx + int(hr * 0.5), cy + int(hr * 0.5)],
              fill=col)
    # спицы
    for i in range(4):
        ang = math.pi / 4 + i * math.pi / 2
        d.line([(cx + int(hr * math.cos(ang)), cy + int(hr * math.sin(ang))),
                (cx + int((r - 10) * math.cos(ang)), cy + int((r - 10) * math.sin(ang)))],
               fill=col_d, width=max(3, int(r * 0.08)))


def rivets(d, x1, y1, x2, y2, n, col):
    """Заклёпки вдоль линии."""
    for i in range(n):
        t = i / max(1, n - 1)
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(255, 255, 255, 60))


def pipe(d, x1, y1, x2, y2, w, col, col_d, rng):
    """Труба с бликом."""
    d.line([(x1, y1), (x2, y2)], fill=col, width=w)
    d.line([(x1, y1), (x2, y2)], fill=col_d, width=max(1, w // 4))
    # блик
    off = w // 3
    d.line([(x1, y1 - off), (x2, y2 - off)], fill=(255, 255, 255, 40), width=max(1, w // 5))


def save(img, name):
    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, name + ".png"))
    print(name, "ok")


# ─── FACTORY: цех с конвейером ─────────────────────────────────────────────
def factory():
    rng = random.Random(101)
    img = vgrad(W, H, (24, 22, 20), (42, 38, 32)).convert("RGBA")

    # тёплый свет от ламп
    for _ in range(5):
        x = rng.randint(150, W - 150)
        img = glow(img, x, int(H * 0.12), 200, 120, (250, 190, 90), 40, 90)

    # задняя стена — панели
    wall = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(wall)
    for x in range(0, W, 160):
        dw.line([(x, 0), (x, int(H * 0.62))], fill=(30, 28, 25, 200), width=3)
    for y in range(0, int(H * 0.62), 130):
        dw.line([(0, y), (W, y)], fill=(30, 28, 25, 160), width=2)
    img = Image.alpha_composite(img, wall)

    # большие шестерни на стене
    gears = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(gears)
    gear(dg, int(W * 0.78), int(H * 0.3), 130, 14, BRASS_D + (200,), (90, 66, 28, 220), rng)
    gear(dg, int(W * 0.68), int(H * 0.42), 80, 11, BRASS + (190,), BRASS_D + (210,), rng)
    gear(dg, int(W * 0.88), int(H * 0.46), 60, 9, COPPER + (180,), (120, 72, 40, 200), rng)
    img = Image.alpha_composite(img, gears)

    # конвейер
    belt_y = int(H * 0.72)
    d = ImageDraw.Draw(img)
    d.rectangle([0, belt_y, W, belt_y + 40], fill=IRON_D)
    d.rectangle([0, belt_y, W, belt_y + 8], fill=STEEL)
    # ролики
    for x in range(40, W, 120):
        d.ellipse([x - 14, belt_y + 40, x + 14, belt_y + 68], fill=IRON)
        d.ellipse([x - 5, belt_y + 49, x + 5, belt_y + 59], fill=STEEL)
    # ящики на конвейере
    for x in [int(W * 0.15), int(W * 0.38), int(W * 0.6)]:
        bw, bh = rng.randint(70, 100), rng.randint(55, 80)
        d.rectangle([x, belt_y - bh, x + bw, belt_y], fill=(122, 88, 48))
        d.rectangle([x, belt_y - bh, x + bw, belt_y - bh + 10], fill=(150, 110, 62))
        d.line([(x, belt_y - bh), (x + bw, belt_y)], fill=(95, 68, 36), width=3)
        d.line([(x + bw, belt_y - bh), (x, belt_y)], fill=(95, 68, 36), width=3)

    # трубы сверху
    pipes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pipes)
    pipe(dp, 0, int(H * 0.18), W, int(H * 0.18), 26, IRON + (255,), IRON_D + (255,), rng)
    pipe(dp, 0, int(H * 0.26), int(W * 0.55), int(H * 0.26), 18, STEEL + (255,), IRON + (255,), rng)
    # фланцы
    for x in [200, 600, 1000, 1400, 1800]:
        dp.rectangle([x - 8, int(H * 0.18) - 18, x + 8, int(H * 0.18) + 18], fill=IRON_D)
    img = Image.alpha_composite(img, pipes)

    # пар
    for _ in range(4):
        x = rng.randint(200, W - 200)
        y = rng.randint(int(H * 0.2), int(H * 0.4))
        steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for k in range(5):
            blob(ImageDraw.Draw(steam), x + k * 12, y - k * 18,
                 rng.randint(25, 55), rng.randint(20, 40), (200, 205, 210, 45), rng, 0.35)
        steam = steam.filter(ImageFilter.GaussianBlur(14))
        img = Image.alpha_composite(img, steam)

    save(img, "factory")


# ─── GEARS: часовая механика ───────────────────────────────────────────────
def gears():
    rng = random.Random(202)
    img = vgrad(W, H, (18, 16, 14), (36, 30, 22)).convert("RGBA")
    img = glow(img, int(W * 0.5), int(H * 0.45), 600, 450, (200, 150, 70), 30, 160)

    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(g)
    # центральная большая шестерня
    gear(dg, int(W * 0.5), int(H * 0.46), 240, 18, BRASS + (235,), BRASS_D + (255,), rng)
    # сцепленные вокруг
    gear(dg, int(W * 0.28), int(H * 0.3), 130, 13, COPPER + (220,), (120, 72, 40, 240), rng)
    gear(dg, int(W * 0.72), int(H * 0.32), 150, 14, BRASS_L + (210,), BRASS + (230,), rng)
    gear(dg, int(W * 0.32), int(H * 0.68), 110, 12, STEEL + (200,), IRON + (220,), rng)
    gear(dg, int(W * 0.7), int(H * 0.66), 95, 11, BRASS + (215,), BRASS_D + (235,), rng)
    gear(dg, int(W * 0.12), int(H * 0.5), 70, 10, COPPER + (190,), (110, 66, 36, 210), rng)
    gear(dg, int(W * 0.88), int(H * 0.5), 80, 10, BRASS_L + (200,), BRASS + (220,), rng)
    # маленькие
    for _ in range(6):
        x = rng.randint(80, W - 80)
        y = rng.randint(80, H - 80)
        r = rng.randint(30, 55)
        gear(dg, x, y, r, rng.randint(8, 11),
             rng.choice([BRASS, COPPER, STEEL]) + (170,),
             BRASS_D + (190,), rng)
    img = Image.alpha_composite(img, g)

    # оси и заклёпки
    d = ImageDraw.Draw(img)
    for cx, cy in [(int(W * 0.5), int(H * 0.46)), (int(W * 0.28), int(H * 0.3)),
                   (int(W * 0.72), int(H * 0.32))]:
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=IRON_D)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=STEEL)

    save(img, "gears")


# ─── STEAM: паровая машина ─────────────────────────────────────────────────
def steam():
    rng = random.Random(303)
    img = vgrad(W, H, (26, 24, 22), (48, 42, 36)).convert("RGBA")
    img = glow(img, int(W * 0.5), int(H * 0.5), 500, 350, (220, 170, 90), 35, 150)

    # котёл — большой цилиндр
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = int(W * 0.32), int(H * 0.3), int(W * 0.36), int(H * 0.4)
    # тело котла с градиентом
    for i in range(bw):
        t = i / bw
        col = lerp((70, 74, 82), (120, 128, 140), math.sin(t * math.pi))
        d.line([(bx + i, by), (bx + i, by + bh)], fill=col)
    # торцы
    d.ellipse([bx - 20, by, bx + 40, by + bh], fill=IRON)
    d.ellipse([bx + bw - 40, by, bx + bw + 20, by + bh], fill=IRON_D)
    # ободы
    for fx in [0.2, 0.5, 0.8]:
        x = bx + int(bw * fx)
        d.rectangle([x - 6, by - 4, x + 6, by + bh + 4], fill=BRASS_D)
        rivets(d, x, by + 8, x, by + bh - 8, 6, BRASS)

    # манометр
    gx, gy, gr = bx + int(bw * 0.5), by - 60, 42
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=BRASS)
    d.ellipse([gx - gr + 8, gy - gr + 8, gx + gr - 8, gy + gr - 8], fill=(235, 230, 215))
    # стрелка
    ang = rng.uniform(-0.6, 0.9)
    d.line([(gx, gy), (gx + int((gr - 14) * math.cos(ang - math.pi / 2)),
                        gy + int((gr - 14) * math.sin(ang - math.pi / 2)))],
           fill=(140, 30, 25), width=3)
    d.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=IRON_D)

    # трубы
    pipes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pipes)
    pipe(dp, bx + int(bw * 0.25), by, bx + int(bw * 0.25), 0, 30, IRON + (255,), IRON_D + (255,), rng)
    pipe(dp, bx + int(bw * 0.75), by, bx + int(bw * 0.75), 0, 24, STEEL + (255,), IRON + (255,), rng)
    pipe(dp, bx + bw, by + int(bh * 0.5), W, by + int(bh * 0.5), 28, IRON + (255,), IRON_D + (255,), rng)
    pipe(dp, bx, by + int(bh * 0.6), 0, by + int(bh * 0.6), 22, COPPER + (255,), (120, 72, 40, 255), rng)
    # вентили
    for vx, vy in [(bx + int(bw * 0.25), int(H * 0.14)), (bx + int(bw * 0.75), int(H * 0.1))]:
        dp.ellipse([vx - 22, vy - 22, vx + 22, vy + 22], fill=BRASS)
        dp.ellipse([vx - 8, vy - 8, vx + 8, vy + 8], fill=BRASS_D)
        for k in range(4):
            a = k * math.pi / 2
            dp.line([(vx, vy), (vx + int(20 * math.cos(a)), vy + int(20 * math.sin(a)))],
                    fill=BRASS_D, width=4)
    img = Image.alpha_composite(img, pipes)

    # пар из труб
    for sx in [bx + int(bw * 0.25), bx + int(bw * 0.75)]:
        for k in range(7):
            st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            blob(ImageDraw.Draw(st), sx + rng.randint(-20, 20) + k * 10,
                 int(H * 0.1) - k * 26, rng.randint(28, 60), rng.randint(22, 45),
                 (205, 210, 215, 50 - k * 4), rng, 0.4)
            st = st.filter(ImageFilter.GaussianBlur(12))
            img = Image.alpha_composite(img, st)

    # пол
    d = ImageDraw.Draw(img)
    d.rectangle([0, by + bh, W, H], fill=(30, 28, 26))
    for x in range(0, W, 90):
        d.line([(x, by + bh), (x, H)], fill=(22, 20, 18), width=2)

    save(img, "steam")


# ─── WORKSHOP: мастерская ──────────────────────────────────────────────────
def workshop():
    rng = random.Random(404)
    img = vgrad(W, H, (30, 26, 22), (52, 44, 36)).convert("RGBA")
    img = glow(img, int(W * 0.5), int(H * 0.2), 500, 250, (240, 190, 110), 45, 130)

    # верстак
    d = ImageDraw.Draw(img)
    ty = int(H * 0.62)
    d.rectangle([int(W * 0.1), ty, int(W * 0.9), ty + 26], fill=(110, 78, 44))
    d.rectangle([int(W * 0.1), ty, int(W * 0.9), ty + 6], fill=(140, 102, 58))
    # ножки
    for lx in [int(W * 0.14), int(W * 0.86)]:
        d.rectangle([lx, ty + 26, lx + 30, H], fill=(80, 56, 32))
    # ящики под верстаком
    d.rectangle([int(W * 0.3), ty + 40, int(W * 0.7), ty + 130], fill=(90, 64, 38))
    for k in range(3):
        yy = ty + 50 + k * 28
        d.rectangle([int(W * 0.32), yy, int(W * 0.68), yy + 20], fill=(70, 50, 30))
        d.ellipse([int(W * 0.49), yy + 6, int(W * 0.51), yy + 14], fill=BRASS)

    # инструменты на верстаке
    # гаечный ключ
    wx, wy = int(W * 0.2), ty - 14
    d.line([(wx, wy), (wx + 90, wy - 20)], fill=STEEL, width=10)
    d.ellipse([wx - 12, wy - 12, wx + 12, wy + 12], fill=STEEL)
    d.ellipse([wx - 6, wy - 6, wx + 6, wy + 6], fill=(40, 44, 50))
    # молоток
    hx, hy = int(W * 0.42), ty - 10
    d.line([(hx, hy), (hx + 70, hy - 30)], fill=(120, 84, 46), width=8)
    d.rectangle([hx + 60, hy - 48, hx + 92, hy - 18], fill=IRON)
    # шестерня на столе
    gear(d, int(W * 0.68), ty - 26, 34, 10, BRASS + (255,), BRASS_D + (255,), rng)

    # полка с деталями на стене
    d.rectangle([int(W * 0.15), int(H * 0.28), int(W * 0.85), int(H * 0.3)], fill=(95, 68, 40))
    for x in range(int(W * 0.2), int(W * 0.8), 110):
        # банки/детали
        bw = rng.randint(30, 55)
        bh = rng.randint(40, 70)
        col = rng.choice([BRASS, COPPER, STEEL, IRON])
        d.rectangle([x, int(H * 0.28) - bh, x + bw, int(H * 0.28)], fill=col)
        d.rectangle([x, int(H * 0.28) - bh, x + bw, int(H * 0.28) - bh + 6],
                    fill=lerp(col, (255, 255, 255), 0.25))

    # чертёж на стене
    bx, by = int(W * 0.62), int(H * 0.1)
    d.rectangle([bx, by, bx + 260, by + 160], fill=(40, 60, 90))
    d.rectangle([bx + 8, by + 8, bx + 252, by + 152], outline=(180, 200, 230), width=1)
    # схема шестерни
    gcx, gcy = bx + 90, by + 80
    d.ellipse([gcx - 40, gcy - 40, gcx + 40, gcy + 40], outline=(200, 220, 245), width=2)
    d.ellipse([gcx - 15, gcy - 15, gcx + 15, gcy + 15], outline=(200, 220, 245), width=1)
    for k in range(8):
        a = k * math.pi / 4
        d.line([(gcx + int(40 * math.cos(a)), gcy + int(40 * math.sin(a))),
                (gcx + int(52 * math.cos(a)), gcy + int(52 * math.sin(a)))],
               fill=(200, 220, 245), width=2)
    # линии-размеры
    d.line([(bx + 170, by + 40), (bx + 240, by + 40)], fill=(200, 220, 245), width=1)
    d.line([(bx + 170, by + 70), (bx + 230, by + 70)], fill=(200, 220, 245), width=1)
    d.line([(bx + 170, by + 100), (bx + 245, by + 100)], fill=(200, 220, 245), width=1)

    # лампа
    lx = int(W * 0.3)
    d.line([(lx, 0), (lx, int(H * 0.14))], fill=IRON_D, width=4)
    d.polygon([(lx - 30, int(H * 0.14)), (lx + 30, int(H * 0.14)),
               (lx + 18, int(H * 0.2)), (lx - 18, int(H * 0.2))], fill=BRASS_D)
    img = glow(img, lx, int(H * 0.22), 160, 110, (250, 210, 130), 55, 60)

    # пол
    d.rectangle([0, int(H * 0.86), W, H], fill=(34, 30, 26))

    save(img, "workshop")


# ─── FOUNDRY: литейный цех ─────────────────────────────────────────────────
def foundry():
    rng = random.Random(505)
    img = vgrad(W, H, (20, 12, 8), (48, 24, 12)).convert("RGBA")

    # жар от печи
    img = glow(img, int(W * 0.5), int(H * 0.55), 550, 380, (255, 120, 30), 60, 170)
    img = glow(img, int(W * 0.5), int(H * 0.6), 280, 200, (255, 190, 60), 70, 100)

    # печь — ковш с расплавом
    d = ImageDraw.Draw(img)
    cx, cy = int(W * 0.5), int(H * 0.58)
    # корпус ковша
    d.polygon([(cx - 130, cy - 90), (cx + 130, cy - 90),
               (cx + 100, cy + 90), (cx - 100, cy + 90)], fill=IRON_D)
    # обод
    d.rectangle([cx - 140, cy - 100, cx + 140, cy - 80], fill=BRASS_D)
    rivets(d, cx - 130, cy - 90, cx + 130, cy - 90, 8, BRASS)
    # расплав
    d.ellipse([cx - 110, cy - 85, cx + 110, cy - 55], fill=(255, 150, 40))
    d.ellipse([cx - 90, cy - 80, cx + 90, cy - 60], fill=(255, 200, 80))
    # блики расплава
    for _ in range(8):
        x = cx + rng.randint(-80, 80)
        y = cy - 70 + rng.randint(-8, 8)
        d.ellipse([x - 4, y - 2, x + 4, y + 2], fill=(255, 235, 140, 200))

    # поток металла
    pour = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dpour = ImageDraw.Draw(pour)
    dpour.polygon([(cx - 12, cy - 70), (cx + 12, cy - 70),
                   (cx + 8, cy + 180), (cx - 8, cy + 180)], fill=(255, 170, 50, 230))
    dpour.line([(cx, cy - 70), (cx, cy + 180)], fill=(255, 220, 110, 200), width=4)
    pour = pour.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, pour)
    # брызги внизу
    for _ in range(14):
        x = cx + rng.randint(-70, 70)
        y = cy + 170 + rng.randint(-20, 30)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 190, 70, rng.randint(120, 230)))

    # формы внизу
    for fx in [cx - 260, cx + 180]:
        d.rectangle([fx, cy + 150, fx + 90, cy + 230], fill=(60, 40, 28))
        d.rectangle([fx, cy + 150, fx + 90, cy + 160], fill=(80, 55, 38))

    # конструкции — балки
    beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(beams)
    db.rectangle([0, int(H * 0.12), W, int(H * 0.16)], fill=IRON_D)
    for x in range(60, W, 240):
        db.rectangle([x, int(H * 0.16), x + 24, int(H * 0.5)], fill=IRON_D)
        db.line([(x, int(H * 0.16)), (x + 24, int(H * 0.5))], fill=IRON, width=3)
        db.line([(x + 24, int(H * 0.16)), (x, int(H * 0.5))], fill=IRON, width=3)
    img = Image.alpha_composite(img, beams)

    # искры
    sparks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sparks)
    for _ in range(50):
        x = cx + rng.randint(-260, 260)
        y = rng.randint(int(H * 0.25), int(H * 0.75))
        r = rng.choice([1, 2, 2, 3])
        ds.ellipse([x, y, x + r, y + r],
                   fill=rng.choice([(255, 160, 40), (255, 210, 90)]) + (rng.randint(90, 230),))
    sparks = sparks.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, sparks)

    # дым/жар
    for _ in range(6):
        x = cx + rng.randint(-150, 150)
        y = rng.randint(int(H * 0.05), int(H * 0.3))
        sm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sm).ellipse([x - 70, y - 50, x + 70, y + 50],
                                   fill=(70, 45, 35, rng.randint(25, 55)))
        sm = sm.filter(ImageFilter.GaussianBlur(28))
        img = Image.alpha_composite(img, sm)

    save(img, "foundry")


# ─── BLUEPRINT: чертёж ─────────────────────────────────────────────────────
def blueprint():
    rng = random.Random(606)
    # синяя бумага
    img = Image.new("RGBA", (W, H), (24, 52, 96))
    d = ImageDraw.Draw(img)
    # лёгкий градиент
    for y in range(H):
        t = y / H
        col = lerp((26, 56, 102), (18, 42, 80), t)
        d.line([(0, y), (W, y)], fill=col + (255,))

    LINE = (190, 215, 245)
    LINE_D = (150, 180, 220)

    # сетка
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        dg.line([(x, 0), (x, H)], fill=LINE_D + (35,), width=1)
    for y in range(0, H, 60):
        dg.line([(0, y), (W, y)], fill=LINE_D + (35,), width=1)
    # крупная сетка
    for x in range(0, W, 300):
        dg.line([(x, 0), (x, H)], fill=LINE_D + (60,), width=1)
    for y in range(0, H, 300):
        dg.line([(0, y), (W, y)], fill=LINE_D + (60,), width=1)
    img = Image.alpha_composite(img, grid)

    d = ImageDraw.Draw(img)
    # рамка чертежа
    d.rectangle([40, 40, W - 40, H - 40], outline=LINE + (200,), width=2)
    d.rectangle([52, 52, W - 52, H - 52], outline=LINE + (120,), width=1)

    # большая шестерня — чертёж
    gcx, gcy, gr = int(W * 0.32), int(H * 0.45), 200
    d.ellipse([gcx - gr, gcy - gr, gcx + gr, gcy + gr], outline=LINE + (230,), width=2)
    d.ellipse([gcx - int(gr * 0.7), gcy - int(gr * 0.7),
               gcx + int(gr * 0.7), gcy + int(gr * 0.7)], outline=LINE + (180,), width=1)
    d.ellipse([gcx - 40, gcy - 40, gcx + 40, gcy + 40], outline=LINE + (230,), width=2)
    # зубья
    for i in range(16):
        ang = 2 * math.pi * i / 16
        d.line([(gcx + int(gr * math.cos(ang)), gcy + int(gr * math.sin(ang))),
                (gcx + int((gr + 26) * math.cos(ang)), gcy + int((gr + 26) * math.sin(ang)))],
               fill=LINE + (220,), width=3)
    # спицы
    for i in range(6):
        ang = i * math.pi / 3
        d.line([(gcx + int(40 * math.cos(ang)), gcy + int(40 * math.sin(ang))),
                (gcx + int((gr * 0.7) * math.cos(ang)), gcy + int((gr * 0.7) * math.sin(ang)))],
               fill=LINE + (160,), width=1)
    # осевые линии
    d.line([(gcx - gr - 60, gcy), (gcx + gr + 60, gcy)], fill=LINE_D + (140,), width=1)
    d.line([(gcx, gcy - gr - 60), (gcx, gcy + gr + 60)], fill=LINE_D + (140,), width=1)

    # размерные линии
    def dim(x1, y1, x2, y2, label=None):
        d.line([(x1, y1), (x2, y2)], fill=LINE + (200,), width=1)
        # стрелки
        for px, py, dx, dy in [(x1, y1, 1, 0), (x2, y2, -1, 0)]:
            d.line([(px, py), (px + 8 * dx, py - 4)], fill=LINE + (200,), width=1)
            d.line([(px, py), (px + 8 * dx, py + 4)], fill=LINE + (200,), width=1)

    dim(gcx - gr, gcy + gr + 50, gcx + gr, gcy + gr + 50)
    dim(gcx + gr + 50, gcy - gr, gcx + gr + 50, gcy + gr)

    # поршень справа — чертёж
    px, py = int(W * 0.72), int(H * 0.4)
    d.rectangle([px - 90, py - 60, px + 90, py + 60], outline=LINE + (220,), width=2)
    d.rectangle([px - 60, py - 40, px + 60, py + 40], outline=LINE + (160,), width=1)
    d.line([(px - 90, py), (px - 150, py)], fill=LINE + (200,), width=2)
    d.ellipse([px - 175, py - 25, px - 125, py + 25], outline=LINE + (200,), width=2)
    # штриховка
    for k in range(-5, 6):
        d.line([(px - 60 + k * 12, py - 40), (px - 60 + k * 12 + 20, py - 20)],
               fill=LINE_D + (110,), width=1)

    # вал внизу
    d.rectangle([int(W * 0.55), int(H * 0.72), int(W * 0.9), int(H * 0.78)],
                outline=LINE + (200,), width=2)
    for k in range(6):
        x = int(W * 0.57) + k * 55
        d.line([(x, int(H * 0.72)), (x + 20, int(H * 0.78))], fill=LINE_D + (120,), width=1)

    # штамп в углу
    d.rectangle([W - 320, H - 160, W - 60, H - 60], outline=LINE + (180,), width=2)
    d.line([(W - 320, H - 120), (W - 60, H - 120)], fill=LINE + (140,), width=1)
    d.line([(W - 320, H - 90), (W - 60, H - 90)], fill=LINE + (140,), width=1)

    # лёгкие потёртости бумаги
    for _ in range(10):
        x, y = rng.randint(0, W), rng.randint(0, H)
        blob(d, x, y, rng.randint(30, 80), rng.randint(20, 50),
             (255, 255, 255, rng.randint(2, 5)), rng, 0.4)

    save(img, "blueprint")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    factory()
    gears()
    steam()
    workshop()
    foundry()
    blueprint()
    print("all Create backgrounds ok (6 themes)")
