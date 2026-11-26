# -*- coding: utf-8 -*-
"""피코의 캠핑장 습격 — 배경·HUD·오버레이 생성기.

도형만으로 3개 맵 배경(낮/해질녘/밤)과 HUD 이미지를 만든다.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import art_sprites as A

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
W, H = 1280, 720

FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
FONT_R = "C:/Windows/Fonts/malgun.ttf"

INK = (22, 36, 30)
CREAM = (250, 246, 236)
AMBER = (233, 166, 63)
AMBER_D = (185, 124, 34)
MUTED = (154, 170, 158)


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def text(d, xy, s, size, color, bold=True, anchor="la", stroke=0,
         stroke_fill=(0, 0, 0, 180), letterspace=0):
    f = font(size, bold)
    x, y = xy
    if letterspace:
        cx = x
        for ch in s:
            d.text((cx, y), ch, font=f, fill=color, anchor=anchor,
                   stroke_width=stroke, stroke_fill=stroke_fill)
            cx += f.getlength(ch) + letterspace
        return cx - letterspace
    d.text((x, y), s, font=f, fill=color, anchor=anchor,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return x + f.getlength(s)


def soft_shadow(im, box, alpha=90, blur=8):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([int(v) for v in box], fill=(8, 14, 10, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(layer)


def radial(w, h, color, a0, a1=0, cx=0.5, cy=0.5, power=1.6):
    """가운데가 밝고 바깥으로 사라지는 원형 그라디언트."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            dx = (x / w - cx) * 2
            dy = (y / h - cy) * 2
            t = min(1.0, (dx * dx + dy * dy) ** 0.5)
            a = int(a0 + (a1 - a0) * (t ** power))
            if a > 0:
                px[x, y] = (color[0], color[1], color[2], min(255, a))
    return im


# ---------------------------------------------------------------- grounds
def grain(im, color, n, size=(1, 4), alpha=(18, 70), ss=1):
    d = ImageDraw.Draw(im)
    w, h = im.size
    rnd = random.Random(7)
    for _ in range(n):
        x = rnd.uniform(0, w)
        y = rnd.uniform(0, h)
        s = rnd.uniform(*size) * ss
        a = rnd.randint(*alpha)
        d.ellipse([x - s, y - s, x + s, y + s],
                  fill=(color[0], color[1], color[2], a))


def grass_tufts(im, color, n, ss=1, rnd_seed=3):
    d = ImageDraw.Draw(im)
    w, h = im.size
    rnd = random.Random(rnd_seed)
    for _ in range(n):
        x = rnd.uniform(0, w)
        y = rnd.uniform(0, h)
        k = rnd.uniform(0.7, 1.6) * ss
        a = rnd.randint(60, 130)
        for dx in (-2, 0, 2):
            d.line([x + dx * k, y, x + dx * k * 1.8, y - 6 * k],
                   fill=(color[0], color[1], color[2], a),
                   width=max(1, int(1.2 * ss)))


def vignette(im, color=(8, 16, 12), a=120, inn=0.55):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-w * 0.25, -h * 0.30, w * 1.25, h * 1.30], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w // 10))
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(mask.point(lambda v: int((255 - v) * a / 255)))
    im.alpha_composite(layer)


def bg_forest():
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (108, 138, 88, 255))
    d = ImageDraw.Draw(im)
    # 바닥 얼룩
    rnd = random.Random(11)
    for _ in range(90):
        cx, cy = rnd.uniform(0, W) * ss, rnd.uniform(0, H) * ss
        rx, ry = rnd.uniform(60, 200) * ss, rnd.uniform(40, 120) * ss
        col = rnd.choice([(96, 126, 80), (118, 148, 94), (102, 132, 84)])
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (110,))
    # 흙길
    path = [(90, 610), (300, 560), (520, 590), (700, 520), (900, 470),
            (1080, 400), (1210, 340)]
    pl = [(x * ss, y * ss) for (x, y) in path]
    d.line(pl, fill=(176, 150, 108, 255), width=88 * ss, joint="curve")
    d.line(pl, fill=(195, 170, 126, 255), width=64 * ss, joint="curve")
    d.line(pl, fill=(204, 181, 138, 255), width=34 * ss, joint="curve")
    # 작은 갈림길
    side = [(520, 588), (470, 470), (500, 380)]
    d.line([(x * ss, y * ss) for (x, y) in side], fill=(180, 155, 112, 255),
           width=54 * ss, joint="curve")
    d.line([(x * ss, y * ss) for (x, y) in side], fill=(199, 175, 132, 255),
           width=28 * ss, joint="curve")
    # 잔디/풀/꽃
    grass_tufts(im, (74, 102, 66), 220, ss)
    grain(im, (60, 88, 56), 500, size=(1, 3), alpha=(20, 60), ss=ss)
    rr = random.Random(5)
    for _ in range(120):
        x, y = rr.uniform(0, W) * ss, rr.uniform(0, H) * ss
        c = rr.choice([(240, 236, 210), (233, 166, 63), (214, 120, 90)])
        d.ellipse([x - 2 * ss, y - 2 * ss, x + 2 * ss, y + 2 * ss], fill=c + (190,))
    # 햇빛 얼룩
    sun = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sun)
    for (cx, cy, rx, ry) in [(330, 210, 260, 150), (760, 300, 300, 160),
                             (1090, 560, 220, 130), (180, 520, 180, 110)]:
        ds.ellipse([(cx - rx) * ss, (cy - ry) * ss, (cx + rx) * ss, (cy + ry) * ss],
                   fill=(246, 240, 168, 46))
    sun = sun.filter(ImageFilter.GaussianBlur(26 * ss))
    im.alpha_composite(sun)
    vignette(im, (36, 58, 38), 90)
    return im.resize((W, H), Image.LANCZOS)


