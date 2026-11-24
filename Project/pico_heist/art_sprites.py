# -*- coding: utf-8 -*-
"""피코의 캠핑장 습격 — 스프라이트 생성기.

외부 이미지를 쓰지 않고 PIL 도형만으로 캐릭터/소품/음식 PNG를 만든다.
pico2d 실행 중에는 이 파일이 필요 없다(에셋만 사용). 재생성:
    python -X utf8 make_assets.py
"""
import os
import math
import random

from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")

# ---------------------------------------------------------------- palette
INK = "#16241E"
CREAM = "#FAF6EC"
AMBER = "#E9A63F"
AMBER_D = "#B97C22"
FUR = "#6E4E38"
FUR_D = "#573C2B"
FUR_L = "#8A6448"
MUZZLE = "#CAAB8B"
GREEN = "#2F5D46"
GREEN_D = "#234636"
GREEN_L = "#3E7256"

SKIN = ["#E3B78F", "#C89468", "#8D5B3C", "#F0C9A6"]
HAIR = ["#2A211C", "#4A3527", "#6E5A45", "#141110", "#7A5B3A"]
JACKET = ["#C98C3E", "#3E6E6A", "#B4553A", "#6E7A45", "#3B4A63", "#7A4A63"]
PANTS = ["#2C3B45", "#3A3F36", "#4A3B32", "#2A3440"]


def _size(im):
    return im.size


def make(w, h, ss=3):
    """슈퍼샘플링용 빈 이미지와 스케일 값을 돌려준다."""
    return Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0)), ss


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


class Pen:
    """좌표를 (0..w, 0..h) 기준으로 쓰고 내부에서 ss배로 확대해 그리는 도우미."""

    def __init__(self, im, ss):
        self.im = im
        self.d = ImageDraw.Draw(im)
        self.ss = ss

    def _p(self, box):
        s = self.ss
        return [box[0] * s, box[1] * s, box[2] * s, box[3] * s]

    def ell(self, box, fill, outline=None, width=0):
        self.d.ellipse(self._p(box), fill=fill, outline=outline,
                       width=max(1, int(width * self.ss)) if (outline and width) else 0)

    def rr(self, box, r, fill, outline=None, width=0):
        self.d.rounded_rectangle(self._p(box), radius=r * self.ss, fill=fill,
                                 outline=outline,
                                 width=max(1, int(width * self.ss)) if (outline and width) else 0)

    def rect(self, box, fill, outline=None, width=0):
        self.d.rectangle(self._p(box), fill=fill, outline=outline,
                         width=max(1, int(width * self.ss)) if (outline and width) else 0)

    def poly(self, pts, fill):
        self.d.polygon([(x * self.ss, y * self.ss) for (x, y) in pts], fill=fill)

    def pline(self, pts, fill, width=1, joint="curve"):
        self.d.line([(x * self.ss, y * self.ss) for (x, y) in pts], fill=fill,
                    width=max(1, int(width * self.ss)), joint=joint)

    def pie(self, box, a0, a1, fill):
        self.d.pieslice(self._p(box), a0, a1, fill=fill)

    def arc(self, box, a0, a1, fill, width=1):
        self.d.arc(self._p(box), a0, a1, fill=fill, width=max(1, int(width * self.ss)))

    def chord(self, box, a0, a1, fill):
        self.d.chord(self._p(box), a0, a1, fill=fill)


