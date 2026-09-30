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
import math

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
SPARK = (255, 246, 170, 255)

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
        'foot_front': (4, 0),  # 앞쪽 발 위치 (dx, dy)
        'foot_back': (-4, 0),  # 뒤쪽 발 위치
        'leg': 0,         # 다리 길이(점프할 때 늘어난다)
        'eye': 'open',    # open / blink / angry
        'mouth': 'smile',  # smile / open / flat
        'brow': False,    # 눈썹(화남 표현)
        'hair_sway': 0,   # 머리카락 흔들림
        'spark': False,   # 공격 타격 효과
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
    capsule(draw, cx + 4, y0 + 4, y1 - 3, hw - 4, fill=YELLOW_DARK)
    capsule(draw, cx - 5, y0 + 1, y0 + 5, 1, fill=YELLOW_LIGHT)
    return frame


def draw_overalls(frame, pose):
    """파란 Overall(바지), 앞치마, 어깨끈, 단추를 그린다.

    바지 부분은 몸통 마스크로 잘라서 몸통 곡선을 그대로 따라가게 한다.
    """
    cx, y0, y1, hw = body_geom(pose)
    bib = y0 + 17

    layer = new_frame()
    draw = ImageDraw.Draw(layer)
    box(draw, cx - hw, bib, cx + hw, y1 + 4, fill=OVERALL)
    box(draw, cx - 3, y0 + 22, cx + 3, y0 + 25,
        fill=OVERALL, outline=OVERALL_DARK)
    for sx in (-6, 3):
        box(draw, cx + sx, y0 + 7, cx + sx + 3, bib + 1,
            fill=OVERALL, outline=OVERALL_DARK)
    ellipse(draw, cx, y0 + 19, 2, 2, fill=BUTTON)
    box(draw, cx - hw, bib, cx + hw, bib, fill=OVERALL_DARK)
    box(draw, cx - hw, y1 - 4, cx + hw, y1 + 4, fill=OVERALL_DARK)
    clip_to(layer, body_mask(pose))

    frame.alpha_composite(layer)
    return frame


def draw_face(frame, pose):
    """고글, 눈, 눈썹, 입을 그린다. 몸통 밖으로는 튀어나가지 않게 자른다."""
    cx, y0, y1, hw = body_geom(pose)
    ey = y0 + 9

    layer = new_frame()
    draw = ImageDraw.Draw(layer)

    box(draw, cx - hw, ey - 4, cx + hw, ey + 3, fill=GOGGLE_DARK)
    box(draw, cx - hw, ey - 4, cx + hw, ey - 3, fill=GOGGLE)

    for i, ex in enumerate((-4, 4)):
        if pose['eye'] == 'blink' and i == 0:
            ellipse(draw, cx + ex, ey, 3, 3, fill=GOGGLE, outline=GOGGLE_DARK)
            box(draw, cx + ex - 2, ey, cx + ex + 2, ey, fill=PUPIL)
            continue
        ellipse(draw, cx + ex, ey, 3, 3, fill=GOGGLE, outline=GOGGLE_DARK)
        ellipse(draw, cx + ex, ey, 2, 2, fill=EYE_WHITE)
        look = 1 if pose['eye'] == 'angry' else 0
        box(draw, cx + ex - 1, ey - 1 + look, cx + ex, ey + look, fill=PUPIL)
        if pose['brow'] or pose['eye'] == 'angry':
            tilt = -1 if i == 0 else 1
            draw.line([cx + ex - 3 * tilt, ey - 6,
                       cx + ex + 3 * tilt, ey - 8], fill=HAIR)

    mouth = pose['mouth']
    if mouth == 'smile':
        box(draw, cx - 3, ey + 3, cx - 2, ey + 4, fill=MOUTH)
        box(draw, cx + 2, ey + 3, cx + 3, ey + 4, fill=MOUTH)
        box(draw, cx - 1, ey + 5, cx + 1, ey + 5, fill=MOUTH)
    elif mouth == 'open':
        ellipse(draw, cx, ey + 5, 2, 2, fill=MOUTH, outline=OUTLINE)
    else:
        box(draw, cx - 2, ey + 4, cx + 2, ey + 4, fill=MOUTH)

    clip_to(layer, body_mask(pose))
    frame.alpha_composite(layer)
    return frame


