"""Фоны v7 — depot (ж/д депо Create) и contraption (механизм в работе)."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "resources", "backgrounds")
W, H = 1920, 1080

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


def blob(d, cx, cy, rx, ry, col, rng, irr=0.3):
    n = rng.randint(12, 20)
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
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], outline=col_d, width=3)
    for i in range(teeth):
        ang = 2 * math.pi * i / teeth
        x1 = cx + int((r - 2) * math.cos(ang - 0.12))
        y1 = cy + int((r - 2) * math.sin(ang - 0.12))
        x2 = cx + int((r + r * 0.22) * math.cos(ang))
        y2 = cy + int((r + r * 0.22) * math.sin(ang))
        x3 = cx + int((r - 2) * math.cos(ang + 0.12))
        y3 = cy + int((r - 2) * math.sin(ang + 0.12))
        d.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=col)
    hr = int(r * 0.32)
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=col_d)
    for i in range(4):
        ang = math.pi / 4 + i * math.pi / 2
        d.line([(cx + int(hr * math.cos(ang)), cy + int(hr * math.sin(ang))),
                (cx + int((r - 10) * math.cos(ang)), cy + int((r - 10) * math.sin(ang)))],
               fill=col_d, width=max(3, int(r * 0.08)))


def rivets(d, x1, y1, x2, y2, n, col):
    for i in range(n):
        t = i / max(1, n - 1)
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)


def save(img, name):
    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, name + ".png"))
    print(name, "ok")


# ─── DEPOT: ж/д депо Create — перрон, вагоны, кран ─────────────────────
def depot():
    rng = random.Random(707)
    img = vgrad(W, H, (30, 26, 22), (55, 46, 36)).convert("RGBA")

    # свет фонарей
    for lx in [int(W * 0.2), int(W * 0.55), int(W * 0.85)]:
        img = glow(img, lx, int(H * 0.3), 200, 140, (250, 200, 110), 38, 100)

    # каркас депо — балки
    beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(beams)
    db.rectangle([0, int(H * 0.1), W, int(H * 0.14)], fill=IRON_D)
    for x in range(80, W, 260):
        db.rectangle([x, int(H * 0.14), x + 22, int(H * 0.5)], fill=IRON_D)
        db.line([(x, int(H * 0.14)), (x + 22, int(H * 0.5))], fill=IRON, width=3)
    # фермы крыши
    for x in range(80, W, 130):
        db.line([(x, int(H * 0.14)), (x + 65, int(H * 0.08)), (x + 130, int(H * 0.14))],
                fill=IRON, width=2)
    img = Image.alpha_composite(img, beams)

    # задняя стена — кирпич
    wall = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(wall)
    for y in range(int(H * 0.14), int(H * 0.55), 26):
        off = (y // 26) % 2 * 30
        for x in range(-30 + off, W, 60):
            dw.rectangle([x, y, x + 54, y + 20], fill=(60, 40, 30, 160))
    wall = wall.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, wall)

    # фонари
    d = ImageDraw.Draw(img)
    for lx in [int(W * 0.2), int(W * 0.55), int(W * 0.85)]:
        d.line([(lx, int(H * 0.14)), (lx, int(H * 0.24))], fill=IRON_D, width=4)
        d.polygon([(lx - 24, int(H * 0.24)), (lx + 24, int(H * 0.24)),
                   (lx + 14, int(H * 0.29)), (lx - 14, int(H * 0.29))], fill=BRASS_D)
        d.ellipse([lx - 8, int(H * 0.26), lx + 8, int(H * 0.3)], fill=(255, 220, 130))

    # рельсы
    ry = int(H * 0.78)
    d.rectangle([0, ry, W, ry + 10], fill=(50, 42, 34))
    d.rectangle([0, ry, W, ry + 4], fill=STEEL)
    # шпалы
    for x in range(30, W, 90):
        d.rectangle([x, ry + 10, x + 55, ry + 22], fill=(70, 50, 32))

    # вагоны
    cars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cars)
    for i, cx in enumerate([int(W * 0.15), int(W * 0.5), int(W * 0.82)]):
        cw = 420 if i == 1 else 320
        ch = 130
        # корпус
        dc.rectangle([cx - cw // 2, ry - ch - 20, cx + cw // 2, ry - 20], fill=(122, 88, 48))
        dc.rectangle([cx - cw // 2, ry - ch - 20, cx + cw // 2, ry - ch], fill=(150, 110, 62))
        # латунная окантовка
        dc.rectangle([cx - cw // 2, ry - ch - 24, cx + cw // 2, ry - ch - 20], fill=BRASS_D)
        # цистерна посередине
        if i == 1:
            dc.rounded_rectangle([cx - cw // 2 + 20, ry - ch - 14, cx + cw // 2 - 20, ry - 26],
                                 radius=45, fill=STEEL)
            dc.rounded_rectangle([cx - cw // 2 + 20, ry - ch - 14, cx + cw // 2 - 20, ry - ch - 4],
                                 radius=45, fill=(120, 130, 142))
        else:
            # окна/решётки
            for k in range(4):
                wx = cx - cw // 2 + 25 + k * (cw - 60) // 4
                dc.rectangle([wx, ry - ch + 10, wx + 50, ry - 40], fill=(70, 55, 35))
                dc.rectangle([wx, ry - ch + 10, wx + 50, ry - ch + 30], fill=(90, 70, 45))
        # колёса
        for wx in [cx - cw // 2 + 40, cx + cw // 2 - 60]:
            dc.ellipse([wx, ry - 34, wx + 36, ry + 2], fill=IRON_D)
            dc.ellipse([wx + 8, ry - 26, wx + 28, ry - 6], fill=IRON)
    img = Image.alpha_composite(img, cars)

    # кран-балка сверху
    crane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dcr = ImageDraw.Draw(crane)
    dcr.rectangle([int(W * 0.3), int(H * 0.16), int(W * 0.7), int(H * 0.2)], fill=IRON_D)
    dcr.line([(int(W * 0.45), int(H * 0.2)), (int(W * 0.45), int(H * 0.34))], fill=IRON, width=5)
    dcr.rectangle([int(W * 0.42), int(H * 0.34), int(W * 0.48), int(H * 0.38)], fill=BRASS_D)
    dcr.ellipse([int(W * 0.43), int(H * 0.38), int(W * 0.47), int(H * 0.42)], fill=COPPER)
    img = Image.alpha_composite(img, crane)

    # пар
    for sx in [int(W * 0.35), int(W * 0.7)]:
        for k in range(5):
            st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            blob(ImageDraw.Draw(st), sx + rng.randint(-15, 15) + k * 8,
                 int(H * 0.5) - k * 22, rng.randint(22, 45), rng.randint(18, 36),
                 (200, 205, 210, 45 - k * 5), rng, 0.4)
            st = st.filter(ImageFilter.GaussianBlur(11))
            img = Image.alpha_composite(img, st)

    # пол
    d = ImageDraw.Draw(img)
    d.rectangle([0, ry + 22, W, H], fill=(28, 24, 20))

    save(img, "depot")


# ─── CONTRAPTION: работающий механизм Create ────────────────────────────
def contraption():
    rng = random.Random(808)
    img = vgrad(W, H, (22, 18, 14), (44, 36, 26)).convert("RGBA")
    img = glow(img, int(W * 0.5), int(H * 0.42), 480, 340, (230, 180, 95), 40, 150)

    # вал — горизонтальная ось
    d = ImageDraw.Draw(img)
    ax_y = int(H * 0.45)
    d.line([(0, ax_y), (W, ax_y)], fill=IRON, width=22)
    d.line([(0, ax_y - 5), (W, ax_y - 5)], fill=(120, 130, 142), width=4)

    # опоры вала
    for px in [int(W * 0.15), int(W * 0.85)]:
        d.polygon([(px - 30, ax_y), (px + 30, ax_y), (px + 45, H), (px - 45, H)], fill=IRON_D)
        rivets(d, px, ax_y + 20, px, H - 20, 4, BRASS)

    # шестерни на валу
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(g)
    gear(dg, int(W * 0.3), ax_y, 150, 14, BRASS + (240,), BRASS_D + (255,), rng)
    gear(dg, int(W * 0.52), ax_y - 10, 190, 16, COPPER + (235,), (120, 72, 40, 250), rng)
    gear(dg, int(W * 0.74), ax_y, 120, 12, BRASS_L + (230,), BRASS + (245,), rng)
    img = Image.alpha_composite(img, g)

    # поршень справа — качается
    piston = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(piston)
    px, py = int(W * 0.55), int(H * 0.66)
    # цилиндр
    dp.rectangle([px - 60, py - 45, px + 60, py + 45], fill=IRON)
    dp.rectangle([px - 60, py - 45, px + 60, py - 35], fill=STEEL)
    rivets(dp, px - 55, py + 20, px + 55, py + 20, 6, BRASS)
    # шток
    dp.rectangle([px - 12, py - 110, px + 12, py - 40], fill=STEEL)
    # головка штока
    dp.rectangle([px - 30, py - 125, px + 30, py - 105], fill=BRASS_D)
    # соединение с кривошипом
    dp.line([(px, py - 110), (int(W * 0.52), ax_y + 30)], fill=STEEL, width=10)
    dp.ellipse([int(W * 0.52) - 16, ax_y + 20, int(W * 0.52) + 16, ax_y + 50], fill=BRASS)
    img = Image.alpha_composite(img, piston)

    # маховик слева
    fw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dfw = ImageDraw.Draw(fw)
    fx, fy, fr = int(W * 0.12), int(H * 0.5), 90
    dfw.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], outline=IRON_D, width=22)
    dfw.ellipse([fx - fr + 8, fy - fr + 8, fx + fr - 8, fy + fr - 8], outline=IRON, width=4)
    dfw.ellipse([fx - 22, fy - 22, fx + 22, fy + 22], fill=BRASS_D)
    for k in range(6):
        a = k * math.pi / 3
        dfw.line([(fx + int(24 * math.cos(a)), fy + int(24 * math.sin(a))),
                  (fx + int((fr - 14) * math.cos(a)), fy + int((fr - 14) * math.sin(a)))],
                 fill=IRON, width=8)
    img = Image.alpha_composite(img, fw)

    # ремень к верхнему шкиву
    d = ImageDraw.Draw(img)
    bx, by, br2 = int(W * 0.68), int(H * 0.16), 46
    d.line([(int(W * 0.74), ax_y - 110), (bx + 10, by + 40)], fill=(80, 60, 40), width=12)
    d.ellipse([bx - br2, by - br2, bx + br2, by + br2], fill=IRON_D)
    d.ellipse([bx - br2 + 10, by - br2 + 10, bx + br2 - 10, by + br2 - 10], fill=IRON)
    d.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=BRASS_D)

    # маленькие шестерни-декор
    g2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg2 = ImageDraw.Draw(g2)
    for _ in range(4):
        x = rng.randint(60, W - 60)
        y = rng.randint(int(H * 0.05), int(H * 0.9))
        if abs(y - ax_y) < 220:
            continue
        r = rng.randint(28, 50)
        gear(dg2, x, y, r, rng.randint(8, 11),
             rng.choice([BRASS, COPPER, STEEL]) + (150,),
             BRASS_D + (170,), rng)
    img = Image.alpha_composite(img, g2)

    # лёгкий пар у цилиндра
    for k in range(4):
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        blob(ImageDraw.Draw(st), px + rng.randint(-20, 20) + k * 10,
             py - 130 - k * 20, rng.randint(18, 40), rng.randint(15, 32),
             (205, 210, 215, 40 - k * 6), rng, 0.4)
        st = st.filter(ImageFilter.GaussianBlur(10))
        img = Image.alpha_composite(img, st)

    save(img, "contraption")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    depot()
    contraption()
    print("ok v7 (2 Create backgrounds)")