# ---------------------------------------------------------------- pico
def pico(direction="down", frame=0):
    """피코: 갈색 털 + 호박색 비니 + 초록 재킷. 64x80."""
    w, h, ss = 64, 80, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    bob = -1 if frame else 0
    # ---- legs
    lx = 19 - (2 if frame else 0)
    rx = 35 + (2 if frame else 0)
    for (ax, shoe_dx) in ((lx, -2 if frame else 0), (rx, 2 if frame else 0)):
        p.rr((ax, 55 + bob, ax + 10, 70 + bob), 4, FUR_D)
        p.ell((ax - 2 + shoe_dx, 67 + bob, ax + 13 + shoe_dx, 76 + bob), INK)
    # ---- body
    p.rr((17, 36 + bob, 47, 59 + bob), 11, GREEN)
    p.rr((21, 40 + bob, 43, 58 + bob), 9, GREEN_L)
    p.pline([(32, 40 + bob), (32, 57 + bob)], GREEN_D, 1.6)
    # ---- arms + hands
    p.ell((10, 40 + bob, 24, 55 + bob), GREEN)
    p.ell((40, 40 + bob, 54, 55 + bob), GREEN)
    p.ell((11, 49 + bob, 21, 57 + bob), FUR)
    p.ell((43, 49 + bob, 53, 57 + bob), FUR)
    # ---- ears
    p.ell((9, 20, 25, 38), FUR)
    p.ell((39, 20, 55, 38), FUR)
    p.ell((12, 24, 21, 33), FUR_D)
    p.ell((43, 24, 52, 33), FUR_D)
    # ---- head
    p.ell((14, 10, 50, 46), FUR)
    if direction == "up":
        # 뒤통수 + 배낭
        p.rr((18, 38 + bob, 46, 58 + bob), 7, "#3E5B44", "#2A4030", 1.2)
        p.rr((24, 41 + bob, 40, 50 + bob), 3, "#54795B")
        p.rr((28, 48 + bob, 36, 54 + bob), 2, AMBER_D)
        p.pline([(20, 40 + bob), (20, 52 + bob)], "#2A4030", 1.4)
        p.pline([(44, 40 + bob), (44, 52 + bob)], "#2A4030", 1.4)
    elif direction in ("left", "right"):
        # 옆모습
        if direction == "right":
            im = ImageOps.mirror(im)
            p = Pen(im, ss)
        p.ell((8, 28, 30, 44), MUZZLE)          # 주둥이
        p.ell((14, 31, 22, 39), INK)            # 코
        p.pie((15, 10, 49, 44), 90, 270, MUZZLE)  # 얼굴 하단 밝게
        p.ell((24, 22, 31, 30), INK)            # 눈
        p.ell((25.5, 23.5, 28, 26), CREAM)      # 눈 하이라이트
        p.pline([(16, 38), (21, 40)], FUR_D, 1.2)
        p.rr((30, 36 + bob, 50, 58 + bob), 7, "#3E5B44", "#2A4030", 1.0)  # 배낭
        p.ell((34, 24, 48, 38), FUR)            # 반대쪽 귀
        p.ell((37, 27, 45, 35), FUR_D)
    else:  # down
        p.ell((22, 30, 42, 44), MUZZLE)
        p.ell((28, 31, 36, 37), INK)
        p.pline([(32, 36), (32, 39)], INK, 1.0)
        p.arc((25, 36, 39, 44), 20, 160, INK, 1.0)
        p.ell((22, 22, 27, 28), INK)
        p.ell((37, 22, 42, 28), INK)
        p.ell((23.5, 23, 25.5, 25.5), CREAM)
        p.ell((38.5, 23, 40.5, 25.5), CREAM)
        p.pline([(20, 20), (25, 19)], FUR_D, 1.0)
        p.pline([(39, 19), (44, 20)], FUR_D, 1.0)
    # ---- beanie
    p.pie((14, 4, 50, 40), 180, 360, AMBER)
    p.rr((13, 25, 51, 31), 3.2, AMBER_D)
    p.ell((28, 1, 36, 9), CREAM)
    p.pie((18, 7, 30, 22), 200, 320, "#F2BC63")
    return down(im, w, h)


def pico_peek():
    """수풀에 앉았을 때 잎 위로 빼꼼 내미는 머리 — pico 상단 34px 만 남긴다."""
    im = pico("down", 0)
    return im.crop((0, 0, im.width, 34))