def draw_hair(frame, pose):
    """머리 꼭대기의 검은 머리카락 뭉치를 그린다."""
    draw = ImageDraw.Draw(frame)
    cx, y0, y1, hw = body_geom(pose)
    sway = pose['hair_sway']
    box(draw, cx - 4 + sway, y0 - 2, cx + 4 + sway, y0 + 1, fill=HAIR)
    draw.polygon([(cx - 2 + sway, y0 - 2), (cx + sway, y0 - 5),
                  (cx + 2 + sway, y0 - 2)], fill=HAIR)
    return frame


def arm_tip(pose, side, tip):
    """팔 끝(주먹) 좌표를 계산한다."""
    cx, y0, y1, hw = body_geom(pose)
    sx = cx + side * (hw - 1)
    sy = y0 + 20
    return sx + tip[0], sy + tip[1]


def draw_arm(draw, pose, side, tip):
    """팔을 어깨에서 tip까지 뻗고, 끝에 주먹을 둔다. side: -1=뒤쪽, 1=앞쪽."""
    cx, y0, y1, hw = body_geom(pose)
    sx = cx + side * (hw - 1)
    sy = y0 + 20
    tx, ty = sx + tip[0], sy + tip[1]
    limb(draw, sx, sy, tx, ty, YELLOW, width=4)
    ellipse(draw, tx, ty, 2, 2, fill=YELLOW, outline=OUTLINE)
    return draw


def draw_spark(draw, pose):
    """공격 타격점에 위로 뻗은 반짝임 세 가지를 그린다."""
    sx, sy = arm_tip(pose, 1, pose['arm_front'])
    for dx, dy in ((-2, -4), (0, -5), (2, -4)):
        draw.line([sx, sy, sx + dx, sy + dy], fill=SPARK)
    return draw


def draw_foot(draw, pose, offset):
    """다리와 검은 신발을 그린다. offset: 발 중심의 (dx, dy)."""
    cx, y0, y1, hw = body_geom(pose)
    x = cx + offset[0]
    foot_y = GROUND - 4 - pose['leg'] + offset[1]
    if foot_y > y1:
        limb(draw, x, y1 - 1, x, foot_y + 1, YELLOW, width=3)
    draw.rounded_rectangle([x - 3, foot_y, x + 3, foot_y + 4],
                           radius=1, fill=SHOE, outline=OUTLINE)
    draw.rounded_rectangle([x - 3, foot_y, x + 3, foot_y + 1],
                           radius=1, fill=SHOE_DARK)
    return draw


def make_frame(**overrides):
    """자세 정보를 받아 200x200 한 셀짜리 프레임을 만든다."""
    pose = default_pose(**overrides)

    frame = new_frame()
    draw = ImageDraw.Draw(frame)
    draw_arm(draw, pose, -1, pose['arm_back'])

    draw_body(frame, pose)
    draw_overalls(frame, pose)
    draw_face(frame, pose)
    draw_hair(frame, pose)

    draw = ImageDraw.Draw(frame)
    draw_arm(draw, pose, 1, pose['arm_front'])
    draw_foot(draw, pose, pose['foot_back'])
    draw_foot(draw, pose, pose['foot_front'])
    if pose['spark']:
        draw_spark(draw, pose)

    return to_cell(frame)


