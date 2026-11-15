# -*- coding: utf-8 -*-
"""피코의 캠핑장 습격 — 게임 로직.

main.py 가 pico2d 입력을 hold/press 로 바꿔 Game.update() 에 넘긴다.
헤드리스 테스트/스크린샷 도구도 같은 Game 객체를 직접 돌릴 수 있다.
"""
import math
import os

from pico2d import clear_canvas, draw_rectangle, load_image

from maps import MAPS

W, H = 1280, 720

# 감지 튜닝 값 (기획서의 예시 값과 같은 계열)
NEAR = 150.0            # 이 안쪽은 무조건 들킨다
FAR = 320.0             # 시야 + 엄폐물 판정이 적용되는 최대 거리
HALF_FOV = math.radians(55)
RISE_NEAR = 38.0        # %/s
RISE_FAR = 14.0
FALL = 26.0
PICKUP_NOISE = 6.0

FOOD_ORDER = [kind for m in MAPS for (kind, _, _) in m["foods"]]

PROP_SPECS = {
    # name: (solid w,h / cover w,h or None / pad / shadow w)
    "prop_tree":       dict(solid=(34, 24), cover=(104, 132), pad=2, shadow=110),
    "prop_pine":       dict(solid=(30, 22), cover=(96, 122), pad=2, shadow=96),
    "prop_bush":       dict(solid=(0, 0), cover=(92, 74), pad=2, shadow=84,
                            hide=True, sprite=(90, 56)),
    "prop_rock":       dict(solid=(52, 26), cover=None, pad=2, shadow=66),
    "prop_tent":       dict(solid=(150, 64), cover=(168, 120), pad=8, shadow=150),
    "prop_tent_teal":  dict(solid=(150, 64), cover=(168, 120), pad=8, shadow=150),
    "prop_fire":       dict(solid=(54, 26), cover=None, pad=2, shadow=62),
    "prop_table":      dict(solid=(100, 30), cover=(104, 42), pad=2, shadow=104),
    "prop_cooler":     dict(solid=(44, 24), cover=None, pad=2, shadow=54),
    "prop_log":        dict(solid=(88, 22), cover=None, pad=2, shadow=92),
    "prop_booth":      dict(solid=(200, 58), cover=(212, 156), pad=6, shadow=196),
    "prop_booth_teal": dict(solid=(200, 58), cover=(212, 156), pad=6, shadow=196),
    "prop_booth_amber": dict(solid=(200, 58), cover=(212, 156), pad=6, shadow=196),
    "prop_lantern":    dict(solid=(18, 12), cover=None, pad=2, shadow=0, glow=132),
    "prop_crate":      dict(solid=(46, 26), cover=None, pad=2, shadow=52),
    "prop_speaker":    dict(solid=(40, 18), cover=None, pad=2, shadow=48),
    "prop_bench":      dict(solid=(104, 20), cover=None, pad=2, shadow=104),
    "prop_grill":      dict(solid=(60, 22), cover=None, pad=2, shadow=64),
}


# ---------------------------------------------------------------- geometry
def circle_rect(cx, cy, r, rect):
    x0, y0, x1, y1 = rect
    nx = max(x0, min(cx, x1))
    ny = max(y0, min(cy, y1))
    return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r


def seg_hits_rect(x1, y1, x2, y2, rect):
    """선분이 사각형과 교차하면 True (Liang-Barsky)."""
    xmin, ymin, xmax, ymax = rect
    dx, dy = x2 - x1, y2 - y1
    p = (-dx, dx, -dy, dy)
    q = (x1 - xmin, xmax - x1, y1 - ymin, ymax - y1)
    t0, t1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False
        else:
            t = qi / pi
            if pi < 0:
                if t > t1:
                    return False
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return False
                if t < t1:
                    t1 = t
    return True


def rect_at(x, y, w, h):
    """발밑 중앙 (x,y) 기준 사각형."""
    return (x - w / 2, y - h, x + w / 2, y)