# ---------------------------------------------------------------- camper
def camper(variant=0, direction="down", frame=0, sitting=False):
    """캠핑객: 64x82. variant 로 옷/머리 색을 바꾼다."""
    w, h, ss = 64, 82, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    skin = SKIN[variant % len(SKIN)]
    hair = HAIR[variant % len(HAIR)]
    jack = JACKET[variant % len(JACKET)]
    pant = PANTS[variant % len(PANTS)]
    bob = -1 if frame else 0

    if sitting:
        # 낚시꾼: 다리를 앞으로 뻗은 자세
        p.rr((24, 56, 48, 66), 4, pant)
        p.ell((42, 60, 58, 70), INK)
        p.ell((42, 58, 56, 68), INK)
        p.rr((18, 40, 44, 64), 10, jack)
        p.ell((12, 47, 22, 57), skin)
        p.ell((40, 47, 50, 57), skin)
        p.ell((20, 14, 46, 42), skin)
        p.pie((20, 10, 46, 36), 180, 360, hair)
        p.ell((19, 26, 47, 40), hair, None, 0)
        p.pie((22, 25, 44, 41), 0, 180, skin)
        p.ell((27, 28, 31, 32), INK)
        p.ell((36, 28, 40, 32), INK)
        p.ell((24, 8, 42, 22), "#B4553A")  # 모자
        p.rr((22, 19, 46, 23), 2, "#8E3F2A")
        return down(im, w, h)

    # legs
    p.rr((22, 56 + bob, 31, 71 + bob), 4, pant)
    p.rr((34, 56 + bob, 43, 71 + bob), 4, pant)
    p.ell((20, 68 + bob, 33, 77 + bob), "#20262A")
    p.ell((32, 68 + bob, 45, 77 + bob), "#20262A")
    # torso
    p.rr((17, 34 + bob, 47, 60 + bob), 9, jack)
    p.rr((29, 34 + bob, 35, 44 + bob), 2, "#EDE5D2")   # 셔츠
    p.pline([(32, 44 + bob), (32, 58 + bob)], "#00000033", 1.0)
    # arms
    p.rr((10, 37 + bob, 19, 57 + bob), 4, jack)
    p.rr((45, 37 + bob, 54, 57 + bob), 4, jack)
    p.ell((11, 53 + bob, 20, 60 + bob), skin)
    p.ell((44, 53 + bob, 53, 60 + bob), skin)
    # head
    p.ell((15, 9, 49, 45), skin)
    p.ell((12, 20, 19, 32), skin)   # 귀
    p.ell((45, 20, 52, 32), skin)
    if direction == "up":
        p.pie((14, 8, 50, 40), 180, 360, hair)
        p.rect((14, 10, 50, 26), hair)
        p.ell((15, 8, 49, 34), hair)
    elif direction in ("left", "right"):
        if direction == "right":
            im = ImageOps.mirror(im)
            p = Pen(im, ss)
        p.pie((14, 8, 50, 42), 90, 270, hair)
        p.ell((14, 10, 48, 30), hair)
        p.ell((24, 24, 30, 31), INK)
        p.ell((25, 25, 27, 27.5), CREAM)
        p.ell((16, 28, 22, 32), "#D9A882")  # 코
        p.pline([(22, 36), (28, 36)], "#8E5A48", 1.2)
    else:
        p.pie((14, 6, 50, 38), 180, 360, hair)
        p.ell((13, 8, 51, 26), hair)
        p.ell((23, 24, 28, 30), INK)
        p.ell((36, 24, 41, 30), INK)
        p.ell((24.5, 25, 26.5, 27.5), CREAM)
        p.ell((37.5, 25, 39.5, 27.5), CREAM)
        p.arc((26, 30, 38, 40), 20, 160, "#8E5A48", 1.1)
    # 머리 위 모자
    if variant % 2 == 0:
        p.pie((15, 0, 49, 26), 180, 360, "#4C6B58")
        p.rr((13, 18, 51, 23), 2, "#3A5346")
        p.ell((28, 13, 36, 20), "#4C6B58")
    return down(im, w, h)


# ---------------------------------------------------------------- props
def tree(kind="round"):
    w, h, ss = 150, 180, 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    # trunk
    p.poly([(66, 100), (84, 100), (88, 176), (62, 176)], "#4A3524")
    p.poly([(70, 100), (78, 100), (80, 172), (66, 172)], "#5E452E")
    p.pline([(74, 110), (72, 160)], "#3A2A1C", 1.4)
    if kind == "round":
        blobs = [(52, 62, 46), (98, 58, 44), (75, 30, 50), (30, 46, 34), (120, 44, 32)]
        for (cx, cy, r) in blobs:
            p.ell((cx - r, cy - r, cx + r, cy + r), "#3F6A46")
        for (cx, cy, r) in [(60, 44, 36), (96, 46, 32), (76, 26, 36)]:
            p.ell((cx - r, cy - r, cx + r, cy + r), "#4C7C50")
        for (cx, cy, r) in [(58, 36, 24), (88, 34, 22)]:
            p.ell((cx - r, cy - r, cx + r, cy + r), "#5D8F59")
        for (cx, cy) in [(48, 30), (72, 22), (94, 32), (62, 52), (104, 52)]:
            p.ell((cx - 7, cy - 6, cx + 7, cy + 8), "#6FA066")
    else:  # pine
        for (cy, half) in [(92, 62), (66, 50), (42, 36), (20, 22)]:
            p.poly([(75, cy - 34), (75 - half, cy), (75 + half, cy)], "#2F5A40")
            p.poly([(75, cy - 34), (75 - half * 0.55, cy), (75, cy - 4)], "#3A6A49")
        p.poly([(75, 96), (75 - 52, 118), (75 + 52, 118)], "#2A5138")
    return down(im, w, h)


