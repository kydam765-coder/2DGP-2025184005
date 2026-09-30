import pico2d

pico2d.open_canvas()

sheet = pico2d.load_image('animation_sheet.png')

# 스프라이트 시트는 8열 x 4행, 한 셀(프레임)은 100x100
FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAMES_PER_ROW = 8
TOTAL_ROWS = 4

# 캐릭터를 화면 중앙에 배치하고 화면 절반 이상을 차지하도록 확대
CENTER_X = 400
CENTER_Y = 300
SCALE = 5
CHARACTER_WIDTH = FRAME_WIDTH * SCALE
CHARACTER_HEIGHT = FRAME_HEIGHT * SCALE

# 4가지 애니메이션: 행 인덱스로 표현 (걷기, 달리기, 점프, 공격)
ANIMATIONS = [
    (0, '걷기'),
    (1, '달리기'),
    (2, '점프'),
    (3, '공격'),
]


def draw_frame(anim_row, frame):
    pico2d.clear_canvas()
    sheet.clip_draw(
        frame * FRAME_WIDTH, anim_row * FRAME_HEIGHT,
        FRAME_WIDTH, FRAME_HEIGHT,
        CENTER_X, CENTER_Y,
        CHARACTER_WIDTH, CHARACTER_HEIGHT
    )
    pico2d.update_canvas()


# 애니메이션 하나는 5회 반복 후 1초 정지
REPEAT_COUNT = 5
PAUSE_AFTER_ANIM = 1.0
FRAME_DELAY = 0.1

while True:
    for anim_row, anim_name in ANIMATIONS:
        for _ in range(REPEAT_COUNT):
            for frame in range(FRAMES_PER_ROW):
                draw_frame(anim_row, frame)
                pico2d.delay(FRAME_DELAY)
        pico2d.delay(PAUSE_AFTER_ANIM)

pico2d.close_canvas()