def in_rect(x, y, rect):
    x0, y0, x1, y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1


# ---------------------------------------------------------------- entities
class Player:
    RADIUS = 15

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.dir = "down"
        self.frame = 0
        self.anim = 0.0
        self.moving = False
        self.speed = 205.0

    def update(self, dt, hold, solids, no_go):
        dx = (1 if "right" in hold else 0) - (1 if "left" in hold else 0)
        dy = (1 if "down" in hold else 0) - (1 if "up" in hold else 0)
        self.moving = bool(dx or dy)
        if self.moving:
            ln = math.hypot(dx, dy)
            dx, dy = dx / ln, dy / ln
            if abs(dx) >= abs(dy):
                self.dir = "right" if dx > 0 else "left"
            else:
                self.dir = "down" if dy > 0 else "up"
            nx = self.x + dx * self.speed * dt
            if self._free(nx, self.y, solids, no_go):
                self.x = nx
            ny = self.y + dy * self.speed * dt
            if self._free(self.x, ny, solids, no_go):
                self.y = ny
            self.anim += dt
            self.frame = int(self.anim / 0.14) % 2
        else:
            self.anim = 0.0
            self.frame = 0

    def _free(self, x, y, solids, no_go):
        if not (36 <= x <= W - 36 and 128 <= y <= H - 18):
            return False
        for r in solids:
            if circle_rect(x, y, self.RADIUS, r):
                return False
        for r in no_go:
            if circle_rect(x, y, self.RADIUS, r):
                return False
        return True


class Camper:
    def __init__(self, data):
        self.path = [tuple(p) for p in data["path"]]
        self.x, self.y = self.path[0]
        self.idx = 1 % len(self.path)
        self.speed = data.get("speed", 50)
        self.wait = data.get("wait", 0.8)
        self.variant = data.get("variant", 0)
        self.sit = data.get("sit", False)
        self.scan = data.get("scan", 0.55)
        self.alarm = 0.0
        self.t = 0.0
        self.timer = 0.0
        self.frame = 0
        self.anim = 0.0
        f = data.get("facing")
        self.base = math.atan2(f[1], f[0]) if f else 0.0
        self.angle = self.base

    def update(self, dt):
        self.t += dt
        self.alarm = max(0.0, self.alarm - dt * 3.0)
        if self.sit or len(self.path) == 1:
            self.angle = self.base + math.sin(self.t * 0.9) * (self.scan * 0.5 if self.sit else self.scan)
            self.frame = 0
            return
        if self.timer > 0:
            self.timer -= dt
            self.angle = self.base + math.sin(self.t * 1.7) * self.scan
            self.frame = 0
            return
        tx, ty = self.path[self.idx]
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d < 5:
            self.idx = (self.idx + 1) % len(self.path)
            self.timer = self.wait
            self.anim = 0.0
            self.frame = 0
            return
        self.angle = math.atan2(dy, dx)
        self.base = self.angle
        step = min(d, self.speed * dt)
        self.x += dx / d * step
        self.y += dy / d * step
        self.anim += dt
        self.frame = int(self.anim / 0.20) % 2

    def sees(self, p, covers):
        dx = p.x - self.x
        dy = (p.y - 24) - (self.y - 26)
        d = math.hypot(dx, dy)
        if d > FAR:
            return None
        if d <= NEAR:
            return "near"
        a = math.atan2(dy, dx)
        diff = abs((a - self.angle + math.pi) % (2 * math.pi) - math.pi)
        if diff > HALF_FOV:
            return None
        ex, ey = self.x, self.y - 26
        for r in covers:
            if seg_hits_rect(ex, ey, p.x, p.y - 24, r):
                return None
        return "far"

    def facing(self):
        c, s = math.cos(self.angle), math.sin(self.angle)
        if abs(c) >= abs(s):
            return "right" if c > 0 else "left"
        return "down" if s > 0 else "up"