def bg_lake():
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (146, 140, 92, 255))
    d = ImageDraw.Draw(im)
    rnd = random.Random(21)
    # 마른 풀밭
    for _ in range(80):
        cx, cy = rnd.uniform(0, W) * ss, rnd.uniform(0, 470) * ss
        rx, ry = rnd.uniform(60, 180) * ss, rnd.uniform(30, 90) * ss
        col = rnd.choice([(134, 128, 84), (156, 148, 100), (122, 118, 80)])
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (110,))
    # 물
    d.rectangle([0, 468 * ss, W * ss, H * ss], fill=(58, 82, 96, 255))
    for i in range(46):
        t = i / 46
        y0 = 468 + t * (H - 468)
        band = Image.new("RGBA", (W * ss, int((H - 468) / 46 * ss) + 2),
                         (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        col = (int(224 - 150 * t), int(140 - 60 * t), int(96 - 20 * t), 46)
        bd.rectangle([0, 0, W * ss, band.size[1]], fill=col)
        im.alpha_composite(band, (0, int(y0 * ss)))
    # 잔물결
    for _ in range(150):
        x = rnd.uniform(0, W) * ss
        y = rnd.uniform(476, H) * ss
        ln = rnd.uniform(20, 90) * ss
        a = rnd.randint(30, 80)
        c = (242, 196, 140, a) if rnd.random() < 0.55 else (150, 190, 196, a)
        d.line([x, y, x + ln, y], fill=c, width=max(1, int(1.6 * ss)))
    # 해질녘 반사
    refl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(refl)
    for i in range(16):
        y = (500 + i * 14) * ss
        wgt = 1 - i / 16
        dr.ellipse([(700 - 210 * wgt) * ss, y, (700 + 210 * wgt) * ss, y + 12 * ss],
                   fill=(246, 178, 104, int(60 * wgt)))
    refl = refl.filter(ImageFilter.GaussianBlur(10 * ss))
    im.alpha_composite(refl)
    # 모래 해변
    shore = [(0, 470), (200, 455), (420, 480), (640, 462), (860, 486),
             (1080, 464), (1280, 478)]
    d.line([(x * ss, y * ss) for (x, y) in shore], fill=(201, 178, 128, 255),
           width=34 * ss, joint="curve")
    d.line([(x * ss, y * ss) for (x, y) in shore], fill=(216, 196, 150, 255),
           width=16 * ss, joint="curve")
    # 부두
    dock = (812, 452, 948, 700)
    d.rectangle([dock[0] * ss, dock[1] * ss, dock[2] * ss, dock[3] * ss],
                fill=(122, 92, 62, 255))
    for i in range(10):
        y = dock[1] + 8 + i * 25
        d.line([dock[0] * ss, y * ss, dock[2] * ss, y * ss],
               fill=(96, 70, 46, 255), width=2 * ss)
    d.rectangle([dock[0] * ss, dock[1] * ss, dock[0] * ss + 10 * ss, dock[3] * ss],
                fill=(146, 112, 76, 255))
    d.rectangle([dock[2] * ss - 10 * ss, dock[1] * ss, dock[2] * ss, dock[3] * ss],
                fill=(146, 112, 76, 255))
    for (px, py) in [(766, 520), (986, 580)]:
        d.ellipse([px * ss, py * ss, (px + 40) * ss, (py + 22) * ss],
                  fill=(94, 88, 74, 255))
    # 풀/돌
    grass_tufts(im, (110, 108, 66), 160, ss, rnd_seed=9)
    grain(im, (70, 70, 48), 300, size=(1, 3), alpha=(18, 50), ss=ss)
    # 노을 색조
    warm = Image.new("RGBA", im.size, (240, 150, 80, 0))
    warm.putalpha(26)
    im.alpha_composite(warm)
    vignette(im, (44, 34, 30), 110)
    return im.resize((W, H), Image.LANCZOS)


def bg_festival():
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (34, 46, 42, 255))
    d = ImageDraw.Draw(im)
    rnd = random.Random(33)
    for _ in range(90):
        cx, cy = rnd.uniform(0, W) * ss, rnd.uniform(0, H) * ss
        rx, ry = rnd.uniform(60, 200) * ss, rnd.uniform(40, 120) * ss
        col = rnd.choice([(30, 42, 38), (40, 54, 48), (26, 38, 34)])
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (120,))
    # 자갈 광장
    d.rounded_rectangle([60 * ss, 330 * ss, 1220 * ss, 700 * ss], 40 * ss,
                        fill=(58, 58, 50, 255))
    d.rounded_rectangle([100 * ss, 360 * ss, 1180 * ss, 690 * ss], 30 * ss,
                        fill=(66, 65, 56, 255))
    grain(im, (40, 40, 34), 700, size=(1, 3), alpha=(20, 70), ss=ss)
    grain(im, (120, 112, 96), 200, size=(1, 2), alpha=(20, 50), ss=ss)
    # 축제 조명 웅덩이
    for (cx, cy, rx) in [(190, 250, 220), (480, 250, 220), (790, 250, 220),
                         (1090, 250, 200), (330, 600, 190), (980, 620, 190)]:
        glow = radial(int(rx * 2 * ss), int(rx * 1.6 * ss), (246, 190, 96), 64)
        im.alpha_composite(glow, (int((cx - rx) * ss), int((cy - rx * 0.8) * ss)))
    # 가랜드 전구
    def garland(x0, y0, x1, y1, sag, n=14):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + math.sin(math.pi * t) * sag
            pts.append((x * ss, y * ss))
        d.line(pts, fill=(74, 66, 54, 255), width=max(1, int(1.6 * ss)))
        for i in range(1, n):
            x, y = pts[i]
            d.ellipse([x - 5 * ss, y - 2 * ss, x + 5 * ss, y + 8 * ss],
                      fill=(250, 214, 132, 255))
            d.ellipse([x - 9 * ss, y - 6 * ss, x + 9 * ss, y + 12 * ss],
                      fill=(250, 205, 120, 34))
    garland(20, 60, 640, 40, 90)
    garland(640, 40, 1260, 70, 80, 12)
    garland(40, 300, 1240, 300, 40, 20)
    # 바닥 조명 반사
    for (x, y) in [(320, 210), (620, 235), (930, 225)]:
        d.line([x * ss, y * ss, x * ss, (y + 160) * ss],
               fill=(246, 200, 110, 26), width=26 * ss)
    grass_tufts(im, (34, 52, 42), 120, ss, rnd_seed=17)
    vignette(im, (6, 12, 10), 140)
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- light cone
def cone(color):
    n = 256
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    cx, cy = n / 2, n / 2
    half = math.radians(55)
    for y in range(n):
        for x in range(n):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy) / (n / 2)
            if r > 1 or r < 0.02:
                continue
            ang = abs(math.atan2(dy, dx))
            if ang > half:
                continue
            edge = 1 - (ang / half) ** 2.4
            fade = (1 - r) ** 1.5
            a = 96 * edge * fade
            if a > 1:
                px[x, y] = (color[0], color[1], color[2], min(255, int(a)))
    return im


