# -*- coding: utf-8 -*-
"""피코의 캠핑장 습격 — 게임 로직.

main.py 가 pico2d 입력을 hold/press 로 바꿔 Game.update() 에 넘긴다.
헤드리스 테스트/스크린샷 도구도 같은 Game 객체를 직접 돌릴 수 있다.
"""
import math
import os
import random

from pico2d import clear_canvas, draw_rectangle, load_image, load_wav

from maps import MAPS

W, H = 1280, 720

# ---- 이동 / 발소리
WALK_SPEED = 205.0      # 기본 걷기
RUN_SPEED = 320.0       # Shift 달리기 (걷기의 1.56배)
NOISE_WALK = 110.0      # 걷기 발소리가 들리는 반경
NOISE_RUN = 270.0       # 달리기 발소리 반경
NOISE_BUSH = 0.55       # 수풀 안에서는 발소리가 줄어든다
STRIDE_WALK = 58.0      # 발소리 한 번 = 이만큼 이동
STRIDE_RUN = 96.0

# ---- 감지 튜닝 값
NEAR = 180.0            # 이 안쪽은 무조건 들킨다 (기존 150 → 180)
FAR = 370.0             # 시야 + 엄폐물 판정이 적용되는 최대 거리 (기존 320 → 370)
HALF_FOV = math.radians(55)
RISE_NEAR = 38.0        # 근거리 기본 %/s
NEAR_BOOST = 1.7        # 붙을수록 가속: d=0 이면 RISE_NEAR * 2.7
RISE_FAR = 15.0         # 원거리 기본 %/s
RISE_HEAR_WALK = 9.0    # 발소리만 들렸을 때 %/s
RISE_HEAR_RUN = 21.0
FALL = 26.0
PICKUP_NOISE = 6.0

# ---- 자고 있는 사람
SLEEP_NEAR = 260.0      # 이 안으로 들어가면 게이지가 오른다 (음식 166px → 반드시 안쪽)
RISE_SLEEP = 46.0       # 자는 사람 근접 기본 %/s
SLEEP_BOOST = 2.0       # d=0 이면 RISE_SLEEP * 3.0

# ---- 텐트
DOOR_LOCK = 0.6         # 들어가고 나온 직후 출입구 재입력 방지

# ---- 2번 맵 낚싯배 / 낚시
BOAT_SPEED = 190.0      # WASD / 방향키로 배를 조종하는 속도
BOAT_HULL_HALF_W = 98.0 # 배 그림 반폭 — 물 영역 좌우 끝에 배를 붙일 때 사용
BOAT_HULL_HALF_H = 42.0 # 배 그림 반높이 — 물 영역 위아래 끝에 배를 붙일 때 사용
BOAT_HALF_W = 46.0      # 배 안에서 움직일 수 있는 가로 반폭
BOAT_HALF_H = 17.0      # 배 안에서 움직일 수 있는 세로 반폭
FISH_TIME = 1.5         # E 홀드로 게이지가 차는 시간
FISH_ZONE_W = 0.20      # 움직이는 초록 구간 폭 (게이지 비율)
FISH_ZONE_SPEED = 2.2   # 초록 구간이 왕복하는 속도
FISH_PATIENCE = 2.4     # 걸린 뒤 이 시간 넘게 떼지 않으면 줄이 끊긴다
FISH_COOLDOWN = 0.55    # 한 번 낚은 뒤 다시 시도할 수 있는 시간
FISH_ANIM = 1.2         # 물고기가 떠오르는 연출 시간
FISH_NOISE = 26.0       # 낚시 성공 시 발소리 대신 퍼지는 소음

# ---- 썩은 음식
GOOD_OUTDOOR = 2        # 야외에서 카운트되는 음식은 맵마다 최대 2개
#       1·2번 맵: 야외 4개 중 2개 썩음 + 텐트 음식 1개(항상 정상·필수) = 정상 3개
#       3번 맵:   야외 5개 중 3개 썩음 = 정상 2개

# ---- 추격
CHASE_SPEED = 240.0     # 달리기(320)보다 느리다 → 달리면 따돌릴 수 있다
CHASE_HOLD = 100.0      # 추격 중 게이지 상한
CHASE_FALL = 24.0       # 시야에서 벗어나면 게이지가 내려가는 속도
CHASE_ESCAPE = 34.0     # 게이지가 이 아래로 떨어지면 추격 종료
CHASE_GIVEUP = 1.7      # 이 시간 동안 못 보면 포기
CHASE_MAX = 9.0         # 최대 추격 시간
CATCH_DIST = 46.0       # 이 안까지 붙으면 잡힌다


def _food_layout():
    """음식 전역 인덱스 — 캠핑장 야외 음식 다음에 그 텐트 음식이 온다."""
    order, base, n = [], [], 0
    for m in MAPS:
        base.append(n)
        kinds = [k for (k, _, _) in m["foods"]]
        if m.get("tent"):
            kinds.append(m["tent"]["food"][0])
        order.extend(kinds)
        n += len(kinds)
    return order, base


FOOD_ORDER, FOOD_BASE = _food_layout()
FOOD_BASES = FOOD_BASE + [len(FOOD_ORDER)]

# 맵의 마지막 음식 = 진짜 음식 (숲속 마시멜로 / 호숫가 샌드위치 / 축제 수프).
# 절대 썩지 않고, 이걸 먹어야만 맵이 클리어된다 → 3개 맵에서 진짜 음식 3개.
REAL_INDICES = tuple(FOOD_BASES[i + 1] - 1 for i in range(len(MAPS)))
REAL_SET = frozenset(REAL_INDICES)

LAKE_MAP = 1                    # 호숫가 — 텐트 대신 낚싯배가 있는 맵
FISH_INDEX = REAL_INDICES[LAKE_MAP]   # 생선 = 호수에서 낚시로만 얻는 진짜 음식

HUD_SLOTS = len(FOOD_ORDER)     # 상단 음식 칸 수 (15칸 유지)

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
    "prop_sleepbag":   dict(solid=(0, 0), cover=None, pad=2, shadow=118),
    "prop_sleeper":    dict(solid=(0, 0), cover=None, pad=2, shadow=0),
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