class Prop:
    def __init__(self, name, x, y, scale):
        spec = PROP_SPECS[name]
        self.name, self.x, self.y, self.scale = name, x, y, scale
        sw, sh = spec["solid"]
        self.solid = rect_at(x, y, sw * scale, sh * scale) if sw > 0 else None
        self.cover = rect_at(x, y, *spec["cover"]) if spec["cover"] else None
        self.pad = spec["pad"]
        self.shadow = spec["shadow"]
        self.glow = spec.get("glow", 0)
        self.hide = spec.get("hide", False)
        self.sprite = spec.get("sprite")

    def hide_rect(self):
        """수풀 잎에 실제로 가려지는 영역 (발 위치 기준)."""
        if not self.sprite:
            return None
        w, h = self.sprite
        return (self.x - w * self.scale / 2 + 6, self.y - h * self.scale + 2,
                self.x + w * self.scale / 2 - 6, self.y - 2)


class Food:
    def __init__(self, kind, x, y, index):
        self.kind, self.x, self.y, self.index = kind, float(x), float(y), index
        self.collected = False
        self.t = (index * 1.7) % 6.28


class Game:
    def __init__(self):
        self.images = {}
        base = os.path.dirname(os.path.abspath(__file__))
        if base not in os.sys.path:
            os.sys.path.insert(0, base)
        os.chdir(base)          # pico2d 는 상대 경로로 이미지를 읽는다
        self.reset()

    # ---------------------------------------------------------- assets
    def img(self, name):
        im = self.images.get(name)
        if im is None:
            im = load_image(os.path.join("assets", name))
            self.images[name] = im
        return im

    # ---------------------------------------------------------- setup
    def reset(self):
        self.map_index = 0
        self.collected = set()
        self.gauge = 0.0
        self.time = 0.0
        self.toast_timer = 0.0
        self.prompt_food = None
        self.load_map(0)
        self.state = "intro"
        self.timer = 2.2

    def load_map(self, i):
        d = MAPS[i]
        self.map = d
        self.props = [Prop(n, x, y, s) for (n, x, y, s) in d["props"]]
        self.solids = [p.solid for p in self.props if p.solid]
        self.covers = [p.cover for p in self.props if p.cover]
        self.hides = [p for p in self.props if p.hide]
        self.no_go = [tuple(r) for r in d["no_go"]]
        self.foods = [Food(k, x, y, i * 3 + j)
                      for j, (k, x, y) in enumerate(d["foods"])]
        self.campers = [Camper(c) for c in d["campers"]]
        self.player = Player(*d["player"])
        self.gauge = 0.0
        self.prompt_food = None
        self.hidden = False
        self.hidden_bush = None

    def goto_next_map(self):
        self.map_index += 1
        self.load_map(self.map_index)
        self.state = "intro"
        self.timer = 2.0

    # ---------------------------------------------------------- update
    def update(self, dt, hold=frozenset(), press=frozenset()):
        self.time += dt
        if "restart" in press:
            self.reset()
            return
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)

        if self.state == "intro":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "playing"
            return
        if self.state in ("caught", "win"):
            return
        if self.state == "map_clear":
            self.timer -= dt
            if self.timer <= 0:
                self.goto_next_map()
            return

        # ---- playing
        self.player.update(dt, hold, self.solids, self.no_go)
        for c in self.campers:
            c.update(dt)

        # 수풀 속에 몸을 숨겼는가 (수풀 잎에 발이 들어가면 은신)
        self.hidden_bush = None
        for p in self.hides:
            if in_rect(self.player.x, self.player.y, p.hide_rect()):
                self.hidden_bush = p
                break
        self.hidden = self.hidden_bush is not None

        seen = None
        for c in self.campers:
            s = c.sees(self.player, self.covers)
            if s == "far" and self.hidden:
                s = None          # 수풀에 숨으면 멀리서는 보이지 않는다
            if s:
                c.alarm = 1.0
            if s == "near":
                seen = "near"
            elif s == "far" and seen != "near":
                seen = "far"
        if seen == "near":
            self.gauge += RISE_NEAR * dt
        elif seen == "far":
            self.gauge += RISE_FAR * dt
        else:
            self.gauge -= FALL * dt
        self.gauge = max(0.0, min(100.0, self.gauge))
        if self.gauge >= 100.0:
            self.state = "caught"
            return

        self.prompt_food = self.nearest_food(78)
        if "collect" in press and self.prompt_food is not None:
            f = self.prompt_food
            f.collected = True
            self.collected.add(f.index)
            self.gauge = min(100.0, self.gauge + PICKUP_NOISE)
            self.toast_timer = 1.1
            self.prompt_food = None
            if all(x.collected for x in self.foods):
                if self.map_index >= len(MAPS) - 1:
                    self.state = "win"
                else:
                    self.state = "map_clear"
                    self.timer = 1.7

    def nearest_food(self, r):
        best, bd = None, r
        for f in self.foods:
            if f.collected:
                continue
            d = math.hypot(f.x - self.player.x, f.y - self.player.y)
            if d < bd:
                best, bd = f, d
        return best

    # ---------------------------------------------------------- render
    def render(self):
        clear_canvas()
        self.img(self.map["bg"]).draw_to_origin(0, 0)

        # 조명 웅덩이 (밤)
        for p in self.props:
            if p.glow:
                g = self.img("glow_lamp.png")
                g.opacify(0.55)
                g.draw(p.x, H - p.y + p.glow * 0.55, p.glow * 2.2, p.glow * 2.2)
                g.opacify(1.0)

        # 시야 콘
        cone = self.img(self.map["cone"])
        for c in self.campers:
            cone.composite_draw(-c.angle, "", c.x, H - c.y + 26, 680, 680)

        # 음식 발광
        for f in self.foods:
            if f.collected:
                continue
            g = self.img("glow_food.png")
            g.opacify(0.42 + 0.14 * math.sin(self.time * 3.2 + f.t))
            g.draw(f.x, H - f.y, 108, 108)
            g.opacify(1.0)

        # y 정렬
        items = []
        for p in self.props:
            items.append((p.y, "prop", p))
        for f in self.foods:
            if not f.collected:
                items.append((f.y + 0.1, "food", f))
        for c in self.campers:
            items.append((c.y, "camper", c))
        items.append((self.player.y, "player", self.player))
        items.sort(key=lambda t: t[0])

        for _, kind, obj in items:
            if kind == "prop":
                self.draw_prop(obj)
            elif kind == "food":
                self.draw_food(obj)
            elif kind == "camper":
                self.draw_camper(obj)
            else:
                self.draw_player(obj)

        self.draw_hud()

    def draw_prop(self, p):
        if p.shadow:
            self.img("shadow.png").draw(p.x, H - p.y + 3, p.shadow * p.scale,
                                        p.shadow * 0.34)
        if p.name == "prop_fire":
            im = self.img("prop_fire_%d.png" % (int(self.time * 5) % 2))
        else:
            im = self.img(p.name + ".png")
        w, h = im.w * p.scale, im.h * p.scale
        im.draw(p.x, H - p.y + h / 2 - p.pad * p.scale, w, h)
        if p.name == "prop_lantern":
            self.img("glow_lamp.png").draw(p.x, H - p.y + 150, 150, 150)

    def draw_food(self, f):
        bob = math.sin(self.time * 2.4 + f.t) * 2.5
        self.img("shadow.png").draw(f.x, H - f.y + 20, 52, 18)
        self.img("food_%s.png" % f.kind).draw(f.x, H - f.y + bob, 54, 54)

    def draw_camper(self, c):
        self.img("shadow.png").draw(c.x, H - c.y + 3, 44, 18)
        if c.sit:
            im = self.img("camper_sit.png")
        else:
            im = self.img("camper%d_%s.png" % (c.variant % 4, c.facing()))
        im.draw(c.x, H - c.y + im.h / 2 - 3, im.w, im.h)
        if c.alarm > 0 and int(self.time * 8) % 2 == 0:
            self.img("mark_alert.png").draw(c.x + 16, H - c.y + 74, 26, 34)

    def draw_player(self, p):
        self.img("shadow.png").draw(p.x, H - p.y + 3, 46, 19)
        im = self.img("pico_%s_%d.png" % (p.dir, p.frame))
        if self.hidden:
            im.opacify(0.9)
        im.draw(p.x, H - p.y + im.h / 2 - 4, im.w, im.h)
        im.opacify(1.0)
        if self.hidden and self.hidden_bush:
            b = self.hidden_bush
            leaf = self.img("prop_bush.png")
            sw, sh = leaf.w * b.scale, leaf.h * b.scale
            leaf.opacify(0.80)
            leaf.draw(b.x, H - b.y + sh / 2 - b.pad * b.scale, sw, sh)
            leaf.opacify(1.0)

    # ---------------------------------------------------------- HUD
    def draw_hud(self):
        # 월드 위 어두운 비네트
        self.img("vignette_dark.png").draw(W / 2, H / 2, W, H)

        if self.gauge > 55:
            r = self.img("vignette_red.png")
            r.opacify(min(1.0, (self.gauge - 55) / 45.0))
            r.draw(W / 2, H / 2, W, H)
            r.opacify(1.0)

        self.img("hud_bar.png").draw_to_origin(0, H - 86)
        self.img(self.map["label"]).draw_to_origin(24, H - 75)

        # 은신 중 표시
        if self.hidden and self.state == "playing":
            badge = self.img("hud_hidden.png")
            badge.opacify(0.80 + 0.16 * math.sin(self.time * 4.0))
            badge.draw(self.player.x, H - self.player.y + 82, 104, 34)
            badge.opacify(1.0)

        # 음식 9칸
        sx = W / 2 - 212
        for i in range(9):
            x = sx + i * 48
            done = i in self.collected
            self.img("slot_full.png" if done else "slot_empty.png").draw_to_origin(x, H - 63)
            if done:
                self.img("food_%s.png" % FOOD_ORDER[i]).draw(x + 20, H - 43, 34, 34)

        # 감지 게이지
        self.img("hud_gauge.png").draw_to_origin(1000, H - 40)
        self.img("hud_gauge_bg.png").draw_to_origin(1000, H - 74)
        frac = max(0.0, min(1.0, self.gauge / 100.0))
        g = self.gauge
        if g < 50:
            t = g / 50.0
            col = (int(92 + (233 - 92) * t), int(160 + (166 - 160) * t),
                   int(108 + (63 - 108) * t))
        else:
            t = (g - 50) / 50.0
            col = (int(233 + (220 - 233) * t), int(166 + (83 - 166) * t),
                   int(63 + (48 - 63) * t))
        if frac > 0.002:
            draw_rectangle(1004, 651, 1004 + 232 * frac, 667, *col, filled=True)

        self.img("hud_controls.png").draw_to_origin(24, 24)

        # 획득 토스트
        if self.toast_timer > 0:
            t = self.toast_timer / 1.1
            self.img("hud_toast.png").draw(W / 2, H - 128 + (1 - t) * 14, 150, 44)

        # E 프롬프트
        if self.state == "playing" and self.prompt_food is not None:
            f = self.prompt_food
            self.img("hud_prompt.png").draw(f.x, H - f.y + 62, 112, 44)

        # 상태 오버레이
        if self.state == "intro":
            self.img(self.map["intro"]).draw_to_origin(0, 0)
        elif self.state == "map_clear":
            self.img("over_mapclear.png").draw_to_origin(0, 0)
        elif self.state == "caught":
            self.img("over_caught.png").draw_to_origin(0, 0)
        elif self.state == "win":
            self.img("over_clear.png").draw_to_origin(0, 0)

    # ---------------------------------------------------------- helpers
    @property
    def total_collected(self):
        return len(self.collected)