def shadow():
    im = Image.new("RGBA", (128, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([10, 12, 118, 44], fill=(6, 12, 8, 110))
    return im.filter(ImageFilter.GaussianBlur(6))


def glow(size, color, a=90):
    return radial(size, size, color, a, 0)


def bg_tent():
    """텐트 안 — 캔버스 벽, 깃발·전등·별 스티커, 수납 포켓, 술 달린 패턴 매트."""
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (74, 58, 44, 255))
    d = ImageDraw.Draw(im)
    # 천 패널
    for i in range(9):
        x0 = i * W / 9
        base = 88 if i % 2 else 80
        d.rectangle([x0 * ss, 0, (x0 + W / 9) * ss, H * ss],
                    fill=(base, base - 22, base - 40, 255))
        d.line([x0 * ss, 0, x0 * ss, H * ss], fill=(52, 40, 30, 210), width=3 * ss)
        d.line([(x0 + 3) * ss, 0, (x0 + 3) * ss, H * ss],
               fill=(112, 92, 70, 80), width=1 * ss)
    # 천 이음선
    d.line([0, 104 * ss, W * ss, 104 * ss], fill=(52, 40, 30, 200), width=3 * ss)
    d.line([0, 108 * ss, W * ss, 108 * ss], fill=(116, 96, 74, 90), width=1 * ss)

    def sag(x, top, drop, x0=150, x1=1130):
        """두 지점 사이에 늘어진 줄의 y 좌표."""
        t = (x - x0) / (x1 - x0)
        return top + drop * (1.0 - (2.0 * t - 1.0) ** 2)

    # ---- 깃발 줄 (천장)
    flag_colors = [(196, 88, 72, 235), (232, 176, 86, 235),
                   (90, 132, 104, 235), (116, 104, 152, 235)]
    d.line([(x * ss, sag(x, 44, 26) * ss) for x in range(150, 1131, 18)],
           fill=(46, 36, 28, 255), width=2 * ss, joint="curve")
    for i, x in enumerate(range(166, 1111, 62)):
        y1, y2 = sag(x, 44, 26), sag(x + 44, 44, 26)
        d.polygon([(x * ss, y1 * ss), ((x + 44) * ss, y2 * ss),
                   ((x + 22) * ss, (y1 + y2) / 2 * ss + 26 * ss)],
                  fill=flag_colors[i % len(flag_colors)])
    # ---- 전등 줄 (깃발 아래, 따뜻한 전구)
    d.line([(x * ss, sag(x, 82, 42) * ss) for x in range(150, 1131, 18)],
           fill=(44, 34, 26, 255), width=3 * ss, joint="curve")
    for x in range(178, 1110, 78):
        y = sag(x, 82, 42)
        d.line([(x * ss, y * ss), (x * ss, (y + 11) * ss)],
               fill=(44, 34, 26, 255), width=2 * ss)
        d.ellipse([(x - 11) * ss, (y + 8) * ss, (x + 11) * ss, (y + 30) * ss],
                  fill=(255, 206, 120, 60))
        d.ellipse([(x - 6) * ss, (y + 10) * ss, (x + 6) * ss, (y + 24) * ss],
                  fill=(255, 226, 150, 255))
        d.ellipse([(x - 3) * ss, (y + 12) * ss, (x + 1) * ss, (y + 17) * ss],
                  fill=(255, 250, 224, 255))
    # ---- 천 벽 스티커 (깃발 줄 위 빈 틈)
    for sx, sy, r in ((286, 24, 8), (982, 26, 7)):
        pts = []
        for k in range(10):
            ang = math.pi / 2 + k * math.pi / 5
            rad = r if k % 2 == 0 else r * 0.45
            pts.append(((sx + math.cos(ang) * rad) * ss,
                        (sy - math.sin(ang) * rad) * ss))
        d.polygon(pts, fill=(232, 190, 112, 215))
    # 오른쪽 벽 초승달 스티커
    d.ellipse([(1172 * ss, 14 * ss), (1196 * ss, 38 * ss)],
              fill=(236, 198, 122, 220))
    d.ellipse([(1178 * ss, 11 * ss), (1200 * ss, 33 * ss)],
              fill=(82, 60, 45, 255))
    # 바닥 매트
    d.rectangle([0, 150 * ss, W * ss, H * ss], fill=(104, 86, 64, 255))
    d.line([0, 150 * ss, W * ss, 150 * ss], fill=(132, 110, 82, 235), width=4 * ss)
    d.rounded_rectangle([320 * ss, 320 * ss, 1000 * ss, 656 * ss], 32 * ss,
                        fill=(126, 96, 72, 255))
    d.rounded_rectangle([342 * ss, 338 * ss, 978 * ss, 638 * ss], 26 * ss,
                        fill=(142, 110, 82, 255))
    for y in range(352, 640, 26):
        d.line([352 * ss, y * ss, 968 * ss, y * ss], fill=(128, 98, 72, 110),
               width=2 * ss)
    # 러그 테두리 바느질 + 가운데 별 무늬
    d.rounded_rectangle([356 * ss, 352 * ss, 964 * ss, 624 * ss], 20 * ss,
                        outline=(178, 140, 102, 140), width=2 * ss)
    for x in range(372, 956, 28):
        d.line([(x * ss, 346 * ss), ((x + 10) * ss, 356 * ss)],
               fill=(190, 150, 108, 120), width=2 * ss)
        d.line([(x * ss, 630 * ss), ((x + 10) * ss, 640 * ss)],
               fill=(190, 150, 108, 120), width=2 * ss)
    cx, cy = 640, 492
    d.polygon([(cx * ss, (cy - 40) * ss), ((cx + 10) * ss, (cy - 10) * ss),
               ((cx + 40) * ss, cy * ss), ((cx + 10) * ss, (cy + 10) * ss),
               (cx * ss, (cy + 40) * ss), ((cx - 10) * ss, (cy + 10) * ss),
               ((cx - 40) * ss, cy * ss), ((cx - 10) * ss, (cy - 10) * ss)],
              fill=(166, 130, 94, 95))
    # 러그 끝술 + 옆면 작은 마름모
    for x in (348, 972):
        for y in range(352, 628, 24):
            d.line([(x * ss, y * ss), ((x - 9) * ss, (y + 6) * ss)],
                   fill=(190, 150, 108, 120), width=2 * ss)
            d.line([(x * ss, y * ss), ((x + 9) * ss, (y + 6) * ss)],
                   fill=(190, 150, 108, 120), width=2 * ss)
    for x in (342, 978):
        d.polygon([(x * ss, 474 * ss), ((x + 8) * ss, 486 * ss),
                   (x * ss, 498 * ss), ((x - 8) * ss, 486 * ss)],
                  fill=(176, 138, 100, 150))
    # 문 앞 바닥 스크래치 (오래 캠핑한 흔적)
    for x, y in ((556, 690), (724, 684)):
        d.arc([(x - 18) * ss, (y - 7) * ss, (x + 18) * ss, (y + 7) * ss],
              200, 340, fill=(74, 58, 44, 95), width=2 * ss)
    # ---- 좌우 벽 수납 포켓 (걷지 못하는 벽면 안쪽에만 걸어 둔다)
    for bx in (96, 1184):
        d.rounded_rectangle([(bx - 42) * ss, 56 * ss, (bx + 42) * ss, 136 * ss],
                            7 * ss, fill=(64, 50, 38, 255),
                            outline=(110, 88, 64, 255), width=2 * ss)
        d.line([(bx - 34) * ss, 92 * ss, (bx + 34) * ss, 92 * ss],
               fill=(96, 76, 56, 255), width=2 * ss)
        for x0, x1 in ((bx - 30, bx - 6), (bx + 6, bx + 30)):
            d.rounded_rectangle([x0 * ss, 100 * ss, x1 * ss, 132 * ss],
                                4 * ss, fill=(92, 72, 54, 255))
        d.rounded_rectangle([(bx - 24) * ss, 78 * ss, (bx - 12) * ss, 106 * ss],
                            2 * ss, fill=(196, 168, 110, 255))
        d.rounded_rectangle([(bx + 8) * ss, 80 * ss, (bx + 22) * ss, 104 * ss],
                            2 * ss, fill=(124, 148, 118, 255))
    # ---- 왼쪽 벽 지도 메모 (포켓 위, 역시 벽면 안쪽)
    d.rounded_rectangle([52 * ss, 8 * ss, 140 * ss, 48 * ss], 3 * ss,
                        fill=(168, 142, 104, 255), outline=(88, 68, 48, 255),
                        width=2 * ss)
    d.line([(62 * ss, 30 * ss), (86 * ss, 20 * ss), (110 * ss, 32 * ss),
            (130 * ss, 24 * ss)], fill=(110, 86, 62, 220), width=2 * ss)
    d.ellipse([(92 * ss, 12 * ss), (100 * ss, 20 * ss)],
              fill=(190, 88, 72, 255))
    # 지퍼 출입구 (아래 가운데)
    d.rectangle([594 * ss, 656 * ss, 686 * ss, H * ss], fill=(44, 35, 26, 255))
    d.polygon([(594 * ss, 656 * ss), (640 * ss, 620 * ss), (686 * ss, 656 * ss)],
              fill=(58, 46, 34, 255))
    for x in range(598, 686, 7):
        d.line([x * ss, 660 * ss, x * ss, H * ss], fill=(92, 76, 58, 190),
               width=2 * ss)
    d.line([0, 104 * ss, 40 * ss, 150 * ss], fill=(60, 46, 34, 200), width=3 * ss)
    d.line([(606 * ss, 712 * ss), (674 * ss, 712 * ss)],
           fill=(150, 124, 92, 170), width=2 * ss)
    # 랜턴 빛
    im.alpha_composite(radial(W * ss, H * ss, (255, 214, 146), 54, 0, 0.30, 0.30))
    grain(im, (40, 30, 22), 700, size=(1, 3), alpha=(14, 46), ss=ss)
    vignette(im, (18, 12, 8), 165)
    return im.resize((W, H), Image.LANCZOS)


def bg_backstage():
    """무대 뒤 조리 부스 — 커튼, 전등 트러스, 조리대와 김 나는 냄비."""
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (38, 30, 46, 255))
    d = ImageDraw.Draw(im)
    # 무대 바닥
    d.rectangle([0, 150 * ss, W * ss, H * ss], fill=(62, 48, 44, 255))
    for y in range(160, H, 28):
        d.line([0, y * ss, W * ss, y * ss], fill=(84, 64, 56, 90), width=2 * ss)
    # 접힌 커튼
    for i in range(16):
        x0 = i * W / 16
        base = 58 if i % 2 else 46
        d.rectangle([x0 * ss, 0, (x0 + W / 16) * ss, 150 * ss],
                    fill=(base, base - 14, base - 26, 255))
        d.line([x0 * ss, 0, x0 * ss, 150 * ss], fill=(26, 20, 30, 190), width=3 * ss)
    # 전등 트러스
    d.rectangle([0, 96 * ss, W * ss, 108 * ss], fill=(28, 24, 30, 255))
    for x in (180, 420, 660, 900, 1140):
        d.ellipse([(x - 16) * ss, 108 * ss, (x + 16) * ss, 132 * ss],
                  fill=(255, 214, 140, 230))
        d.ellipse([(x - 10) * ss, 110 * ss, (x + 10) * ss, 128 * ss],
                  fill=(255, 240, 200, 255))
    # 조리대와 냄비
    d.rounded_rectangle([120 * ss, 250 * ss, 1160 * ss, 300 * ss], 12 * ss,
                        fill=(96, 70, 52, 255))
    d.rounded_rectangle([136 * ss, 258 * ss, 1144 * ss, 292 * ss], 8 * ss,
                        fill=(132, 98, 72, 255))
    d.ellipse([760 * ss, 236 * ss, 880 * ss, 276 * ss], fill=(48, 42, 46, 255))
    d.ellipse([770 * ss, 240 * ss, 870 * ss, 270 * ss], fill=(196, 112, 56, 255))
    d.ellipse([780 * ss, 244 * ss, 860 * ss, 264 * ss], fill=(232, 164, 82, 255))
    d.line([820 * ss, 246 * ss, 850 * ss, 210 * ss],
           fill=(210, 214, 206, 230), width=5 * ss)
    for x, y, r in ((800, 220, 14), (830, 198, 18), (856, 176, 12)):
        d.ellipse([(x - r) * ss, (y - r) * ss, (x + r) * ss, (y + r) * ss],
                  fill=(236, 238, 226, 34))
    # 지퍼 출입구 (아래 가운데)
    d.rectangle([594 * ss, 656 * ss, 686 * ss, H * ss], fill=(26, 20, 28, 255))
    d.polygon([(594 * ss, 656 * ss), (640 * ss, 620 * ss), (686 * ss, 656 * ss)],
              fill=(40, 30, 40, 255))
    for x in range(598, 686, 7):
        d.line([x * ss, 660 * ss, x * ss, H * ss], fill=(74, 60, 74, 190), width=2 * ss)
    im.alpha_composite(radial(W * ss, H * ss, (255, 206, 138), 46, 0, 0.5, 0.32))
    grain(im, (30, 22, 32), 700, size=(1, 3), alpha=(12, 42), ss=ss)
    vignette(im, (12, 8, 16), 170)
    return im.resize((W, H), Image.LANCZOS)


