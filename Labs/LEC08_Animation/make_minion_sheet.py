"""미니언 스프라이트 시트 생성기.

시트 구성: 8열 x 5행, 한 셀은 200x200 픽셀
  행 0: idle   (가만히 서 있기)
  행 1: walk   (걷기)
  행 2: run    (뛰기)
  행 3: jump   (점프)
  행 4: attack (공격)

저해상도(50x50) 그리드에 픽셀아트로 그린 뒤 NEAREST 확대해
선명한 픽셀 스프라이트를 얻는다.
"""

from PIL import Image, ImageChops, ImageDraw

# 시트 / 셀 규격
COLS = 8
ROWS = 5
CELL = 200

# 저해상도 드로잉 그리드
GRID_W = 50
GRID_H = 50
SCALE = CELL // GRID_W
OW = 1  # 아웃라인 두께

# 팔레트
OUTLINE = (74, 56, 20, 255)
YELLOW = (250, 208, 40, 255)
YELLOW_DARK = (214, 168, 22, 255)
YELLOW_LIGHT = (255, 232, 112, 255)
OVERALL = (48, 84, 168, 255)
OVERALL_DARK = (28, 52, 110, 255)
BUTTON = (168, 172, 180, 255)
GOGGLE = (176, 182, 192, 255)
GOGGLE_DARK = (112, 118, 130, 255)
EYE_WHITE = (252, 252, 252, 255)
PUPIL = (28, 28, 36, 255)
MOUTH = (120, 40, 40, 255)
HAIR = (58, 48, 38, 255)
SHOE = (66, 66, 78, 255)
SHOE_DARK = (44, 44, 54, 255)

# 몸체 기준 좌표 (cx: 가로 중심, y0: 머리 위, y1: 몸 아래, hw: 반너비)
BODY_CX = 25
BODY_HW = 10
BODY_TOP = 12
BODY_BOTTOM = 41
GROUND = 47


def new_frame():
    """빈 RGBA 프레임(그리드 크기)을 만든다."""
    return Image.new('RGBA', (GRID_W, GRID_H), (0, 0, 0, 0))


def to_cell(image):
    """그리드 이미지를 200x200 셀로 확대한다."""
    return image.resize((CELL, CELL), Image.NEAREST)


def ellipse(draw, cx, cy, rx, ry, fill=None, outline=None, ow=OW):
    """타원을 그린다. outline이 있으면 먼저 1픽셀 넓게 덧그린다."""
    if outline is not None:
        ellipse(draw, cx, cy, rx + ow, ry + ow, fill=outline, ow=0)
    if fill is not None:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def box(draw, x0, y0, x1, y1, fill=None, outline=None, ow=OW):
    """사각형을 그린다. outline이 있으면 먼저 1픽셀 넓게 덧그린다."""
    if outline is not None:
        box(draw, x0 - ow, y0 - ow, x1 + ow, y1 + ow, fill=outline, ow=0)
    if fill is not None:
        draw.rectangle([x0, y0, x1, y1], fill=fill)


def capsule(draw, cx, y0, y1, hw, fill=None, outline=None, ow=OW):
    """위아래가 둥근 캡슐(미니언 몸통 모양)을 그린다."""
    if outline is not None:
        capsule(draw, cx, y0 - ow, y1 + ow, hw + ow, fill=outline, ow=0)
    if fill is None:
        return
    draw.rectangle([cx - hw, y0 + hw, cx + hw, y1 - hw], fill=fill)
    draw.ellipse([cx - hw, y0, cx + hw, y0 + 2 * hw], fill=fill)
    draw.ellipse([cx - hw, y1 - 2 * hw, cx + hw, y1], fill=fill)


def limb(draw, x0, y0, x1, y1, fill, outline=OUTLINE, width=4):
    """팔/다리처럼 가늘고 긴 모양을 아웃라인과 함께 그린다."""
    draw.line([x0, y0, x1, y1], fill=outline, width=width + 2)
    draw.line([x0, y0, x1, y1], fill=fill, width=width)


def clip_to(frame, mask):
    """frame에 mask(흰색=보존) 영역만 남긴다."""
    frame.putalpha(ImageChops.multiply(frame.getchannel('A'), mask))
    return frame


def default_pose(**overrides):
    """프레임 하나의 몸 상태. 필요에 따라 값을 덮어쓴다."""
    pose = {
        'body_dy': 0,     # 몸통 상하 이동
        'lean': 0,        # 몸통 좌우 이동(달리기/공격 기울기)
        'arm_front': (4, 5),   # 앞쪽 팔 끝점 (dx, dy) - 어깨 기준
        'arm_back': (-4, 5),   # 뒤쪽 팔 끝점
        'foot_front': (2, 0),  # 앞쪽 발 위치 (dx, dy)
        'foot_back': (-2, 0),  # 뒤쪽 발 위치
        'leg': 0,         # 다리 길이(점프할 때 늘어난다)
        'eye': 'open',    # open / blink / angry
        'mouth': 'smile',  # smile / open / flat
        'brow': False,    # 눈썹(화남 표현)
        'hair_sway': 0,   # 머리카락 흔들림
    }
    pose.update(overrides)
    return pose


def body_geom(pose):
    """현재 자세의 몸통 기하 정보 (중심x, 위y, 아래y, 반너비)."""
    return (BODY_CX + pose['lean'],
            BODY_TOP + pose['body_dy'],
            BODY_BOTTOM + pose['body_dy'],
            BODY_HW)


def body_mask(pose):
    """몸통 영역만 흰색인 마스크를 만든다(얼굴/옷 디테일 자르기용)."""
    cx, y0, y1, hw = body_geom(pose)
    mask = Image.new('L', (GRID_W, GRID_H), 0)
    capsule(ImageDraw.Draw(mask), cx, y0, y1, hw, fill=255)
    return mask


def draw_body(frame, pose):
    """노란 캡슐 몸통과 좌우 음영을 그린다."""
    draw = ImageDraw.Draw(frame)
    cx, y0, y1, hw = body_geom(pose)
    capsule(draw, cx, y0, y1, hw, fill=YELLOW, outline=OUTLINE)
    capsule(draw, cx + 3, y0 + 3, y1 - 2, hw - 3, fill=YELLOW_DARK)
    capsule(draw, cx - 5, y0 + 5, y1 - 7, 2, fill=YELLOW_LIGHT)
    return frame


def draw_overalls(frame, pose):
    """파란 Overall(바지), 앞치마, 어깨끈, 단추를 그린다.

    바지 부분은 몸통 마스크로 잘라서 몸통 곡선을 그대로 따라가게 한다.
    """
    cx, y0, y1, hw = body_geom(pose)
    waist = y0 + 20

    layer = new_frame()
    draw = ImageDraw.Draw(layer)
    box(draw, cx - hw, waist, cx + hw, y1 + 4, fill=OVERALL)
    box(draw, cx - hw, y1 - 5, cx + hw, y1 + 4, fill=OVERALL_DARK)
    for sx in (-6, 3):
        box(draw, cx + sx, y0 + 6, cx + sx + 3, y0 + 16,
            fill=OVERALL, outline=OVERALL_DARK)
    box(draw, cx - 5, y0 + 15, cx + 5, waist + 2,
        fill=OVERALL, outline=OVERALL_DARK)
    box(draw, cx - 3, y0 + 19, cx + 3, waist + 1,
        fill=OVERALL, outline=OVERALL_DARK)
    ellipse(draw, cx, y0 + 17, 2, 2, fill=BUTTON)
    clip_to(layer, body_mask(pose))

    frame.alpha_composite(layer)
    return frame