def bush():
    w, h, ss = 90, 56, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    for (cx, cy, r) in [(30, 34, 18), (52, 30, 20), (70, 36, 15)]:
        p.ell((cx - r, cy - r, cx + r, cy + r), "#3C6644")
    p.ell((36, 20, 62, 40), "#4B7A4F")
    p.ell((26, 26, 46, 42), "#4B7A4F")
    for (cx, cy) in [(36, 24), (56, 20), (68, 28)]:
        p.ell((cx - 3, cy - 2, cx + 3, cy + 3), "#63955F")
    return down(im, w, h)


def rock():
    w, h, ss = 80, 56, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.poly([(10, 50), (20, 24), (40, 14), (62, 22), (72, 48), (40, 54)], "#7C8378")
    p.poly([(20, 30), (40, 18), (56, 24), (44, 32), (26, 38)], "#9AA095")
    p.poly([(38, 8), (52, 16), (40, 22)], "#8B9287")
    return down(im, w, h)


def tent(color="#D9A048", dark="#A8701F", cloth="#EFE6CF"):
    w, h, ss = 176, 132, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    # 본체
    p.poly([(86, 12), (10, 112), (162, 112)], color)
    p.poly([(86, 12), (86, 112), (10, 112)], dark)
    p.poly([(86, 12), (162, 112), (140, 112), (86, 40)], cloth)
    # 문
    p.poly([(86, 44), (62, 112), (110, 112)], "#2A3326")
    p.poly([(86, 44), (86, 112), (110, 112)], "#1E261B")
    p.poly([(66, 70), (86, 52), (86, 70)], "#3A4533")
    # 이음선
    p.pline([(86, 14), (150, 108)], "#8E5C16", 1.2)
    p.pline([(86, 14), (22, 108)], "#7C4E12", 1.2)
    p.line if False else None
    return down(im, w, h)


def campfire(frame=0):
    w, h, ss = 84, 76, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.ell((8, 48, 76, 72), "#4A3B2C")
    p.rr((10, 56, 74, 66), 5, "#5E4A35")
    p.rr((18, 50, 66, 60), 4, "#6E5840")
    p.pline([(20, 58), (64, 58)], "#3E2F22", 2)
    fh = 6 if frame else 0
    p.poly([(42, 56), (26, 40 + fh), (36, 24 - fh), (44, 40), (50, 20 + fh),
            (58, 40 - fh), (48, 56)], "#DC5330")
    p.poly([(42, 54), (33, 42 + fh), (40, 32 - fh), (45, 44), (50, 30 + fh),
            (55, 44 + fh), (47, 54)], "#F09A3E")
    p.poly([(43, 52), (38, 44 + fh), (43, 38), (47, 46), (50, 40 + fh)], "#FBE3A6")
    return down(im, w, h)


def table():
    w, h, ss = 120, 84, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    for x in (18, 92):
        p.rr((x, 30, x + 10, 78), 2, "#6B4E32")
    p.rr((8, 24, 112, 40), 4, "#8A6743")
    p.rr((12, 28, 108, 36), 3, "#9C7850")
    # 위에 놓인 것들
    p.ell((30, 14, 52, 28), "#E9E2D2")
    p.ell((34, 16, 48, 25), "#C0563C")
    p.rr((64, 16, 92, 26), 3, "#D9C7A4")
    p.rr((70, 12, 86, 18), 2, "#B4553A")
    p.ell((96, 18, 106, 28), "#7FA37E")
    return down(im, w, h)


def cooler():
    w, h, ss = 60, 54, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((8, 14, 52, 46), 5, "#D9D3C4")
    p.rr((8, 14, 52, 24), 4, "#E8E3D6")
    p.rr((24, 6, 36, 16), 2, "#8A8578")
    p.pline([(12, 30), (48, 30)], "#B6AE9C", 1.6)
    p.rr((8, 40, 52, 46), 3, "#B9B2A0")
    return down(im, w, h)