def zzz():
    """자는 사람 위로 떠오르는 Z."""
    im = Image.new("RGBA", (104, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x, y, s, a) in ((10, 44, 20, 210), (34, 24, 26, 180), (62, 2, 32, 140)):
        text(d, (x, y), "Z", s, (236, 244, 232, a), bold=True,
             stroke=2, stroke_fill=(10, 18, 12, 120))
    return im


def door_marker():
    """텐트 출입구 표시 (지면 발광 + 화살표)."""
    im = Image.new("RGBA", (168, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([12, 24, 156, 72], fill=(233, 166, 63, 40))
    d.ellipse([26, 34, 142, 68], outline=(255, 214, 140, 150), width=3)
    d.polygon([(84, 8), (98, 28), (70, 28)], fill=(255, 226, 164, 220))
    return im


# ---------------------------------------------------------------- HUD
def hud_bar():
    im = Image.new("RGBA", (W, 86), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(86):
        t = y / 85
        a = int(226 - 90 * t ** 1.6)
        d.line([0, y, W, y], fill=(11, 22, 17, a))
    d.line([0, 85, W, 85], fill=(233, 166, 63, 70), width=2)
    return im


def plate(w, h, radius=10, fill=(14, 26, 20, 176), edge=(233, 166, 63, 90)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, w - 2, h - 2], radius, fill=fill, outline=edge, width=2)
    return im


def map_label(name, sub, accent=AMBER):
    im = plate(352, 64, 10)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 6, 63], 3, fill=accent + (255,))
    text(d, (20, 10), name, 24, CREAM + (255,))
    text(d, (20, 40), sub, 11, accent + (235,), bold=True, letterspace=1.2)
    return im


def gauge_label():
    im = plate(104, 26, 7, (14, 26, 20, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    text(d, (10, 5), "감지도", 12, (206, 216, 204, 255), bold=True)
    return im


def slot(empty=True):
    im = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if empty:
        d.rounded_rectangle([1, 1, 38, 38], 8, fill=(255, 255, 255, 16),
                            outline=(255, 255, 255, 60), width=2)
    else:
        d.rounded_rectangle([1, 1, 38, 38], 8, fill=(233, 166, 63, 56),
                            outline=(233, 166, 63, 220), width=2)
    return im


def controls():
    items = [("WASD", "이동"), ("SHIFT", "달리기"), ("E", "줍기/낚시"),
             ("Q", "낚싯배"), ("X", "수풀 앉기"), ("R", "다시 시작")]
    fk, fl = font(11, True), font(12, True)
    spans, x = [], 16
    for key, label in items:
        kw = fk.getlength(key) + 14
        spans.append((key, label, kw))
        x += kw + 7 + fl.getlength(label) + 14
    im = plate(int(x), 40, 9, (12, 24, 18, 168), (255, 255, 255, 34))
    d = ImageDraw.Draw(im)
    x = 16
    for key, label, kw in spans:
        d.rounded_rectangle([x, 8, x + kw, 31], 5, fill=(233, 166, 63, 235))
        text(d, (x + kw / 2, 12), key, 11, (24, 34, 26, 255), anchor="ma")
        x += kw + 7
        x += text(d, (x, 12), label, 12, (226, 233, 222, 235))
        x += 14
    return im


def prompt():
    return prompt_label("줍기", 112)


def prompt_label(label, w=112, key="E"):
    im = plate(w, 44, 10, (14, 26, 20, 210), (233, 166, 63, 190))
    d = ImageDraw.Draw(im)
    d.ellipse([9, 7, 39, 37], fill=(233, 166, 63, 255))
    text(d, (24, 14), key, 16, (26, 36, 26, 255), anchor="ma")
    text(d, (47, 14), label, 14, CREAM + (255,))
    return im


def toast(s="음식 +1"):
    im = Image.new("RGBA", (150, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, 147, 41], 9, fill=(233, 166, 63, 232))
    text(d, (75, 10), s, 18, (28, 34, 26, 255), anchor="ma")
    return im


def toast_bad(s="썩은 음식!"):
    im = Image.new("RGBA", (150, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, 147, 41], 9, fill=(178, 52, 38, 238),
                        outline=(255, 178, 140, 255), width=2)
    text(d, (75, 10), s, 16, (255, 240, 226, 255), anchor="ma")
    return im


def slot_rotten():
    im = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 38, 38], 8, fill=(150, 44, 32, 170),
                        outline=(220, 96, 72, 230), width=2)
    d.line([(13, 13), (27, 27)], fill=(255, 206, 180, 255), width=3)
    d.line([(27, 13), (13, 27)], fill=(255, 206, 180, 255), width=3)
    return im


def sit_badge():
    im = Image.new("RGBA", (124, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 122, 32], 8, fill=(16, 38, 24, 220),
                        outline=(122, 190, 118, 220), width=2)
    d.ellipse([10, 10, 26, 26], fill=(116, 178, 108, 250))
    d.ellipse([14, 14, 22, 22], fill=(38, 74, 42, 255))
    text(d, (34, 8), "수풀 앉기", 13, (224, 244, 214, 255))
    return im


def hidden_badge():
    im = Image.new("RGBA", (104, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 102, 32], 8, fill=(16, 38, 24, 216),
                        outline=(122, 190, 118, 200), width=2)
    d.ellipse([11, 11, 27, 27], fill=(116, 178, 108, 250))
    d.ellipse([15, 15, 23, 23], fill=(38, 74, 42, 255))
    text(d, (34, 8), "은신 중", 14, (224, 244, 214, 255))
    return im


def counter_plate(label, value, color=AMBER, w=158):
    """HUD 상단 카운터 — '남은 음식: 5개', '진짜 음식: 2/3'."""
    im = Image.new("RGBA", (w, 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, w - 2, 28], 8, fill=(10, 20, 15, 214),
                        outline=color + (200,), width=2)
    text(d, (11, 5), label, 14, CREAM + (255,))
    text(d, (w - 11, 5), value, 14, color + (255,), anchor="ra")
    return im


def real_mark():
    """진짜 음식 칸에 붙는 작은 별."""
    im = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = 9 if k % 2 == 0 else 4
        pts.append((10 + math.cos(a) * r, 9 - math.sin(a) * r))
    d.polygon(pts, fill=AMBER + (255,), outline=(90, 54, 12, 255))
    return im


def chase_banner():
    im = Image.new("RGBA", (372, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 370, 58], 12, fill=(140, 34, 24, 226),
                        outline=(255, 132, 96, 232), width=2)
    d.polygon([(38, 30), (50, 12), (62, 30)], fill=(255, 176, 132, 245))
    d.rectangle([47, 21, 53, 27], fill=(140, 34, 24, 255))
    d.rectangle([47, 29, 53, 33], fill=(140, 34, 24, 255))
    text(d, (78, 8), "추격 중", 21, (255, 238, 226, 255))
    text(d, (78, 36), "SHIFT 로 달려서 따돌려라", 11, (255, 196, 168, 240),
         letterspace=0.6)
    return im


def noise_ring():
    """발소리 반경 표시용 지면 링."""
    im = Image.new("RGBA", (320, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, a in ((0, 130), (1, 100), (2, 72), (3, 46)):
        pad = 6 + i * 5
        d.ellipse([pad, pad * 0.56, 319 - pad, 179 - pad * 0.56],
                  outline=(255, 241, 206, a), width=3)
    return im


def alert_mark():
    im = Image.new("RGBA", (34, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([3, 12, 31, 40], fill=(220, 83, 48, 245))
    text(d, (17, 17), "!", 20, (255, 246, 232, 255), anchor="ma")
    d.polygon([(13, 16), (17, 4), (21, 16)], fill=(220, 83, 48, 245))
    return im


# ---------------------------------------------------------------- overlays
def intro(i, name, time_label, foods, tip):
    im = Image.new("RGBA", (W, H), (6, 12, 9, 168))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=AMBER + (230,))
    d.rectangle([0, H - 8, W, H], fill=AMBER + (230,))
    # 왼쪽 텍스트 블록
    d.rectangle([96, 250, 102, 470], fill=AMBER + (255,))
    text(d, (126, 246), f"MAP 0{i + 1} / 03", 15, AMBER + (255,), letterspace=3.0)
    text(d, (126, 272), name, 56, CREAM + (255,))
    text(d, (126, 350), time_label, 24, AMBER + (255,))
    d.line([126, 400, 620, 400], fill=(255, 255, 255, 46), width=2)
    text(d, (126, 416), tip, 19, (206, 218, 204, 255))
    text(d, (126, 448), "수풀에서 X로 앉으면 완전 은신  ·  WASD 이동, E 줍기", 15,
         (146, 164, 152, 255), bold=False)
    # 오른쪽 음식 5개
    for k, f in enumerate(foods):
        cx = 780 + k * 110
        d.ellipse([cx - 46, 330, cx + 46, 422], fill=(255, 255, 255, 20),
                  outline=(233, 166, 63, 90), width=2)
        im.alpha_composite(f, (int(cx - f.width / 2), int(376 - f.height / 2)))
        text(d, (cx, 434), f"{i * 5 + k + 1}", 12, (170, 184, 168, 255), anchor="ma")
    text(d, (780, 300), "THIS MAP", 11, AMBER + (255,), bold=True, letterspace=2.4)
    text(d, (W - 96, H - 44), "PICO'S CAMP HEIST", 11, (120, 138, 126, 220),
         bold=True, letterspace=2.6, anchor="ra")
    return im


def overlay_end(kind="caught"):
    im = Image.new("RGBA", (W, H), (6, 10, 8, 190))
    d = ImageDraw.Draw(im)
    col = (220, 83, 48) if kind == "caught" else (233, 166, 63)
    title = "들켰다!" if kind == "caught" else "클리어!"
    sub = ("감지 게이지 100%  —  캠핑장 사람들에게 들켰다"
           if kind == "caught" else "진짜 음식 3개, 세 캠핑장을 모두 털었다")
    hint = "R  다시 시작"
    d.rounded_rectangle([300, 232, 980, 500], 22, fill=(13, 24, 18, 236),
                        outline=col + (230,), width=3)
    d.rectangle([300, 232, 980, 240], fill=col + (255,))
    text(d, (640, 268), title, 66, CREAM + (255,), anchor="ma")
    text(d, (640, 356), sub, 21, (206, 218, 204, 255), anchor="ma", bold=False)
    d.line([420, 404, 860, 404], fill=(255, 255, 255, 34), width=2)
    kw = 210
    d.rounded_rectangle([640 - kw / 2, 424, 640 + kw / 2, 468], 9,
                        fill=col + (235,))
    text(d, (640, 433), hint, 18, (28, 34, 26, 255), anchor="ma")
    text(d, (640, 518), "PICO'S CAMP HEIST", 11, (120, 138, 126, 200),
         bold=True, letterspace=2.8, anchor="ma")
    return im


def dark_vignette():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-W * 0.15, -H * 0.2, W * 1.15, H * 1.2], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(90))
    im.putalpha(mask.point(lambda v: int((255 - v) * 0.55)))
    out = Image.new("RGBA", (W, H), (4, 8, 6, 255))
    out.putalpha(im.getchannel("A"))
    return out


def red_vignette():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(mask)
    d.ellipse([W * 0.06, H * 0.08, W * 0.94, H * 0.92], fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(80))
    out = Image.new("RGBA", (W, H), (198, 50, 34, 255))
    out.putalpha(mask.point(lambda v: int(v * 0.9)))
    return out


def gauge_bg():
    im = Image.new("RGBA", (244, 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 242, 24], 8, fill=(8, 16, 12, 210),
                        outline=(255, 255, 255, 44), width=2)
    for i in range(1, 5):
        x = 2 + i * 48
        d.line([x, 6, x, 20], fill=(255, 255, 255, 26), width=1)
    return im


def map_clear():
    im = Image.new("RGBA", (W, H), (6, 12, 9, 120))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([370, 288, 910, 432], 18, fill=(13, 24, 18, 232),
                        outline=AMBER + (220,), width=3)
    text(d, (640, 310), "MAP CLEAR", 15, AMBER + (255,), anchor="ma", letterspace=4.0)
    text(d, (640, 338), "진짜 음식 1개 확보!", 34, CREAM + (255,), anchor="ma")
    text(d, (640, 390), "다음 캠핑장으로 이동합니다", 16, (196, 210, 196, 255),
         anchor="ma", bold=False)
    return im


# ---------------------------------------------------------------- 낚싯배 / 낚시
def bg_lake_open():
    """호수 한가운데 — 낚시배에 탄 뒤 보이는 넓은 수면."""
    ss = 2
    im = Image.new("RGBA", (W * ss, H * ss), (52, 82, 100, 255))
    d = ImageDraw.Draw(im)
    rnd = random.Random(77)
    # 하늘 / 먼 언덕
    d.rectangle([0, 0, W * ss, 206 * ss], fill=(214, 158, 110, 255))
    d.rectangle([0, 0, W * ss, 84 * ss], fill=(176, 126, 104, 255))
    for x in range(0, W, 96):
        h = rnd.uniform(120, 190) * ss
        d.ellipse([(x - 92) * ss, 206 * ss - h, (x + 92) * ss, 206 * ss + 20 * ss],
                  fill=(74, 84, 70, 255))
    d.rectangle([0, 202 * ss, W * ss, 226 * ss], fill=(96, 106, 74, 255))
    # 수면 띠
    for i in range(58):
        t = i / 58
        y = 226 + t * (H - 226)
        band = Image.new("RGBA", (W * ss, int((H - 226) / 58 * ss) + 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        col = (int(112 - 62 * t), int(146 - 84 * t), int(156 - 96 * t), 40)
        bd.rectangle([0, 0, W * ss, band.size[1]], fill=col)
        im.alpha_composite(band, (0, int(y * ss)))
    # 노을 반사
    refl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(refl)
    for i in range(20):
        y = (232 + i * 22) * ss
        wgt = 1 - i / 20
        dr.ellipse([(640 - 170 * wgt) * ss, y, (640 + 170 * wgt) * ss, y + 12 * ss],
                   fill=(252, 196, 126, int(56 * wgt)))
    refl = refl.filter(ImageFilter.GaussianBlur(12 * ss))
    im.alpha_composite(refl)
    # 잔물결
    for _ in range(220):
        x, y = rnd.uniform(0, W) * ss, rnd.uniform(230, H) * ss
        ln = rnd.uniform(16, 78) * ss
        c = (236, 204, 160, rnd.randint(24, 78)) if rnd.random() < 0.5 else \
            (168, 206, 212, rnd.randint(24, 70))
        d.line([x, y, x + ln, y], fill=c, width=max(1, int(1.6 * ss)))
    return im.resize((W, H), Image.LANCZOS)


def boat():
    """나무 낚싯배 — 가로로 긴 작은 보트."""
    im = Image.new("RGBA", (196, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(8, 34), (188, 34), (166, 72), (30, 72)],
              fill=(132, 90, 56, 255), outline=(72, 46, 28, 255))
    d.polygon([(8, 34), (188, 34), (176, 46), (20, 46)],
              fill=(166, 118, 72, 255), outline=(82, 52, 30, 255))
    d.rectangle([34, 48, 162, 54], fill=(96, 62, 38, 255))
    d.line([(64, 22), (64, 34)], fill=(70, 48, 30, 255), width=5)
    d.line([(132, 22), (132, 34)], fill=(70, 48, 30, 255), width=5)
    d.ellipse([146, 8, 170, 32], fill=(206, 176, 120, 255))
    d.polygon([(158, 12), (186, 26), (158, 30)], fill=(232, 196, 138, 255))
    return im


def fish_jump():
    d = Image.new("RGBA", (76, 64), (0, 0, 0, 0))
    dr = ImageDraw.Draw(d)
    dr.ellipse([12, 14, 62, 54], fill=(122, 182, 194, 255),
               outline=(44, 88, 102, 255), width=3)
    dr.polygon([(58, 34), (76, 12), (72, 52)], fill=(96, 152, 166, 255))
    dr.ellipse([20, 25, 28, 33], fill=(20, 38, 44, 255))
    dr.line([(32, 20), (38, 12), (46, 20)], fill=(60, 112, 126, 255), width=3)
    return d


def fish_gauge_bg():
    """화면 아래쪽 타이밍 낚시 게이지."""
    im = Image.new("RGBA", (340, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 338, 70], 10, fill=(8, 18, 16, 220),
                        outline=(233, 166, 63, 210), width=2)
    text(d, (14, 5), "타이밍 낚시  ·  초록 구간에서 E 떼기", 15, CREAM + (255,))
    d.rounded_rectangle([14, 34, 326, 60], 6, fill=(4, 10, 8, 240))
    return im


def sign_post(label, w=300, accent=AMBER):
    """물가 끝 안내 표지 — 나무 기둥 + 판자 + 아래쪽 화살표."""
    im = Image.new("RGBA", (w, 88), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([w // 2 - 7, 34, w // 2 + 7, 88], 3,
                        fill=(96, 62, 34, 255))
    d.rounded_rectangle([2, 2, w - 3, 52], 8, fill=(52, 38, 26, 245),
                        outline=accent + (255,), width=3)
    text(d, (w / 2, 11), label, 21, CREAM + (255,), anchor="ma")
    d.polygon([(w // 2 - 10, 57), (w // 2 + 10, 57), (w // 2, 76)],
              fill=accent + (255,))
    return im


def pier():
    """호숫가 맵 아래쪽 낚시터 부두."""
    im = Image.new("RGBA", (224, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 14, 221, 68], 6, fill=(112, 78, 44, 255),
                        outline=(64, 42, 24, 255), width=2)
    for x in range(12, 216, 26):
        d.line([(x, 17), (x, 65)], fill=(76, 50, 28, 190), width=2)
    for px in (28, 194):
        d.rounded_rectangle([px, 66, px + 10, 96], 2, fill=(78, 52, 30, 255))
    return im


def exit_gate(label, accent=(122, 190, 118)):
    """진짜 음식을 다 먹으면 열리는 출구 게이트."""
    im = Image.new("RGBA", (150, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 34, 26, 128], 4, fill=(96, 62, 34, 255))
    d.rounded_rectangle([124, 34, 140, 128], 4, fill=(96, 62, 34, 255))
    d.rounded_rectangle([2, 10, 148, 48], 8, fill=(52, 38, 26, 245),
                        outline=accent + (255,), width=3)
    text(d, (75, 18), label, 20, CREAM + (255,), anchor="ma")
    d.polygon([(60, 64), (90, 64), (75, 88)], fill=accent + (225,))
    d.polygon([(60, 90), (90, 90), (75, 114)], fill=accent + (150,))
    return im


def exit_trail():
    """출구까지 이어지는 발자국/화살표 표지."""
    im = Image.new("RGBA", (28, 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([2, 4, 26, 20], fill=(122, 190, 118, 150))
    d.polygon([(10, 7), (20, 12), (10, 17)], fill=(250, 246, 236, 240))
    return im


# ---------------------------------------------------------------- build
def build_all():
    os.makedirs(OUT, exist_ok=True)

    def save(im, name):
        im.save(os.path.join(OUT, name))

    bg_forest().convert("RGB").save(os.path.join(OUT, "bg_forest.png"))
    bg_lake().convert("RGB").save(os.path.join(OUT, "bg_lake.png"))
    bg_festival().convert("RGB").save(os.path.join(OUT, "bg_festival.png"))
    bg_tent().convert("RGB").save(os.path.join(OUT, "bg_tent.png"))
    bg_backstage().convert("RGB").save(os.path.join(OUT, "bg_backstage.png"))
    bg_lake_open().convert("RGB").save(os.path.join(OUT, "bg_lake_open.png"))

    for name, col in (("day", (255, 246, 214)), ("sunset", (255, 190, 120)),
                      ("night", (255, 214, 140))):
        save(cone(col), f"cone_{name}.png")

    save(shadow(), "shadow.png")
    save(glow(160, (233, 166, 63), 70), "glow_food.png")
    save(glow(420, (246, 200, 110), 44), "glow_lamp.png")
    save(dark_vignette(), "vignette_dark.png")
    save(red_vignette(), "vignette_red.png")

    save(hud_bar(), "hud_bar.png")
    save(gauge_label(), "hud_gauge.png")
    save(gauge_bg(), "hud_gauge_bg.png")
    save(slot(True), "slot_empty.png")
    save(slot(False), "slot_full.png")
    save(slot_rotten(), "slot_rotten.png")
    save(controls(), "hud_controls.png")
    save(prompt(), "hud_prompt.png")
    save(prompt_label("수풀에 앉기", 168, "X"), "hud_prompt_sit.png")
    save(prompt_label("일어나기", 132, "X"), "hud_prompt_stand.png")
    save(toast(), "hud_toast.png")
    save(toast_bad(), "hud_toast_bad.png")
    save(hidden_badge(), "hud_hidden.png")
    save(sit_badge(), "hud_sit.png")
    for n in range(16):
        save(counter_plate("남은 음식:", f"{n}개"), f"hud_remain_{n}.png")
    for n in range(4):
        save(counter_plate("진짜 음식:", f"{n}/3", (122, 190, 118)),
             f"hud_real_{n}.png")
    save(real_mark(), "hud_real_mark.png")
    save(chase_banner(), "hud_chase.png")
    save(noise_ring(), "fx_ring.png")
    save(zzz(), "fx_zzz.png")
    save(door_marker(), "fx_door.png")
    save(prompt_label("텐트 안으로", 168), "hud_prompt_door.png")
    save(prompt_label("조리 부스 안으로", 210), "hud_prompt_stall.png")
    save(prompt_label("밖으로 나가기", 176), "hud_prompt_out.png")
    save(alert_mark(), "mark_alert.png")

    # 낚싯배 / 낚시
    save(boat(), "boat.png")
    save(fish_jump(), "fx_fish_jump.png")
    save(fish_gauge_bg(), "hud_fish_bg.png")
    save(prompt_label("낚싯배 타기", 176, "Q"), "hud_prompt_boat.png")
    save(prompt_label("내리기", 132, "Q"), "hud_prompt_leave.png")
    save(prompt_label("낚시하기", 152, "E"), "hud_prompt_fish.png")
    save(prompt_label("지금 떼기!", 160, "E"), "hud_prompt_release.png")
    save(prompt_label("배에서 내리기", 200, "Q"), "hud_prompt_land.png")
    save(prompt_label("부두로 돌아가기", 200, "Q"), "hud_prompt_return.png")
    save(prompt_label("부두로 이동", 200, "↓"), "hud_prompt_to_spot.png")
    save(toast("낚싯배 탑승!"), "hud_toast_boat.png")
    save(toast("물고기 도망!"), "hud_toast_miss.png")
    save(toast("대물 낚시!"), "hud_toast_big.png")
    save(toast("부두 도착!"), "hud_toast_spot.png")
    save(sign_post("호숫가 이동"), "sign_to_lake.png")
    save(sign_post("부두로 이동"), "sign_to_spot.png")
    save(pier(), "prop_pier.png")

    # 걸어서 다음 맵으로 — 출구 게이트와 길 표지
    save(exit_gate("다음 맵"), "fx_exit_next.png")
    save(exit_gate("완료"), "fx_exit_win.png")
    save(exit_trail(), "fx_exit_trail.png")
    save(prompt_label("다음 맵으로", 168, "E"), "hud_prompt_next.png")
    save(prompt_label("게임 완료", 160, "E"), "hud_prompt_win.png")
    save(toast("출구가 열렸다!"), "hud_toast_exit.png")

    names = [("숲속 캠핑장", "한낮  ·  MAP 01", AMBER),
             ("호숫가 캠핑장", "해 질 녘  ·  MAP 02", (233, 141, 79)),
             ("야간 축제 캠핑장", "밤  ·  MAP 03", (238, 200, 120)),
             ("텐트 안", "숲속  ·  자는 사람이 있다", (206, 178, 120)),
             ("텐트 안", "호숫가  ·  자는 사람이 있다", (206, 178, 120)),
             ("호숫가 낚시배", "호수  ·  E 홀드로 낚시", (150, 200, 206)),
             ("무대 뒤 조리 부스", "축제  ·  요리사가 냄비를 젓는다", (238, 200, 120))]
    for i, (nm, sub, accent) in enumerate(names):
        fn = (f"label_map{i}.png" if i < 3 else
              "label_lake.png" if i == 5 else
              "label_backstage.png" if i == 6 else f"label_tent{i - 3}.png")
        save(map_label(nm, sub, accent), fn)

    sets = [("숲속 캠핑장", "한낮  —  햇빛 아래, 사람은 두 명"),
            ("호숫가 캠핑장", "해 질 녘  —  낚시꾼과 산책하는 사람"),
            ("야간 축제 캠핑장", "밤  —  불빛과 인파, 다섯 명")]
    food_set = [["stew", "sausage", "mallow", "apple", "cheese"],
                ["corn", "sandwich", "bread", "egg", "fish"],
                ["chicken", "cake", "soda", "berry", "soup"]]
    tips = ["야외 정상 2개 + 텐트 음식 1개를 모아 다음 캠핑장으로",
            "야외 정상 2개 + Q로 낚싯배를 타고 생선을 낚아야 한다",
            "야외 정상 1개 + 조리 부스의 수프를 모아 다음 캠핑장으로"]
    for i, (nm, tm) in enumerate(sets):
        ims = [Image.open(os.path.join(OUT, f"food_{k}.png")).convert("RGBA")
               for k in food_set[i]]
        save(intro(i, nm, tm, ims, tips[i]), f"intro_{i}.png")

    save(overlay_end("caught"), "over_caught.png")
    save(overlay_end("clear"), "over_clear.png")
    save(map_clear(), "over_mapclear.png")
    print("scenes/hud saved ->", OUT)


def write_sfx():
    """발소리 WAV 2종 (걷기/달리기). 외부 파일 없이 합성한다."""
    import struct
    import wave

    sr = 22050

    def step(heavy):
        dur = 0.12
        n = int(sr * dur)
        rnd = random.Random(21 if heavy else 7)
        lp, out = 0.0, []
        for i in range(n):
            t = i / sr
            env = math.exp(-t * (34 if heavy else 46))
            f = (72 if heavy else 96) - 18 * (t / dur)
            body = math.sin(2 * math.pi * f * t) * env
            nz = rnd.uniform(-1.0, 1.0)
            lp += 0.22 * (nz - lp)
            burst = lp * math.exp(-t * (88 if heavy else 118))
            v = (body * 0.55 + burst * (0.50 if heavy else 0.32))
            v *= 0.60 if heavy else 0.34
            out.append(max(-1.0, min(1.0, v)))
        data = b"".join(struct.pack("<h", int(v * 32767)) for v in out)
        w = wave.open(os.path.join(OUT, "sfx_step_run.wav" if heavy
                                   else "sfx_step_walk.wav"), "wb")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data)
        w.close()

    step(False)
    step(True)
    print("sfx saved ->", OUT)


if __name__ == "__main__":
    A.build_all()
    build_all()
    write_sfx()
