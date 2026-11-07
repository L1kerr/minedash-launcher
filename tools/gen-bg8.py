"""Фоны v8 — природа: forest, meadow, lake, mountains, sunrise, swamp, winter, birch.
Качественная отрисовка: многослойность, размытие дальних планов, мягкие переходы.
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
    n = rng.randint(16, 28)
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        r = 1 + rng.uniform(-irr, irr)
        pts.append((cx + int(rx * r * math.cos(ang)), cy + int(ry * r * math.sin(ang))))
    d.polygon(pts, fill=col)


def soft_polygon(img, pts, col, blur):
    """Заливка с мягким краем."""
    layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(pts, fill=col)
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(blur)))


def smooth_ridge(img, y, amp, col, rng, blur=12, alpha=255, w=None):
    """Хребет с плавным контуром (синус + шум) и мягким краем."""
    w = w or img.width
    phase = rng.uniform(0, 10)
    pts = [(0, img.height)]
    x = 0
    while x <= w:
        t = x / w
        yy = y + amp * math.sin(t * math.pi * 3 + phase) * 0.5 + rng.randint(-amp // 2, amp // 2)
        pts.append((x, int(yy)))
        x += 40
    pts += [(w, img.height)]
    return soft_polygon(img, pts, col + (alpha,), blur)


def tree(d, x, base, h, trunk, leaf, rng, pine=False):
    tw = max(4, h // 16)
    d.rectangle([x - tw // 2, base - h // 3, x + tw // 2, base], fill=trunk)
    if pine:
        for k in range(4):
            ly = base - h // 4 - k * (h // 4.5)
            lw = (h // 2) * (1 - k * 0.2)
            d.polygon([(x - lw, ly), (x + lw, ly), (x, ly - h // 3)], fill=leaf)
    else:
        blob(d, x, base - h // 2 - h // 5, h // 2.2, h // 2.4, leaf, rng, 0.2)
        blob(d, x - h // 6, base - h // 2, h // 3, h // 3, leaf, rng, 0.25)


def save(img, name):
    img = grain(img)
    vignette(img, 0.38).save(os.path.join(BG, name + ".png"))
    print(name, "ok", flush=True)


def clouds(img, rng, n, ymin, ymax, col, alpha=170, blur=10):
    """Мягкие многослойные облака."""
    for _ in range(n):
        cx, cy = rng.randint(100, W - 100), rng.randint(ymin, ymax)
        cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cl)
        for k in range(5):
            blob(dc, cx + k * rng.randint(40, 80) - 160, cy + rng.randint(-25, 25),
                 rng.randint(60, 120), rng.randint(25, 50), col + (alpha,), rng, 0.2)
        img = Image.alpha_composite(img, cl.filter(ImageFilter.GaussianBlur(blur)))
    return img


def mist(img, rng, y, n=4, col=(190, 210, 215, 30), alpha=None):
    for k in range(n):
        fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c = (col + (alpha,)) if alpha else col
        blob(ImageDraw.Draw(fg), rng.randint(200, W - 200), y + k * 30,
             rng.randint(350, 550), rng.randint(40, 80), c, rng, 0.25)
        img = Image.alpha_composite(img, fg.filter(ImageFilter.GaussianBlur(45)))
    return img


# ─── FOREST: хвойный лес в тумане ─────────────────────────────────────────
def forest():
    rng = random.Random(909)
    img = vgrad(W, H, (35, 60, 72), (20, 38, 44)).convert("RGBA")
    img = glow(img, int(W * 0.72), int(H * 0.18), 350, 220, (170, 225, 195), 35, 130)

    # дальние хребты — размытые
    img = smooth_ridge(img, int(H * 0.42), 70, (38, 66, 72), rng, blur=14, alpha=200)
    img = smooth_ridge(img, int(H * 0.52), 60, (30, 54, 60), rng, blur=8, alpha=230)
    img = mist(img, rng, int(H * 0.52), 4)

    # ряды ёлок
    d = ImageDraw.Draw(img)
    for col_a, (y, col, size, count) in enumerate([
        (int(H * 0.68), (30, 66, 56), 170, 15),
        (int(H * 0.8), (22, 52, 46), 230, 11),
        (int(H * 0.96), (15, 38, 34), 310, 7),
    ]):
        trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dt = ImageDraw.Draw(trees)
        for i in range(count):
            x = int((i + rng.uniform(0.15, 0.85)) * W / count)
            tree(dt, x, y + rng.randint(-25, 25), size + rng.randint(-50, 50),
                 (42, 32, 24), col + (255,), rng, pine=True)
        blur = [6, 3, 0][col_a]
        if blur:
            trees = trees.filter(ImageFilter.GaussianBlur(blur))
        img = Image.alpha_composite(img, trees)
    img = mist(img, rng, int(H * 0.72), 2, (190, 215, 220, 22))
    save(img, "forest")


# ─── MEADOW: цветущий луг ─────────────────────────────────────────────────
def meadow():
    rng = random.Random(1010)
    img = vgrad(W, H, (115, 175, 225), (205, 235, 205)).convert("RGBA")
    img = glow(img, int(W * 0.25), int(H * 0.12), 380, 260, (255, 250, 205), 100, 130)
    img = clouds(img, rng, 6, 60, int(H * 0.28), (255, 255, 255), 200, 14)

    # холмы — мягкие
    img = smooth_ridge(img, int(H * 0.55), 50, (125, 185, 95), rng, blur=10, alpha=250)
    img = smooth_ridge(img, int(H * 0.68), 40, (105, 170, 80), rng, blur=6, alpha=252)
    img = smooth_ridge(img, int(H * 0.82), 30, (90, 155, 70), rng, blur=3)

    d = ImageDraw.Draw(img)
    # цветы
    for _ in range(260):
        x = rng.randint(0, W)
        y = rng.randint(int(H * 0.62), H)
        col = rng.choice([(240, 125, 145), (250, 220, 95), (255, 255, 255), (160, 130, 225), (250, 170, 80)])
        r = rng.randint(3, 8)
        d.ellipse([x, y, x + r, y + r], fill=col + (rng.randint(170, 250),))
        if rng.random() < 0.5:
            d.ellipse([x + 1, y + 1, x + r - 1, y + r - 1], fill=lerp(col, (255, 255, 255), 0.4) + (120,))
    save(img, "meadow")


# ─── LAKE: озеро на закате ────────────────────────────────────────────────
def lake():
    rng = random.Random(1111)
    img = vgrad(W, H, (248, 165, 85), (125, 72, 92)).convert("RGBA")
    img = glow(img, int(W * 0.5), int(H * 0.4), 260, 180, (255, 222, 145), 130, 100)
    img = clouds(img, rng, 5, 60, int(H * 0.28), (205, 125, 115), 150, 14)

    # дальние горы
    img = smooth_ridge(img, int(H * 0.4), 90, (112, 62, 88), rng, blur=7, alpha=240)
    img = smooth_ridge(img, int(H * 0.47), 70, (92, 52, 78), rng, blur=4)

    d = ImageDraw.Draw(img)
    # солнце с ореолом
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    sx, sy = int(W * 0.5), int(H * 0.4)
    for r, a in [(90, 40), (72, 80), (58, 255)]:
        ds.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 235, 170, a))
    img = Image.alpha_composite(img, sun.filter(ImageFilter.GaussianBlur(4)))

    # вода
    wy = int(H * 0.52)
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(water)
    dw.rectangle([0, wy, W, H], fill=(72, 42, 72, 255))
    # отражение солнца — дорожка
    for k in range(20):
        y = wy + k * 13 + 5
        wd = max(10, 130 - k * 6)
        dw.ellipse([sx - wd, y - 3, sx + wd, y + 3], fill=(255, 212, 135, max(0, 175 - k * 8)))
    # блики на воде
    for _ in range(90):
        x = rng.randint(0, W)
        y = rng.randint(wy + 5, H)
        ln = rng.randint(15, 80)
        dw.line([(x, y), (x + ln, y)], fill=(255, 205, 145, rng.randint(25, 80)), width=2)
    img = Image.alpha_composite(img, water)
    # берег
    img = soft_polygon(img, [(0, wy), (int(W * 0.18), wy - 50), (int(W * 0.3), wy - 10),
                             (W, wy + 30), (W, wy + 70), (0, wy + 70)], (42, 32, 27, 255), 3)
    save(img, "lake")


# ─── MOUNTAINS: рассветные пики ───────────────────────────────────────────
def mountains():
    rng = random.Random(1212)
    img = vgrad(W, H, (95, 115, 165), (235, 165, 135)).convert("RGBA")
    img = glow(img, int(W * 0.8), int(H * 0.72), 450, 220, (255, 195, 125), 85, 140)
    img = clouds(img, rng, 4, 80, int(H * 0.2), (230, 200, 200), 120, 18)

    layers = [
        (int(H * 0.36), (145, 125, 155), 150, 5, 8, True),
        (int(H * 0.5), (115, 100, 135), 115, 4, 4, True),
        (int(H * 0.63), (88, 78, 112), 92, 3, 2, False),
        (int(H * 0.75), (62, 57, 86), 72, 2, 0, False),
    ]
    for y, col, amp, n, blur, snow in layers:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        for i in range(n):
            x0 = int(i * W / n) - rng.randint(0, 60)
            x1 = int((i + 1) * W / n) + rng.randint(0, 60)
            cx = (x0 + x1) // 2
            pk = y - rng.randint(amp // 2, amp)
            dl.polygon([(x0, y + 40), (cx - rng.randint(60, 140), y),
                        (cx, pk), (cx + rng.randint(60, 140), y), (x1, y + 40),
                        (x1, H), (x0, H)], fill=col + (255,))
            if snow:
                dl.polygon([(cx - 45, pk + 60), (cx, pk), (cx + 45, pk + 60),
                            (cx + 20, pk + 50), (cx - 15, pk + 70)], fill=(242, 243, 252, 255))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img = Image.alpha_composite(img, layer)
    # передний план
    img = smooth_ridge(img, int(H * 0.82), 60, (45, 42, 62), rng, blur=0)
    save(img, "mountains")


# ─── SUNRISE: туманный рассвет ────────────────────────────────────────────
def sunrise():
    rng = random.Random(1313)
    img = vgrad(W, H, (255, 205, 135), (205, 125, 95)).convert("RGBA")

    # солнце + ореол
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    sx, sy = int(W * 0.5), int(H * 0.52)
    for r, a in [(110, 35), (85, 70), (65, 255)]:
        ds.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 248, 220, a))
    img = Image.alpha_composite(img, sun.filter(ImageFilter.GaussianBlur(6)))
    img = glow(img, sx, sy, 350, 240, (255, 240, 200), 80, 110)

    # лучи
    for k in range(14):
        ang = math.pi * (0.12 + 0.76 * k / 13)
        beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(beam).line(
            [(sx + int(70 * math.cos(ang)), sy - int(70 * math.sin(ang))),
             (sx + int(950 * math.cos(ang)), sy - int(950 * math.sin(ang)))],
            fill=(255, 232, 185, 22), width=rng.randint(24, 44))
        img = Image.alpha_composite(img, beam.filter(ImageFilter.GaussianBlur(22)))

    # слои туманных холмов
    for k in range(5):
        t = k / 4
        img = smooth_ridge(img, int(H * (0.58 + k * 0.075)), 45,
                           lerp((205, 135, 105), (62, 46, 52), t), rng,
                           blur=14 - k * 3, alpha=int(200 + t * 55))
    # птицы
    d = ImageDraw.Draw(img)
    for _ in range(6):
        x, y = rng.randint(250, W - 250), rng.randint(100, int(H * 0.3))
        s = rng.randint(8, 18)
        d.arc([x, y, x + s, y + s // 2], 200, 340, fill=(45, 33, 30, 200), width=2)
    save(img, "sunrise")


# ─── SWAMP: болото с корягами ─────────────────────────────────────────────
def swamp():
    rng = random.Random(1414)
    img = vgrad(W, H, (62, 82, 72), (32, 47, 42)).convert("RGBA")
    img = glow(img, int(W * 0.4), int(H * 0.28), 280, 160, (148, 220, 162), 38, 115)
    img = smooth_ridge(img, int(H * 0.48), 45, (42, 64, 57), rng, blur=8, alpha=230)
    img = mist(img, rng, int(H * 0.5), 3)

    # деревья-коряги
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(trees)
    for x in [int(W * 0.15), int(W * 0.35), int(W * 0.62), int(W * 0.85)]:
        h = rng.randint(230, 340)
        base = int(H * 0.6)
        bend = rng.randint(-45, 45)
        for k in range(8):
            t = k / 8
            bx = x + int(bend * t)
            by = base - int(h * t)
            bw = max(9, 30 - k * 4)
            d.rounded_rectangle([bx - bw // 2, by - h // 8, bx + bw // 2, by + h // 8], radius=bw // 3, fill=(32, 27, 22, 255))
        for _ in range(4):
            vy = base - rng.randint(h // 3, h - 40)
            ln = rng.randint(60, 130) * rng.choice([1, -1])
            d.line([(x, vy), (x + ln, vy - rng.randint(-35, 35))], fill=(32, 27, 22, 255), width=6)
    img = Image.alpha_composite(img, trees)

    # вода
    wy = int(H * 0.66)
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(water)
    dw.rectangle([0, wy, W, H], fill=(26, 42, 44, 255))
    for _ in range(40):
        x = rng.randint(0, W)
        y = rng.randint(wy + 5, H)
        ln = rng.randint(20, 90)
        dw.line([(x, y), (x + ln, y)], fill=(100, 160, 130, rng.randint(20, 55)), width=2)
    img = Image.alpha_composite(img, water)

    # кувшинки
    lilies = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lilies)
    for _ in range(28):
        x, y = rng.randint(0, W), rng.randint(wy + 15, H)
        r = rng.randint(14, 34)
        dl.ellipse([x, y, x + r, y + r // 2], fill=(52, 95, 58, 255))
        dl.ellipse([x + 3, y + 2, x + r - 3, y + r // 2 - 3], fill=(70, 118, 72, 200))
        if rng.random() < 0.4:
            dl.ellipse([x + r // 3, y - 5, x + r // 3 + 9, y + 4], fill=(232, 202, 124, 255))
    img = Image.alpha_composite(img, lilies)
    img = mist(img, rng, wy - 25, 3, (150, 182, 162, 42))
    save(img, "swamp")


# ─── WINTER: зимний лес ───────────────────────────────────────────────────
def winter():
    rng = random.Random(1515)
    img = vgrad(W, H, (192, 212, 232), (152, 178, 202)).convert("RGBA")
    img = glow(img, int(W * 0.7), int(H * 0.15), 300, 180, (235, 242, 252), 70, 110)
    img = smooth_ridge(img, int(H * 0.4), 55, (172, 192, 218), rng, blur=10, alpha=230)

    # снегопад
    snow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(snow)
    for _ in range(600):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.choice([1, 2, 2, 3, 3, 4])
        ds.ellipse([x, y, x + r, y + r], fill=(255, 255, 255, rng.randint(70, 210)))
    img = Image.alpha_composite(img, snow)

    # ёлки в снегу
    for col_a, (y, size, count) in enumerate([
        (int(H * 0.6), 190, 12),
        (int(H * 0.76), 250, 9),
        (int(H * 0.94), 330, 6),
    ]):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dt = ImageDraw.Draw(layer)
        tcol = lerp((75, 105, 118), (30, 62, 72), col_a / 2)
        for i in range(count):
            x = int((i + rng.uniform(0.15, 0.85)) * W / count)
            tree(dt, x, y + rng.randint(-25, 25), size + rng.randint(-60, 60),
                 (52, 42, 37, 255), tcol + (255,), rng, pine=True)
            # шапки снега
            for k in range(4):
                ly = y - (size // 4) * (k + 1)
                dt.polygon([(x - 14, ly), (x + 14, ly), (x, ly - 9)], fill=(238, 243, 250, 235))
        blur = [7, 3, 0][col_a]
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img = Image.alpha_composite(img, layer)

    # сугробы
    ground = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(ground)
    dg.rectangle([0, int(H * 0.87), W, H], fill=(226, 234, 244, 255))
    for _ in range(10):
        x = rng.randint(0, W)
        blob(dg, x, int(H * 0.9), rng.randint(100, 240), rng.randint(25, 45), (236, 242, 250, 255), rng, 0.25)
    img = Image.alpha_composite(img, ground.filter(ImageFilter.GaussianBlur(2)))
    save(img, "winter")


# ─── BIRCH: берёзовая роща ────────────────────────────────────────────────
def birch():
    rng = random.Random(1616)
    img = vgrad(W, H, (152, 202, 232), (122, 182, 162)).convert("RGBA")
    img = glow(img, int(W * 0.6), int(H * 0.18), 320, 200, (255, 252, 214), 65, 105)
    img = clouds(img, rng, 5, 70, int(H * 0.25), (255, 255, 255), 180, 12)
    img = smooth_ridge(img, int(H * 0.5), 45, (102, 162, 122), rng, blur=10, alpha=240)
    img = smooth_ridge(img, int(H * 0.78), 35, (65, 115, 75), rng, blur=4)

    # берёзы в 3 ряда
    for layer, (size, count, col, wmul) in enumerate([
        (420, 6, (218, 221, 215), 1.0),
        (620, 4, (203, 208, 201), 1.2),
        (820, 3, (188, 193, 188), 1.45),
    ]):
        trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dt = ImageDraw.Draw(trees)
        base = H + 40
        for i in range(count):
            x = int((i + rng.uniform(0.25, 0.75)) * W / count)
            tw = int(24 * wmul)
            for k in range(30):
                yy = base - k * (size // 30)
                xx = x + int(math.sin(k * 0.25 + layer * 2) * 7)
                dt.rectangle([xx - tw // 2, yy - size // 30, xx + tw // 2, yy], fill=col + (255,))
            # чёрные полоски
            for _ in range(12):
                yy = base - rng.randint(60, size - 40)
                xx = x + int(math.sin(yy * 0.008) * 7)
                dt.rectangle([xx - tw // 2, yy, xx + tw // 2, yy + rng.randint(5, 12)], fill=(38, 38, 38, 235))
            # крона
            crown = lerp((145, 205, 105), (58, 132, 72), layer / 2)
            blob(dt, x, base - size, size // 3, size // 4, crown + (255,), rng, 0.2)
            blob(dt, x + size // 6, base - size + 70, size // 4, size // 5, crown + (255,), rng, 0.25)
        blur = [5, 2, 0][layer]
        if blur:
            trees = trees.filter(ImageFilter.GaussianBlur(blur))
        img = Image.alpha_composite(img, trees)
    save(img, "birch")


if __name__ == "__main__":
    os.makedirs(BG, exist_ok=True)
    forest()
    meadow()
    lake()
    mountains()
    sunrise()
    swamp()
    winter()
    birch()
    print("ok v8 (8 nature backgrounds)")