def idle_frames():
    """0번 행: 가만히 서서 살짝 숨 쉬고 가끔 눈을 깜빡인다."""
    bob = [0, 0, -1, -1, 0, 0, 0, 0]
    return [make_frame(
        body_dy=bob[i],
        arm_front=(4, 5 + bob[i] // 2),
        arm_back=(-4, 5 + bob[i] // 2),
        eye='blink' if i == 5 else 'open',
        mouth='smile',
    ) for i in range(COLS)]


def gait_pose(phase, swing, lift, bob, lean, mouth='smile'):
    """걷기/뛰기 공통 자세 계산.

    phase: 0~2*pi. swing: 발이 앞뒤로 흔들리는 폭, lift: 발이 뜨는 높이,
    bob: 몸이 위아래로 출렁이는 폭, lean: 몸이 기울어지는 양.
    """
    front = math.sin(phase)
    back = math.sin(phase + math.pi)
    return dict(
        body_dy=-int(round(bob * abs(math.sin(phase * 2)))),
        lean=lean,
        foot_front=(int(round(front * swing)),
                    -int(round(max(0.0, front) * lift))),
        foot_back=(int(round(back * swing)),
                   -int(round(max(0.0, back) * lift))),
        arm_front=(int(round(back * swing)), 4 - int(round(front))),
        arm_back=(int(round(front * swing)), 4 - int(round(back))),
        hair_sway=int(round(front * 1)),
        eye='open',
        mouth=mouth,
    )


def walk_frames():
    """1번 행: 걷기. 다리는 번갈아 어끼고 몸은 두 번 출렁인다."""
    return [make_frame(**gait_pose(i / COLS * 2 * math.pi, 5, 2, 1, 0))
            for i in range(COLS)]


def run_frames():
    """2번 행: 뛰기. 보폭과 팔 흔들림을 키우고 앞으로 기울이며 헐떡인다."""
    frames = []
    for i in range(COLS):
        pose = gait_pose(i / COLS * 2 * math.pi, 7, 4, 2, 2, mouth='open')
        pose['hair_sway'] -= 2
        frames.append(make_frame(**pose))
    return frames


def jump_frames():
    """3번 행: 점프. 웅크려 힘내고 올라갔다가 떨어지고 착지한다."""
    body = [0, -1, -3, -5, -6, -4, -1, 0]
    leg = [0, 0, 2, 3, 3, 2, 0, 0]
    arm_f = [(2, 5), (1, 3), (0, -1), (-1, -4), (-1, -4), (0, -1), (1, 3), (2, 5)]
    arm_b = [(-v[0], v[1]) for v in arm_f]
    foot_f = [(3, 0), (3, 0), (1, -1), (0, -2), (0, -2), (1, -1), (3, 0), (3, 0)]
    foot_b = [(-v[0], v[1]) for v in foot_f]
    mouth = ['flat', 'open', 'open', 'open', 'open', 'open', 'flat', 'flat']
    return [make_frame(body_dy=body[i], leg=leg[i],
                       arm_front=arm_f[i], arm_back=arm_b[i],
                       foot_front=foot_f[i], foot_back=foot_b[i],
                       hair_sway=body[i] // 2, mouth=mouth[i])
            for i in range(COLS)]


def attack_frames():
    """4번 행: 공격. 주먹을 거두고 앞으로 내리친 뒤 자세를 되돌린다."""
    body = [0, 0, -1, -2, -1, 0, 0, 0]
    lean = [0, -1, 1, 2, 1, 0, 0, 0]
    arm_f = [(-2, 2), (-4, 0), (9, -1), (9, -1), (7, 0), (4, 3), (2, 5), (4, 5)]
    arm_b = [(-4, 5), (-6, 4), (-4, 5), (-3, 5), (-4, 5), (-4, 5), (-4, 5), (-4, 5)]
    foot_f = [(4, 0), (4, 0), (6, 0), (7, 0), (6, 0), (5, 0), (4, 0), (4, 0)]
    foot_b = [(-4, 0), (-5, 0), (-4, 0), (-3, 0), (-4, 0), (-4, 0), (-4, 0), (-4, 0)]
    eye = ['open', 'angry', 'angry', 'angry', 'angry', 'open', 'open', 'open']
    mouth = ['flat', 'open', 'open', 'open', 'flat', 'flat', 'smile', 'smile']
    return [make_frame(body_dy=body[i], lean=lean[i],
                       arm_front=arm_f[i], arm_back=arm_b[i],
                       foot_front=foot_f[i], foot_back=foot_b[i],
                       eye=eye[i], brow=eye[i] == 'angry', mouth=mouth[i],
                       spark=i in (2, 3))
            for i in range(COLS)]


# 시트에 들어갈 애니메이션 순서(행 순서). animation_viewer.py의 ANIMATIONS와 순서를 맞춘다.
ANIMATIONS = [
    ('idle', idle_frames),
    ('walk', walk_frames),
    ('run', run_frames),
    ('jump', jump_frames),
    ('attack', attack_frames),
]

SHEET_FILE = 'minion_sheet.png'


def build_sheet():
    """5종 애니메이션을 8열 x 5행 스프라이트 시트로 합친다."""
    sheet = Image.new('RGBA', (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    for row, (name, builder) in enumerate(ANIMATIONS):
        for col, frame in enumerate(builder()):
            sheet.paste(frame, (col * CELL, row * CELL))
    return sheet


def main():
    sheet = build_sheet()
    sheet.save(SHEET_FILE)
    print('%s 저장: %dx%d (%d행 x %d열, 셀 %dx%d)'
          % (SHEET_FILE, sheet.width, sheet.height, ROWS, COLS, CELL, CELL))


if __name__ == '__main__':
    main()