def path_markers(points, spacing=54.0):
    """출구까지 이어지는 길 위의 표지 좌표를 일정 간격으로 뽑는다."""
    out = []
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        d = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(d // spacing))
        for i in range(n + 1):
            t = i / n
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    return out


# ---------------------------------------------------------------- entities
class Player:
    RADIUS = 15

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.dir = "down"
        self.frame = 0
        self.anim = 0.0
        self.moving = False
        self.sprinting = False
        self.sitting = False
        self.speed = WALK_SPEED
        self.moved = 0.0

    def update(self, dt, hold, solids, no_go):
        if self.sitting:
            # 수풀에 앉아 있으면 움직이지 않는다 — 발소리도 나지 않는다
            self.moving = False
            self.sprinting = False
            self.speed = 0.0
            self.moved = 0.0
            self.anim = 0.0
            self.frame = 0
            return
        dx = (1 if "right" in hold else 0) - (1 if "left" in hold else 0)
        dy = (1 if "down" in hold else 0) - (1 if "up" in hold else 0)
        self.moving = bool(dx or dy)
        self.sprinting = self.moving and "sprint" in hold
        speed = RUN_SPEED if self.sprinting else WALK_SPEED
        self.speed = speed
        ox, oy = self.x, self.y
        if self.moving:
            ln = math.hypot(dx, dy)
            dx, dy = dx / ln, dy / ln
            if abs(dx) >= abs(dy):
                self.dir = "right" if dx > 0 else "left"
            else:
                self.dir = "down" if dy > 0 else "up"
            nx = self.x + dx * speed * dt
            if self._free(nx, self.y, solids, no_go):
                self.x = nx
            ny = self.y + dy * speed * dt
            if self._free(self.x, ny, solids, no_go):
                self.y = ny
            self.anim += dt * (1.5 if self.sprinting else 1.0)
            self.frame = int(self.anim / 0.14) % 2
        else:
            self.anim = 0.0
            self.frame = 0
        self.moved = math.hypot(self.x - ox, self.y - oy)

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
        self.mode = "patrol"      # patrol / chase / return
        self.lost = 0.0           # 추격 중 시야를 놓친 시간
        self.chase_t = 0.0
        self.ret = 0              # 복귀 목표 경로 index
        self.heard = False
        self.napper = data.get("sleep", False)
        self.sleeping = self.napper
        self.home = self.path[0]

    # ---------------------------------------------------------- 상태
    def dist_to(self, p):
        return math.hypot(p.x - self.x, (p.y - 24) - (self.y - 26))

    def begin_chase(self):
        self.mode = "chase"
        self.lost = 0.0
        self.chase_t = 0.0
        self.alarm = 1.0
        self.sleeping = False      # 자다가 깬다

    def give_up(self):
        self.mode = "return"
        self.ret = self.nearest_node()
        self.alarm = 0.0

    def nearest_node(self):
        best, bd = 0, 1e9
        for i, (x, y) in enumerate(self.path):
            d = math.hypot(x - self.x, y - self.y)
            if d < bd:
                bd, best = d, i
        return best

    def hears(self, p, radius):
        if radius <= 0 or self.sleeping:
            return False
        d = math.hypot(p.x - self.x, (p.y - 24) - (self.y - 26))
        return d <= radius

    def look_at(self, p):
        self.angle = math.atan2((p.y - 24) - (self.y - 26), p.x - self.x)
        self.base = self.angle

    def _free(self, x, y, solids):
        if not (24 <= x <= W - 24 and 120 <= y <= H - 14):
            return False
        for r in solids:
            if circle_rect(x, y, 20.0, r):
                return False
        return True

    def move_toward(self, tx, ty, dt, speed, solids):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d < 2:
            return 0.0
        self.angle = math.atan2(dy, dx)
        self.base = self.angle
        step = min(d, speed * dt)
        ux, uy = dx / d * step, dy / d * step
        if self._free(self.x + ux, self.y + uy, solids):
            self.x += ux
            self.y += uy
        else:                      # 소품에 걸리면 축별로 미끄러진다
            if self._free(self.x + ux, self.y, solids):
                self.x += ux
            if self._free(self.x, self.y + uy, solids):
                self.y += uy
        self.anim += dt
        self.frame = int(self.anim / 0.20) % 2
        return step

    def update(self, dt):
        self.t += dt
        self.alarm = max(0.0, self.alarm - dt * 3.0)
        if self.sleeping:
            self.frame = int(self.t * 0.9) % 2      # 천천히 숨쉬는 느낌
            return
        if self.mode != "patrol":
            return
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
        if self.sleeping:
            return None
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
    def __init__(self, seed=None):
        self.seed = seed            # 테스트에서 썩은 음식 배치를 고정할 수 있다
        self.images = {}
        base = os.path.dirname(os.path.abspath(__file__))
        if base not in os.sys.path:
            os.sys.path.insert(0, base)
        os.chdir(base)          # pico2d 는 상대 경로로 이미지를 읽는다
        self.sfx = {}
        for name, vol in (("sfx_step_walk", 46), ("sfx_step_run", 92)):
            try:
                w = load_wav(os.path.join("assets", name + ".wav"))
                w.set_volume(vol)
                self.sfx[name] = w
            except Exception:
                pass            # 사운드 장치가 없어도 게임은 돈다
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
        self.toast_kind = "good"
        self.rotten_found = set()
        self.prompt_food = None
        self.fish_rng = random.Random((self.seed or 0) + 991)
        self._assign_rotten()
        self.load_map(0)
        self.state = "intro"
        self.timer = 2.2

    def _assign_rotten(self):
        """야외에서 카운트되는 음식은 맵마다 최대 GOOD_OUTDOOR 개.

        1·2번 맵: 야외 4개 중 2개를 썩혀 정상 2개만 남기고,
                  텐트 안 음식(마지막·진짜 음식)은 절대 썩히지 않는다.
                  → 야외만 다 먹어도 텐트 음식이 남아 있으므로 반드시 들어가야 맵 클리어.
        3번 맵:   야외 5개 중 3개를 썩혀 정상 2개(그중 하나가 진짜 음식)만 남긴다.
        """
        rng = random.Random(self.seed)
        self.rotten = set()
        for i, m in enumerate(MAPS):
            base = FOOD_BASES[i]
            outdoor = range(base, base + len(m["foods"]))
            # 생선은 호수에서 낚시로 얻으므로 야외 음식 계산에서 제외한다.
            candidates = [j for j in outdoor if j != FISH_INDEX]
            real_outdoor = REAL_INDICES[i] in candidates
            pool = [j for j in candidates if j != REAL_INDICES[i]]
            target = max(0, GOOD_OUTDOOR - (1 if real_outdoor else 0))
            n_rotten = max(0, len(pool) - target)
            self.rotten.update(rng.sample(pool, min(n_rotten, len(pool))))

    def load_map(self, i):
        d = MAPS[i]
        self.map = d
        self.scene = d
        self.in_tent = False
        self.tent = None
        self.props = [Prop(n, x, y, s) for (n, x, y, s) in d["props"]]
        self.solids = [p.solid for p in self.props if p.solid]
        self.covers = [p.cover for p in self.props if p.cover]
        self.hides = [p for p in self.props if p.hide]
        self.no_go = [tuple(r) for r in d["no_go"]]
        self.foods = [Food(k, x, y, FOOD_BASE[i] + j)
                      for j, (k, x, y) in enumerate(d["foods"])]
        self.campers = [Camper(c) for c in d["campers"]]
        self.player = Player(*d["player"])
        self.door = d.get("tent_door")
        self.gauge = 0.0
        self.prompt_food = None
        self.prompt_door = False
        self.door_lock = 0.0
        self.hidden = False
        self.hidden_bush = None
        self.chaser = None
        self.noise = 0.0
        self.step_acc = 0.0
        self.chase_count = 0
        self.escaped = 0
        # 낚싯배 / 낚시 상태
        self.boat_mode = None          # None / "sailing" / "fishing" / "landed"
        self.boat = None
        self.lake = None
        self.prompt_boat = False
        self.fishing = 0.0
        self.fish_hooked = False       # 게이지가 차서 E를 떼기를 기다리는 중
        self.fish_hold = 0.0
        self.fish_cd = 0.0
        self.fish_anim = 0.0
        self.fish_miss = False
        # 진짜 음식을 다 먹으면 출구가 열리고, 피코가 걸어가야 다음 맵으로 간다.
        self.exit_open = False
        self.prompt_exit = False

    # ---------------------------------------------------------- 텐트 출입
    def tent_food_index(self, i=None):
        i = self.map_index if i is None else i
        t = MAPS[i].get("tent")
        if not t:
            return None
        return FOOD_BASE[i] + len(MAPS[i]["foods"])

    def map_complete(self):
        """현재 맵의 정상 음식을 모두 모았는가 — 낚시 맵에 있어도 맵 기준으로 판정."""
        i = self.map_index
        # 마지막 음식(진짜 음식)은 썩지도 않고 반드시 먹어야 한다
        if REAL_INDICES[i] not in self.collected:
            return False
        lo, hi = FOOD_BASES[i], FOOD_BASES[i + 1]
        # 썩은 음식은 카운트에서 제외 — 안 주워도 맵 클리어가 가능하다
        return all(j in self.collected for j in range(lo, hi) if j not in self.rotten)

    def real_eaten(self):
        """먹은 진짜 음식 개수 (0~3)."""
        return len(self.collected & REAL_SET)

    def remaining_food(self):
        """현재 맵에 남은 음식 개수 — 썩은 음식도 주우기 전까지는 남은 것으로 센다."""
        lo, hi = FOOD_BASES[self.map_index], FOOD_BASES[self.map_index + 1]
        taken = self.collected | self.rotten_found
        return sum(1 for j in range(lo, hi) if j not in taken)

    def enter_tent(self):
        t = self.map["tent"]
        self.in_tent = True
        self.tent = t
        self.scene = t
        self.props = [Prop(n, x, y, s) for (n, x, y, s) in t["props"]]
        self.solids = [p.solid for p in self.props if p.solid]
        self.covers = []
        self.hides = []
        self.no_go = [tuple(r) for r in t["no_go"]]
        k, fx, fy = t["food"]
        idx = self.tent_food_index()
        food = Food(k, fx, fy, idx)
        food.collected = idx in self.collected
        self.foods = [food]
        self.campers = [Camper(c) for c in t["campers"]]
        self.player = Player(*t["player"])
        self.door = t["door"]
        self.gauge = 0.0
        self.prompt_food = None
        self.prompt_door = False
        self.door_lock = DOOR_LOCK
        self.hidden = False
        self.hidden_bush = None
        self.chaser = None
        self.noise = 0.0
        self.step_acc = 0.0

    def exit_tent(self):
        i = self.map_index
        self.load_map(i)
        for f in self.foods:
            if f.index in self.collected:
                f.collected = True
        ex, ey = self.map["tent_exit"]
        self.player.x, self.player.y = float(ex), float(ey)
        self.player.dir = "down"
        self.state = "playing"
        self.door_lock = DOOR_LOCK
        if self.map_complete():
            self._finish_map()      # 자동 전환 대신 출구를 연다

    # ---------------------------------------------------------- 낚싯배 / 낚시
    def visible_foods(self):
        """호숫가 육지에서는 생선을 보여주지 않는다 — 낚시로만 얻는다."""
        if self.map_index == LAKE_MAP and self.boat_mode is None:
            return [f for f in self.foods if f.index != FISH_INDEX]
        return self.foods

    def board_boat(self):
        if self.map_index != LAKE_MAP or self.boat_mode is not None:
            return False
        bx, by = self.map["boat"]
        self.boat = {"x": float(bx), "y": float(by)}
        self.boat_mode = "sailing"
        self.player.x, self.player.y = bx, by
        self.player.sitting = False
        self.hidden = False
        self.chaser = None
        self.gauge = 0.0
        self.fishing = 0.0
        self.fish_hooked = False
        self.fish_hold = 0.0
        self.toast_kind = "boat"
        self.toast_timer = 1.1
        return True

    def enter_lake(self):
        """배가 호수 끝에 닿으면 낚시 전용 맵으로 전환된다."""
        lake = self.map["lake"]
        self.boat_mode = "fishing"
        self.lake = lake
        self.scene = lake
        bx, by = lake["boat"]
        self.boat = {"x": float(bx), "y": float(by)}
        self.player.x, self.player.y = bx, by
        self.player.sitting = False
        self.props, self.covers, self.hides = [], [], []
        self.solids, self.no_go = [], []
        self.campers = []
        self.foods = []
        self.door = None
        self.prompt_food = None
        self.prompt_door = False
        self.prompt_boat = False
        self.hidden = False
        self.hidden_bush = None
        self.chaser = None
        self.gauge = 0.0
        self.noise = 0.0
        self.fishing = 0.0
        self.fish_hooked = False
        self.fish_hold = 0.0

    def at_fishing_spot(self):
        """배가 낚시 맵 아래쪽 끝(낚시터)에 닿았는가."""
        if self.boat_mode != "fishing" or self.lake is None:
            return False
        _, _, _, bottom = self.water_rect()
        return self.boat["y"] >= bottom - BOAT_HULL_HALF_H - 10.0

    def land_at_spot(self):
        """Q — 낚시터 부두에 하선한다. 낚시는 배 위에서만 가능하므로 여기선 안 된다."""
        self.boat_mode = "landed"
        self.player.sitting = False
        self.hidden = False
        self.chaser = None
        self.gauge = 0.0
        self.noise = 0.0
        self.fishing = 0.0
        self.fish_hooked = False
        self.fish_hold = 0.0
        lx, ly = self.lake.get("landing", (640, 676))
        self.player.x, self.player.y = float(lx), float(ly)
        self.player.dir = "up"
        # 배는 부두 옆에 매어 둔다 — 선수가 가리지 않게 살짝 왼쪽으로.
        self.boat["x"] = max(BOAT_HULL_HALF_W, self.boat["x"] - 150.0)
        self.toast_kind = "spot"
        self.toast_timer = 1.1

    def leave_boat(self):
        """Q — 낚시 맵/항해 중이면 부두로 돌아온다. 열린 출구는 그대로 유지."""
        was_open = self.exit_open
        self.load_map(self.map_index)
        self.exit_open = was_open
        bx, by = self.map["boat"]
        self.player.x, self.player.y = float(bx), float(by) - 72
        self.player.dir = "down"
        self.state = "playing"
        for f in self.foods:
            if f.index in self.collected:
                f.collected = True

    def update_landed(self, dt, hold):
        """낚시터 부두 위 — 좁은 공간에서만 걸어 다닌다."""
        self.fish_anim = max(0.0, self.fish_anim - dt)
        self.player.update(dt, hold, [], [])
        x0, y0, x1, y1 = self.lake.get("spot_rect", (548, 642, 732, 704))
        self.player.x = max(x0, min(x1, self.player.x))
        self.player.y = max(y0, min(y1, self.player.y))
        self.player.sprinting = False

    def clamp_to_boat(self):
        bx, by = self.boat["x"], self.boat["y"]
        self.player.x = max(bx - BOAT_HALF_W, min(bx + BOAT_HALF_W, self.player.x))
        self.player.y = max(by - BOAT_HALF_H, min(by + BOAT_HALF_H, self.player.y))

    def water_rect(self):
        """현재 장면에서 배가 다닐 수 있는 물 영역 (x0, y0, x1, y1)."""
        return self.scene.get("water", (0, 0, W, H))

    def clamp_boat_to_water(self):
        """배 그림 전체가 물 안에 들어오도록 중심 좌표를 제한한다."""
        x0, y0, x1, y1 = self.water_rect()
        self.boat["x"] = max(x0 + BOAT_HULL_HALF_W,
                             min(x1 - BOAT_HULL_HALF_W, self.boat["x"]))
        self.boat["y"] = max(y0 + BOAT_HULL_HALF_H,
                             min(y1 - BOAT_HULL_HALF_H, self.boat["y"]))

    def update_boat(self, dt, hold):
        # 항해 중이든 낚시 맵이든 WASD / 방향키로 배 자체를 조종한다.
        dx = (1 if "right" in hold else 0) - (1 if "left" in hold else 0)
        dy = (1 if "down" in hold else 0) - (1 if "up" in hold else 0)
        if dx or dy:
            ln = math.hypot(dx, dy)
            dx, dy = dx / ln, dy / ln
            self.boat["x"] += dx * BOAT_SPEED * dt
            self.boat["y"] += dy * BOAT_SPEED * dt
            if abs(dx) >= abs(dy):
                self.player.dir = "right" if dx > 0 else "left"
            else:
                self.player.dir = "down" if dy > 0 else "up"
            self.player.moving = True
            self.player.anim += dt
            self.player.frame = int(self.player.anim / 0.14) % 2
        else:
            self.player.moving = False
            self.player.anim = 0.0
            self.player.frame = 0
        self.player.sprinting = False

        # 육지 쪽으로는 절대 못 간다 — 물 영역 끝에서 멈춘다.
        self.clamp_boat_to_water()
        self.player.x, self.player.y = self.boat["x"], self.boat["y"]
        self.clamp_to_boat()

        if self.boat_mode == "sailing":
            # 육지 쪽(물 시작선)이 아니라 물의 먼 쪽 끝(화면 아래)에 닿아야 전환.
            _, _, _, water_bottom = self.water_rect()
            if self.boat["y"] >= water_bottom - BOAT_HULL_HALF_H - 0.01:
                self.enter_lake()
        elif self.boat_mode == "fishing":
            self.update_fishing(dt, hold)

    def fish_zone_center(self):
        """게이지 위를 왕복하는 초록 구간의 중심 (0~1)."""
        return 0.5 + 0.34 * math.sin(self.time * FISH_ZONE_SPEED)

    def fish_on_target(self):
        """가운데 낚시 바늘이 초록 구간 안에 있는가 — E를 떼는 순간 판정."""
        return abs(self.fish_zone_center() - 0.5) <= FISH_ZONE_W / 2.0

    def update_fishing(self, dt, hold):
        self.fish_anim = max(0.0, self.fish_anim - dt)
        self.fish_cd = max(0.0, self.fish_cd - dt)
        if FISH_INDEX in self.collected:
            self.fishing = 0.0
            self.fish_hooked = False
            return

        held = "collect" in hold
        if self.fish_hooked:
            self.fish_hold += dt
            if not held:
                # E를 뗀 순간 타이밍 판정 — 랜덤 도망은 없다.
                self.resolve_fishing(self.fish_on_target())
            elif self.fish_hold >= FISH_PATIENCE:
                self.resolve_fishing(False)     # 너무 오래 잡고 있으면 줄이 끊긴다
            return

        if held and self.fish_cd <= 0:
            self.fishing += dt / FISH_TIME
            if self.fishing >= 1.0:
                self.fishing = 1.0
                self.fish_hooked = True
                self.fish_hold = 0.0
        else:
            self.fishing = max(0.0, self.fishing - dt / FISH_TIME * 1.6)

    def resolve_fishing(self, success):
        self.fishing = 0.0
        self.fish_hooked = False
        self.fish_hold = 0.0
        self.fish_cd = FISH_COOLDOWN
        if not success:
            self.fish_miss = True
            self.toast_kind = "fish_miss"
            self.toast_timer = 1.1
            return
        self.fish_miss = False
        self.fish_anim = FISH_ANIM
        self.collected.add(FISH_INDEX)
        self.gauge = min(100.0, self.gauge + FISH_NOISE)
        self.toast_kind = "big"
        self.toast_timer = 1.1
        w = self.sfx.get("sfx_step_run")
        if w is not None:
            try:
                w.play()
            except Exception:
                pass
        if self.map_complete():
            self._finish_map()

    def goto_next_map(self):
        self.map_index += 1
        self.load_map(self.map_index)
        self.state = "intro"
        self.timer = 2.0

    def bush_at(self, x, y):
        """발밑 (x,y)가 수풀 잎 안이면 그 수풀 Prop 을 돌려준다."""
        for p in self.hides:
            r = p.hide_rect()
            if r and in_rect(x, y, r):
                return p
        return None

    def update_campers(self, dt):
        """캠핑객 순찰·귀환 이동 — 낚싯배를 탄 뒤에도 계속 움직인다."""
        for c in self.campers:
            c.heard = False
            if c.mode == "chase":
                continue
            if c.mode == "return":
                c.update(dt)
                tx, ty = c.path[c.ret]
                c.move_toward(tx, ty, dt, CHASE_SPEED * 0.5, self.solids)
                if math.hypot(tx - c.x, ty - c.y) < 8:
                    c.mode = "patrol"
                    c.idx = (c.ret + 1) % len(c.path)
                    c.timer = c.wait
                    if c.napper:
                        c.sleeping = True      # 다시 눕는다
                continue
            c.update(dt)

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
        if self.door_lock > 0:
            self.door_lock = max(0.0, self.door_lock - dt)

        # Q: 낚싯배 타기 / 낚시터 하선 / 부두 복귀
        if "boat" in press:
            if self.boat_mode == "fishing":
                # 낚시터 부두에 닿기 전에는 절대 내리지 않는다.
                if self.at_fishing_spot():
                    self.land_at_spot()
                return
            if self.boat_mode is not None:
                self.leave_boat()
                return
            bp = self.map.get("boat")
            if (self.map_index == LAKE_MAP and bp is not None
                    and math.hypot(bp[0] - self.player.x, bp[1] - self.player.y) < 82):
                self.board_boat()
                return

        # 배에 탄 동안에는 WASD / 방향키로 배를 조종하고, 화면 끝에서 낚시 맵으로 간다
        if self.boat_mode is not None:
            self.prompt_boat = False
            self.prompt_food = None
            if self.boat_mode == "landed":
                self.update_landed(dt, hold)
            else:
                # 2번 맵 사람들은 배가 출발한 뒤에도 원래 순찰을 계속한다.
                self.update_campers(dt)
                self.update_boat(dt, hold)
            return

        # X: 수풀 안에서만 앉기 / 일어나기 토글
        if "sit" in press:
            if self.player.sitting:
                self.player.sitting = False
            elif self.bush_at(self.player.x, self.player.y) is not None:
                self.player.sitting = True

        self.player.update(dt, hold, self.solids, self.no_go)

        self.update_campers(dt)

        # 수풀 속에 몸을 숨겼는가 (수풀 잎에 발이 들어가면 은신)
        self.hidden_bush = self.bush_at(self.player.x, self.player.y)
        if self.hidden_bush is None and self.player.sitting:
            self.player.sitting = False    # 수풀을 나오면 자동으로 일어난다
        self.hidden = self.hidden_bush is not None

        # 발소리 (걷기 작게 / 달리기 크게)
        self.update_noise(dt)

        # 소리를 들은 사람은 걸음을 멈추고 고개를 돌린다
        for c in self.campers:
            c.heard = False
            if c.mode != "patrol" or c.sleeping:
                continue
            if c.hears(self.player, self.noise):
                c.heard = True
                c.look_at(self.player)
                c.alarm = 1.0
                if c.timer <= 0 and len(c.path) > 1:
                    c.timer = 0.35

        if self.chaser is not None:
            self.update_chase(dt)
        else:
            self.update_gauge(dt)
        if self.state != "playing":
            return

        # 출입구 앞인가
        self.prompt_door = (self.door is not None and self.door_lock <= 0
                            and in_rect(self.player.x, self.player.y, self.door))

        # 부두 끝 낚싯배 앞인가
        bp = self.map.get("boat")
        self.prompt_boat = (bp is not None and self.boat_mode is None
                            and math.hypot(bp[0] - self.player.x,
                                           bp[1] - self.player.y) < 82)

        # 열린 출구 앞에 서 있는가 — 배/텐트 안에서는 사용할 수 없다
        ex = self.map.get("exit")
        self.prompt_exit = (self.exit_open and ex is not None
                            and self.boat_mode is None and not self.in_tent
                            and in_rect(self.player.x, self.player.y, ex["rect"]))

        # 텐트 안에서 쫓기면 문으로 도망칠 수 있다
        if self.in_tent and self.chaser is not None and self.prompt_door:
            self.exit_tent()
            return

        self.prompt_food = self.nearest_food(78)
        if "collect" in press:
            if self.prompt_exit:
                self.use_exit()
                return
            if self.prompt_food is not None:
                self._collect(self.prompt_food)
                if self.state != "playing":
                    return
            elif self.prompt_door:
                if self.in_tent:
                    self.exit_tent()
                elif self.chaser is None:
                    self.enter_tent()
                return

    def _collect(self, f):
        f.collected = True
        self.prompt_food = None
        if f.index in self.rotten:
            # 썩은 음식: 주워지지만 수집 카운트에는 넣지 않고 경고만 띄운다
            self.rotten_found.add(f.index)
            self.toast_kind = "bad"
            self.toast_timer = 1.1
            if self.map_complete() and not self.in_tent:
                self._finish_map()
            return
        self.collected.add(f.index)
        self.gauge = min(100.0, self.gauge + PICKUP_NOISE)
        self.toast_kind = "good"
        self.toast_timer = 1.1
        if self.map_complete() and not self.in_tent:
            self._finish_map()

    def _finish_map(self):
        """진짜 음식을 먹어도 바로 넘어가지 않고 출구를 연다."""
        if self.exit_open or self.state != "playing":
            return
        self.exit_open = True
        self.prompt_exit = False
        self.toast_kind = "exit"
        self.toast_timer = 1.1

    def use_exit(self):
        """출구 게이트에서 E — 피코가 직접 걸어온 뒤에만 다음 맵/완료로 간다."""
        if not self.exit_open or not self.prompt_exit:
            return
        if self.map_index >= len(MAPS) - 1:
            self.state = "win"
        else:
            self.goto_next_map()

    # ---------------------------------------------------------- 발소리 / 감지
    def update_noise(self, dt):
        p = self.player
        if p.moved > 0.4:
            base = NOISE_RUN if p.sprinting else NOISE_WALK
            self.noise = base * (NOISE_BUSH if self.hidden else 1.0)
            self.step_acc += p.moved
            stride = STRIDE_RUN if p.sprinting else STRIDE_WALK
            if self.step_acc >= stride:
                self.step_acc -= stride
                w = self.sfx.get("sfx_step_run" if p.sprinting else "sfx_step_walk")
                if w is not None:
                    try:
                        w.play()
                    except Exception:
                        pass
        else:
            self.noise = 0.0
            self.step_acc = 0.0

    def heard_by(self, camper):
        return self.noise > 0 and camper.hears(self.player, self.noise)

    def update_gauge(self, dt):
        if self.player.sitting and self.hidden:
            # 수풀에 앉아 있으면 근거리·원거리·청각·자는 사람 전부 무시
            # (감지 반경 안에 있어도 눈치채지 못한다)
            self.gauge = max(0.0, self.gauge - FALL * dt)
            return
        rise = 0.0
        for c in self.campers:
            d = c.dist_to(self.player)
            if c.sleeping:
                if d < SLEEP_NEAR:      # 자는 사람에게 붙을수록 급격히 오른다
                    f = 1.0 - d / SLEEP_NEAR
                    rise = max(rise, RISE_SLEEP * (1.0 + SLEEP_BOOST * f ** 1.15))
                continue
            s = c.sees(self.player, self.covers)
            if s == "far" and self.hidden:
                s = None          # 수풀에 숨으면 멀리서는 보이지 않는다
            if s:
                c.alarm = 1.0
            if s == "near":
                # 붙을수록 가속 — d=0 이면 RISE_NEAR * 2.7
                f = max(0.0, 1.0 - d / NEAR)
                rise = max(rise, RISE_NEAR * (1.0 + NEAR_BOOST * f ** 1.4))
            elif s == "far":
                f = max(0.0, 1.0 - (d - NEAR) / max(1.0, FAR - NEAR))
                rise = max(rise, RISE_FAR * (0.7 + 0.6 * f))

        heard = any(c.heard for c in self.campers)
        if heard:
            rise = max(rise, RISE_HEAR_RUN if self.player.sprinting
                       else RISE_HEAR_WALK)
        if rise <= 0.0:
            rise = -FALL

        self.gauge = max(0.0, min(100.0, self.gauge + rise * dt))
        if self.gauge >= 100.0:
            self.start_chase()

    def start_chase(self):
        if not self.campers:
            return
        pool = [c for c in self.campers
                if c.mode == "patrol" and not c.sleeping] or self.campers
        c = min(pool, key=lambda k: math.hypot(k.x - self.player.x,
                                              k.y - self.player.y))
        c.begin_chase()
        self.chaser = c
        self.gauge = CHASE_HOLD
        self.chase_count += 1

    def update_chase(self, dt):
        c = self.chaser
        c.chase_t += dt
        c.move_toward(self.player.x, self.player.y, dt, CHASE_SPEED, self.solids)
        d = math.hypot(c.x - self.player.x, (c.y - 26) - (self.player.y - 24))
        invisible = self.player.sitting and self.hidden
        if d <= CATCH_DIST and not invisible:
            self.state = "caught"
            self.chaser = None
            return

        s = c.sees(self.player, self.covers)
        if s == "far" and self.hidden:
            s = None
        if invisible:
            s = None      # 앉아 있으면 추격 중에도 시야에서 사라진다
        if s:
            c.lost = 0.0
            self.gauge = CHASE_HOLD
        else:
            c.lost += dt
            self.gauge = max(0.0, self.gauge - CHASE_FALL * dt)

        if (c.lost >= CHASE_GIVEUP or self.gauge <= CHASE_ESCAPE
                or c.chase_t >= CHASE_MAX):
            c.give_up()
            self.chaser = None
            self.escaped += 1
            self.gauge = min(self.gauge, 50.0)

    def nearest_food(self, r):
        best, bd = None, r
        for f in self.visible_foods():
            if f.collected:
                continue
            d = math.hypot(f.x - self.player.x, f.y - self.player.y)
            if d < bd:
                best, bd = f, d
        return best

    # ---------------------------------------------------------- render
    def render(self):
        clear_canvas()
        self.img(self.scene["bg"]).draw_to_origin(0, 0)
        cone_name = self.scene.get("cone")

        # 물 끝 안내 표지 — 호숫가 이동 / 낚시터로 이동
        sign = self.scene.get("sign")
        if sign is not None and self.state == "playing":
            sx, sy, sname = sign
            im = self.img(sname)
            im.draw(sx, H - sy + im.h / 2, im.w, im.h)

        # 낚시터 부두 — 하선한 뒤 그 위에 선수가 서 있다
        if self.boat_mode == "landed" and self.lake is not None:
            lx, ly = self.lake.get("landing", (640, 676))
            pier = self.img("prop_pier.png")
            pier.draw(lx, H - ly + pier.h / 2 - 10, pier.w, pier.h)

        # 출구가 열리면 길 표지를 따라 게이트까지 안내한다.
        ex = self.map.get("exit")
        if self.exit_open and ex is not None and self.boat_mode is None and not self.in_tent:
            marker = self.img("fx_exit_trail.png")
            for mx, my in path_markers(ex["path"]):
                marker.opacify(0.55 + 0.35 * math.sin(self.time * 3.2 + mx * 0.02))
                marker.draw(mx, H - my + 8, 28, 22)
            marker.opacify(1.0)
            gx, gy = ex["gate"]
            gate = self.img("fx_exit_win.png" if self.map_index == len(MAPS) - 1
                            else "fx_exit_next.png")
            gate.draw(gx, H - gy + gate.h / 2 - 10, gate.w, gate.h)

        # 조명 웅덩이 (밤)
        for p in self.props:
            if p.glow:
                g = self.img("glow_lamp.png")
                g.opacify(0.55)
                g.draw(p.x, H - p.y + p.glow * 0.55, p.glow * 2.2, p.glow * 2.2)
                g.opacify(1.0)

        # 시야 콘
        if cone_name:
            cone = self.img(cone_name)
            for c in self.campers:
                if c.sleeping:
                    continue        # 자는 사람은 시야가 없다
                cone.composite_draw(-c.angle, "", c.x, H - c.y + 26, 680, 680)

        # 텐트 출입구 표시
        if self.door is not None and self.state == "playing":
            x0, y0, x1, y1 = self.door
            mk = self.img("fx_door.png")
            mk.opacify(0.55 + 0.25 * math.sin(self.time * 3.4))
            mk.draw((x0 + x1) / 2, H - (y0 + y1) / 2 + 6, 168, 76)
            mk.opacify(1.0)

        # 발소리가 퍼지는 반경 (걷기 작게 / 달리기 크게)
        if self.noise > 0 and self.state == "playing":
            ring = self.img("fx_ring.png")
            a = 0.46 if self.player.sprinting else 0.30
            ring.opacify(a * (0.82 + 0.18 * math.sin(self.time * 8.0)))
            ring.draw(self.player.x, H - self.player.y + 4,
                      self.noise * 2.0, self.noise * 1.12)
            ring.opacify(1.0)

        # 음식 발광
        for f in self.visible_foods():
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
        for f in self.visible_foods():
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

        if self.boat is not None:
            self.draw_boat()
        self.draw_hud()

    def draw_boat(self):
        bx, by = self.boat["x"], self.boat["y"]
        self.img("shadow.png").draw(bx, H - by - 4, 168, 30)
        im = self.img("boat.png")
        im.draw(bx, H - by + 12, 196, 84)
        if self.boat_mode == "fishing":
            # 낚싯줄
            from pico2d import draw_line
            draw_line(bx + 62, H - by + 2, bx + 104, H - by - 118,
                      236, 214, 170, 2)
            if self.fish_anim > 0:
                t = 1.0 - self.fish_anim / FISH_ANIM
                fish = self.img("fx_fish_jump.png")
                lift = math.sin(min(1.0, t * 1.5) * math.pi) * 96
                fish.opacify(min(1.0, self.fish_anim * 2.2))
                fish.draw(bx + 104, H - by + lift, 76, 64)
                fish.opacify(1.0)
            ripple = self.img("fx_ring.png")
            ripple.opacify(0.20 + 0.12 * math.sin(self.time * 5.0))
            ripple.draw(bx + 104, H - by + 20, 86, 26)
            ripple.opacify(1.0)

    def draw_fishing_hud(self):
        if self.boat_mode != "fishing" or FISH_INDEX in self.collected:
            return
        self.img("hud_fish_bg.png").draw_to_origin(470, 518)
        frac = max(0.0, min(1.0, self.fishing))
        if frac > 0.002:
            draw_rectangle(486, 530, 486 + 310 * frac, 556,
                           240, 196, 104, filled=True)

        # 움직이는 초록 구간 — 게이지가 찬 뒤 E를 떼는 순간 여기로 판정한다.
        c = self.fish_zone_center()
        half = FISH_ZONE_W / 2.0
        z0 = 486 + 310 * max(0.0, c - half)
        z1 = 486 + 310 * min(1.0, c + half)
        if self.fish_hooked:
            draw_rectangle(int(z0), 530, int(z1), 556, 122, 190, 118, filled=True)
        else:
            draw_rectangle(int(z0), 530, int(z1), 556, 74, 126, 76, filled=True)

        # 가운데 고정 낚시 바늘
        draw_rectangle(638, 526, 642, 560, 250, 246, 236, filled=True)

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
        if c.sleeping:
            # 침낭 위에서 자는 사람 + 떠오르는 Z
            im = self.img("prop_sleeper.png")
            im.draw(c.x, H - c.y + im.h / 2 - 2, im.w, im.h)
            z = self.img("fx_zzz.png")
            zz = 0.55 + 0.45 * math.sin(self.time * 1.8)
            z.opacify(zz)
            z.draw(c.x - 26, H - c.y + 86 + 4 * math.sin(self.time * 1.4), 104, 96)
            z.opacify(1.0)
            return
        if c.sit:
            im = self.img("camper_sit.png")
        else:
            im = self.img("camper%d_%s.png" % (c.variant % 4, c.facing()))
        im.draw(c.x, H - c.y + im.h / 2 - 3, im.w, im.h)
        if c.alarm > 0 and int(self.time * 8) % 2 == 0:
            self.img("mark_alert.png").draw(c.x + 16, H - c.y + 74, 26, 34)

    def draw_player(self, p):
        self.img("shadow.png").draw(p.x, H - p.y + 3, 46, 19)
        if p.sitting and self.hidden_bush:
            # 수풀 잎 위로 머리만 빼꼼 — 몸은 잎에 완전히 가린다
            b = self.hidden_bush
            leaf = self.img("prop_bush.png")
            sw, sh = leaf.w * b.scale, leaf.h * b.scale
            ly = H - b.y + sh / 2 - b.pad * b.scale
            leaf_top = ly + sh / 2
            peek = self.img("pico_peek.png")
            peek.draw(p.x, leaf_top + peek.h * 0.30, peek.w, peek.h)
            leaf.draw(b.x, ly, sw, sh)
            return
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
        self.img(self.scene["label"]).draw_to_origin(24, H - 75)

        # 은신 / 수풀 앉기 표시
        if self.hidden and self.state == "playing":
            name = "hud_sit.png" if self.player.sitting else "hud_hidden.png"
            badge = self.img(name)
            badge.opacify(0.80 + 0.16 * math.sin(self.time * 4.0))
            badge.draw(self.player.x, H - self.player.y + 82, 124, 34)
            badge.opacify(1.0)

        # 추격 중 표시
        if self.chaser is not None and self.state == "playing":
            b = self.img("hud_chase.png")
            b.opacify(0.82 + 0.18 * math.sin(self.time * 9.0))
            b.draw(W / 2, H - 116, 372, 60)
            b.opacify(1.0)

        # 음식 15칸 유지 — 썩은 음식은 주운 뒤 붉은 칸으로 표시하고 카운트에서 제외
        sx = W / 2 - HUD_SLOTS * 24
        for i in range(HUD_SLOTS):
            x = sx + i * 48
            if i in self.collected:
                self.img("slot_full.png").draw_to_origin(x, H - 63)
                self.img("food_%s.png" % FOOD_ORDER[i]).draw(x + 20, H - 43, 34, 34)
            elif i in self.rotten_found:
                self.img("slot_rotten.png").draw_to_origin(x, H - 63)
            else:
                self.img("slot_empty.png").draw_to_origin(x, H - 63)
            if i in REAL_SET:
                # 맵의 마지막 칸 = 진짜 음식 (별 표시)
                self.img("hud_real_mark.png").draw_to_origin(x + 28, H - 55)

        # 15칸 왼쪽 위에 남은 음식 / 진짜 음식 카운터
        remain = max(0, min(len(FOOD_ORDER), self.remaining_food()))
        self.img("hud_remain_%d.png" % remain).draw_to_origin(222, 600)
        real = max(0, min(len(REAL_INDICES), self.real_eaten()))
        self.img("hud_real_%d.png" % real).draw_to_origin(400, 600)

        # 감지 게이지
        self.draw_fishing_hud()

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

        # 획득 / 썩은 음식 경고 토스트
        if self.toast_timer > 0:
            t = self.toast_timer / 1.1
            names = {"bad": "hud_toast_bad.png", "boat": "hud_toast_boat.png",
                     "fish_miss": "hud_toast_miss.png", "big": "hud_toast_big.png",
                     "spot": "hud_toast_spot.png", "exit": "hud_toast_exit.png"}
            name = names.get(self.toast_kind, "hud_toast.png")
            self.img(name).draw(W / 2, H - 128 + (1 - t) * 14, 150, 44)

        # E 프롬프트
        if self.state == "playing" and self.prompt_food is not None:
            f = self.prompt_food
            self.img("hud_prompt.png").draw(f.x, H - f.y + 62, 112, 44)
        elif self.state == "playing" and self.prompt_door and self.door is not None:
            x0, y0, x1, y1 = self.door
            name = "hud_prompt_out.png" if self.in_tent else "hud_prompt_door.png"
            im = self.img(name)
            im.draw((x0 + x1) / 2, H - (y0 + y1) / 2 - 44,
                    im.w, im.h)
        elif self.state == "playing" and self.hidden_bush is not None:
            name = "hud_prompt_stand.png" if self.player.sitting else "hud_prompt_sit.png"
            im = self.img(name)
            im.draw(self.player.x, H - self.player.y + 62, im.w, im.h)

        # 출구 프롬프트 — 길을 따라 걸어온 뒤에만 뜬다
        if self.state == "playing" and self.prompt_exit:
            name = ("hud_prompt_win.png" if self.map_index == len(MAPS) - 1
                    else "hud_prompt_next.png")
            im = self.img(name)
            im.draw(self.player.x, H - self.player.y + 100, im.w, im.h)

        # 낚싯배 프롬프트
        if self.state == "playing" and self.prompt_boat:
            im = self.img("hud_prompt_boat.png")
            bx, by = self.map["boat"]
            im.draw(bx, H - by + 56, im.w, im.h)
        elif self.state == "playing" and self.boat_mode is not None:
            # 호숫가 맵에서는 낚시터 부두에 닿기 전에 '내리기' 문구를 띄우지 않는다.
            name = None
            if self.boat_mode == "landed":
                name = "hud_prompt_return.png"
            elif self.boat_mode == "sailing":
                name = "hud_prompt_leave.png"
            elif self.at_fishing_spot():
                name = "hud_prompt_land.png"
            elif self.boat["y"] >= 600:
                name = "hud_prompt_to_spot.png"
            if name is not None:
                im = self.img(name)
                im.draw(self.player.x + 96, H - self.player.y + 42, im.w, im.h)
            if self.boat_mode == "fishing":
                fi = self.img("hud_prompt_release.png" if self.fish_hooked
                              else "hud_prompt_fish.png")
                fi.draw(self.player.x, H - self.player.y + 92, fi.w, fi.h)

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