def log():
    w, h, ss = 100, 48, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((8, 22, 92, 42), 9, "#6B4E32")
    p.rr((8, 22, 92, 32), 9, "#7E5D3C")
    p.ell((78, 18, 98, 44), "#8A6743")
    p.ell((82, 22, 94, 40), "#A8814F")
    p.ell((85, 26, 91, 36), "#8A6743")
    p.pline([(20, 30), (70, 30)], "#5A4029", 1.2)
    return down(im, w, h)


def booth(awning="#C0563C"):
    w, h, ss = 220, 172, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    # 기둥
    for x in (18, 190):
        p.rr((x, 60, x + 12, 160), 2, "#6B4E32")
    # 카운터
    p.rr((10, 104, 210, 158), 5, "#8A6743")
    p.rr((16, 110, 204, 148), 4, "#A8814F")
    p.rr((10, 150, 210, 162), 3, "#6B4E32")
    # 어닝
    p.poly([(6, 58), (214, 58), (198, 22), (22, 22)], awning)
    for i in range(5):
        x0 = 22 + i * 35.2
        if i % 2 == 0:
            p.poly([(x0, 58), (x0 + 35.2, 58), (x0 + 31.5, 22), (x0 + 3.5, 22)], "#F2E7CD")
    p.rr((6, 56, 214, 64), 3, "#8E3F2A")
    # 진열대
    p.rr((30, 90, 190, 104), 3, "#7E5D3C")
    p.ell((40, 78, 62, 94), "#E9D9B4")
    p.ell((42, 80, 60, 90), "#D9A048")
    p.rr((72, 80, 100, 94), 3, "#C0563C")
    p.ell((112, 78, 132, 94), "#7FA37E")
    p.rr((144, 80, 172, 94), 2, "#E9E2D2")
    # 간판
    p.rr((58, 66, 162, 92), 4, "#2A3326")
    p.ell((72, 72, 84, 84), "#E9A63F")
    p.rr((90, 76, 150, 82), 2, "#C7C0AC")
    return down(im, w, h)


def lantern():
    w, h, ss = 56, 176, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((24, 40, 32, 168), 3, "#4A4034")
    p.rr((20, 160, 36, 172), 3, "#3A3228")
    p.rr((18, 30, 38, 44), 3, "#3A3228")
    p.rr((14, 10, 42, 34), 4, "#2A3326")
    p.rr((18, 14, 38, 30), 3, "#F6D27A")
    p.poly([(14, 12), (42, 12), (36, 4), (20, 4)], "#2A3326")
    p.ell((27, 20, 29, 24), "#FFF3CF")
    return down(im, w, h)


def crate():
    w, h, ss = 60, 56, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((8, 14, 52, 50), 3, "#8A6743")
    p.rect((12, 18, 48, 46), "#9C7850")
    p.pline([(12, 18), (48, 46)], "#6B4E32", 2)
    p.pline([(48, 18), (12, 46)], "#6B4E32", 2)
    p.rr((8, 14, 52, 19), 2, "#6B4E32")
    p.rr((8, 45, 52, 50), 2, "#6B4E32")
    return down(im, w, h)


def snack_basket(open_=False):
    """작은 캔버스 간식 꾸러미 — 나무 상자보다 작고 부드러운 캠핑 짐."""
    w, h, ss = 72, 56, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    if open_:
        # 뒤로 젖혀진 뚜껑 + 비어 있는 어두운 내부
        p.rr((14, 6, 58, 20), 4, "#D9BC88")
        p.rr((14, 6, 58, 12), 3, "#C7A570")
        p.ell((14, 18, 58, 32), "#4A3626")
        p.ell((19, 21, 53, 30), "#5C4530")
    else:
        # 손잡이와 덮개가 보이는 닫힌 바구니
        p.arc((20, 6, 52, 32), 180, 360, "#6B4E32", 3)
        p.rr((12, 18, 60, 30), 5, "#DCC08C")
        p.rr((12, 18, 60, 24), 4, "#EAD3A6")
    # 캔버스 몸체
    p.rr((10, 24, 62, 50), 6, "#C9A36A")
    p.rr((10, 24, 62, 32), 5, "#D7B57E")
    for x in (23, 36, 49):
        p.pline([(x, 32), (x, 49)], "#A9814C", 1)
    # 가죽 끈
    p.rr((16, 22, 22, 50), 2, "#6B4E32")
    p.rr((50, 22, 56, 50), 2, "#6B4E32")
    # 호박색 간식 라벨
    p.rr((28, 34, 44, 46), 3, "#E9A63F")
    p.rr((31, 37, 41, 43), 1, "#6B4E32")
    if not open_:
        p.rr((32, 27, 40, 34), 2, "#B97C22")
    return down(im, w, h)


