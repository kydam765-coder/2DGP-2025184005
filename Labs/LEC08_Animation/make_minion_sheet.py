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

from PIL import Image, ImageChops

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