def speaker():
    w, h, ss = 56, 96, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((9, 6, 47, 88), 4, "#2A2E2C")
    p.ell((16, 14, 40, 40), "#3C4340")
    p.ell((22, 20, 34, 34), "#202423")
    p.ell((16, 48, 40, 74), "#3C4340")
    p.ell((23, 55, 33, 65), "#202423")
    p.rr((20, 78, 36, 82), 1, "#5A625E")
    return down(im, w, h)


def bench():
    w, h, ss = 120, 56, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((8, 18, 112, 26), 3, "#8A6743")
    p.rr((8, 28, 112, 36), 3, "#9C7850")
    for x in (18, 94):
        p.rr((x, 30, x + 8, 52), 2, "#5E4A35")
    return down(im, w, h)


def grill():
    w, h, ss = 76, 66, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    for x in (14, 54):
        p.rr((x, 34, x + 8, 62), 2, "#4A4034")
    p.rr((6, 24, 70, 38), 4, "#3A3F3C")
    p.ell((10, 20, 66, 34), "#2A2E2C")
    p.ell((24, 22, 42, 30), "#C0563C")
    p.ell((42, 22, 56, 30), "#8A4A2E")
    p.rr((6, 36, 70, 42), 3, "#2A2E2C")
    return down(im, w, h)


def sleepbag():
    """텐트 안 침낭 (가로로 눕힌 형태)."""
    w, h, ss = 132, 68, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    p.rr((4, 14, 128, 60), 16, "#4E5E3E")
    p.rr((9, 19, 123, 55), 13, "#6E8052")
    p.rr((9, 19, 123, 34), 13, "#7D9060")
    # 이불 접힌 선
    for x in (56, 84, 108):
        p.pline([(x, 22), (x, 52)], "#5C6C44", 1.4)
    # 베개
    p.rr((10, 21, 40, 53), 10, "#E8E1CB")
    p.rr((13, 24, 37, 50), 8, "#F1EBD8")
    p.pline([(14, 37), (36, 37)], "#D5CCB2", 1.2)
    # 지퍼
    p.pline([(46, 57), (124, 57)], "#3E4A32", 1.6)
    p.ell((60, 54, 68, 62), "#B9B29C")
    return down(im, w, h)


def sleeper():
    """침낭에서 자는 사람 (머리는 왼쪽)."""
    w, h, ss = 140, 72, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    skin = SKIN[2]
    hair = HAIR[1]
    # 담요
    p.rr((30, 12, 136, 58), 14, "#B4553A")
    p.rr((30, 12, 136, 28), 12, "#C4653F")
    p.rr((44, 8, 78, 34), 12, "#C4653F")     # 어깨 솟은 부분
    for x in (74, 100, 122):
        p.pline([(x, 14), (x, 56)], "#9C452E", 1.4)
    p.pline([(34, 40), (132, 40)], "#9C452E", 1.0)
    # 베개에 기댄 머리
    p.ell((8, 20, 46, 56), skin)
    p.ell((14, 44, 34, 56), "#D9A882")
    p.pie((8, 16, 46, 44), 180, 360, hair)
    p.ell((7, 18, 47, 34), hair)
    # 감은 눈 + 입
    p.pline([(17, 40), (24, 40)], "#6B4A3C", 1.6)
    p.pline([(28, 40), (35, 40)], "#6B4A3C", 1.6)
    p.pline([(24, 47), (30, 47)], "#8E5A48", 1.3)
    # 담요 밖으로 나온 팔
    p.rr((44, 50, 68, 58), 4, skin)
    p.ell((64, 50, 74, 58), skin)
    return down(im, w, h)


# ---------------------------------------------------------------- foods
FOOD_KINDS = ["stew", "sausage", "mallow", "fish", "sandwich", "corn",
              "chicken", "cake", "soda", "apple", "cheese", "bread",
              "egg", "berry", "soup"]


def food(kind):
    w, h, ss = 64, 64, 3
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    p = Pen(im, ss)
    # 접시
    p.ell((6, 30, 58, 56), "#D8CBB2")
    p.ell((10, 34, 54, 52), "#EFE6D2")
    p.ell((12, 36, 52, 48), "#E4DAC3")
    if kind == "stew":
        p.ell((14, 26, 50, 50), "#4A3B32")
        p.ell((16, 28, 48, 46), "#8E3F2A")
        p.ell((20, 30, 44, 42), "#B4553A")
        for (x, y) in [(24, 34), (32, 31), (39, 36)]:
            p.ell((x - 3, y - 2, x + 3, y + 3), "#D9A048")
        p.arc((18, 32, 46, 46), 200, 340, "#E9A63F", 1.4)
        p.pline([(24, 24), (22, 16)], "#EFE6D2", 1.4)
        p.pline([(36, 22), (38, 14)], "#EFE6D2", 1.4)
    elif kind == "sausage":
        p.pline([(12, 44), (52, 20)], "#8A6743", 2.4)
        for (x, y, a) in [(22, 38, 0), (33, 31, 0), (44, 25, 0)]:
            p.ell((x - 9, y - 6, x + 9, y + 6), "#A8552F")
            p.ell((x - 7, y - 4, x + 5, y + 3), "#C4653A")
            p.ell((x - 4, y - 3, x + 2, y), "#D98A5A")
    elif kind == "mallow":
        p.pline([(14, 46), (50, 18)], "#8A6743", 2.2)
        for (x, y) in [(28, 36), (40, 26)]:
            p.rr((x - 8, y - 8, x + 8, y + 8), 5, "#F2E7CD")
            p.rr((x - 7, y - 7, x + 2, y + 2), 4, "#FFF9EA")
            p.ell((x - 6, y - 2, x + 6, y + 6), "#C99A5E")
    elif kind == "fish":
        p.ell((16, 26, 52, 48), "#B9B0A0")
        p.ell((20, 28, 48, 44), "#D9CFBC")
        p.poly([(18, 36), (6, 26), (8, 44)], "#A89C88")
        p.poly([(22, 36), (48, 30), (50, 40), (24, 42)], "#C08A62")
        p.poly([(26, 38), (46, 33), (47, 39), (28, 41)], "#D9A882")
        p.ell((38, 34, 42, 38), "#4A3527")
        p.pline([(30, 38), (44, 36)], "#8A6743", 1.0)
        p.ell((28, 42, 34, 46), "#7FA37E")
    elif kind == "sandwich":
        p.poly([(10, 46), (54, 46), (32, 20)], "#E9C87E")
        p.poly([(14, 43), (50, 43), (32, 25)], "#F2DEA8")
        p.poly([(20, 41), (44, 41), (32, 30)], "#7FA37E")
        p.poly([(24, 36), (40, 36), (32, 28)], "#C0563C")
        p.poly([(26, 32), (38, 32), (32, 27)], "#E9E2D2")
    elif kind == "corn":
        p.ell((20, 20, 44, 50), "#E9C24A")
        for i in range(4):
            for j in range(3):
                p.ell((23 + i * 5, 24 + j * 7, 27 + i * 5, 28 + j * 7), "#F2DB7E")
        p.poly([(22, 46), (14, 30), (26, 30)], "#6E9A5E")
        p.poly([(42, 46), (50, 30), (38, 30)], "#7FA86A")
    elif kind == "chicken":
        p.ell((18, 22, 46, 44), "#B4703A")
        p.ell((22, 25, 43, 42), "#C9834A")
        p.ell((26, 27, 39, 37), "#D99A60")
        p.rr((38, 36, 52, 46), 4, "#E3D6BE")
        p.ell((40, 38, 50, 45), "#EFE6D2")
        p.ell((28, 22, 34, 28), "#E9D9B4")
    elif kind == "cake":
        p.poly([(14, 46), (50, 46), (50, 26), (14, 30)], "#E4C7A6")
        p.poly([(14, 30), (50, 26), (50, 20), (14, 24)], "#F2E7CD")
        p.poly([(14, 46), (50, 46), (50, 42), (14, 42)], "#C98C5A")
        p.ell((28, 14, 38, 24), "#C0563C")
        p.pline([(33, 14), (33, 10)], "#6E9A5E", 1.2)
    elif kind == "apple":
        p.ell((18, 22, 48, 52), "#C0563C")
        p.ell((22, 24, 44, 48), "#D9744E")
        p.ell((24, 26, 34, 40), "#E99A6A")
        p.pline([(33, 22), (35, 14)], "#6B4A3C", 2.0)
        p.ell((35, 12, 46, 19), "#6E9A5E")
    elif kind == "cheese":
        p.poly([(14, 46), (50, 46), (48, 20), (18, 26)], "#E9C24A")
        p.poly([(16, 44), (46, 44), (45, 24), (20, 29)], "#F2DB7E")
        for (x, y) in ((26, 36), (38, 34), (32, 42)):
            p.ell((x - 3, y - 3, x + 3, y + 3), "#C99A3E")
    elif kind == "bread":
        p.rr((12, 24, 52, 50), 10, "#B4703A")
        p.rr((16, 26, 48, 46), 8, "#D9A05A")
        p.pline([(20, 31), (44, 31)], "#E9C98A", 1.6)
        p.pline([(20, 42), (44, 42)], "#E9C98A", 1.6)
    elif kind == "egg":
        p.ell((14, 20, 50, 52), "#EFE6D2")
        p.ell((20, 26, 44, 48), "#FFF9EA")
        p.ell((26, 30, 40, 44), "#E9C24A")
        p.ell((29, 33, 35, 39), "#F2DB7E")
    elif kind == "berry":
        for (x, y) in ((22, 36), (36, 34), (29, 44)):
            p.ell((x - 8, y - 7, x + 8, y + 7), "#7E4E7A")
            p.ell((x - 5, y - 5, x + 1, y + 1), "#A8709A")
        p.pline([(30, 28), (34, 16)], "#6E9A5E", 2.0)
        p.ell((34, 13, 46, 20), "#7FA86A")
    elif kind == "soup":
        p.ell((12, 28, 52, 52), "#C7C0AC")
        p.ell((16, 30, 48, 48), "#8E3F2A")
        p.ell((20, 32, 44, 44), "#B4553A")
        for (x, y) in ((26, 36), (36, 34), (32, 40)):
            p.ell((x - 2, y - 2, x + 2, y + 2), "#E9C24A")
        p.pline([(44, 28), (52, 16)], "#C7C0AC", 2.2)
    else:  # soda
        p.poly([(22, 16), (42, 16), (38, 52), (26, 52)], "#E9E2D2")
        p.poly([(24, 28), (40, 28), (37, 50), (27, 50)], "#C0563C")
        p.rr((20, 12, 44, 18), 2, "#F2E7CD")
        p.pline([(36, 12), (44, 4)], "#C7C0AC", 2.0)
        p.ell((31, 26, 37, 32), "#F2E7CD")
    return down(im, w, h)


# ---------------------------------------------------------------- save all
def build_all():
    os.makedirs(OUT, exist_ok=True)
    n = 0

    def save(im, name):
        nonlocal n
        im.save(os.path.join(OUT, name))
        n += 1

    for d in ("down", "up", "left", "right"):
        for f in (0, 1):
            save(pico(d, f), f"pico_{d}_{f}.png")
    save(pico_peek(), "pico_peek.png")

    for v in range(4):
        for d in ("down", "up", "left", "right"):
            save(camper(v, d), f"camper{v}_{d}.png")
    save(camper(1, "down", sitting=True), "camper_sit.png")

    save(tree("round"), "prop_tree.png")
    save(tree("pine"), "prop_pine.png")
    save(bush(), "prop_bush.png")
    save(rock(), "prop_rock.png")
    save(tent(), "prop_tent.png")
    save(tent("#3E6E6A", "#2A4E4B", "#DDE8DC"), "prop_tent_teal.png")
    save(campfire(0), "prop_fire_0.png")
    save(campfire(1), "prop_fire_1.png")
    save(table(), "prop_table.png")
    save(cooler(), "prop_cooler.png")
    save(log(), "prop_log.png")
    save(booth(), "prop_booth.png")
    save(booth("#3E6E6A"), "prop_booth_teal.png")
    save(booth("#B97C22"), "prop_booth_amber.png")
    save(lantern(), "prop_lantern.png")
    save(crate(), "prop_crate.png")
    save(snack_basket(False), "prop_snack_basket.png")
    save(snack_basket(True), "prop_snack_basket_open.png")
    save(speaker(), "prop_speaker.png")
    save(bench(), "prop_bench.png")
    save(grill(), "prop_grill.png")
    save(sleepbag(), "prop_sleepbag.png")
    save(sleeper(), "prop_sleeper.png")

    for k in FOOD_KINDS:
        save(food(k), f"food_{k}.png")

    print(f"sprites: {n} files -> {OUT}")


if __name__ == "__main__":
    build_all()
