"""미니언 스프라이트 시트 애니메이션 뷰어.

minion_sheet.png(8열 x 5행, 셀 200x200)의 각 행에 담긴 애니메이션을
화면 중앙에서 큰 크기로 재생한다.

- 5종(idle / walk / run / jump / attack)을 차례로 무한 반복한다.
- 각 애니메이션은 5회 반복한 뒤 1초 동안 멈춘다.
- 캐릭터는 3배 확대해 화면의 절반 이상을 차지한다.

실행: python animation_viewer.py
(스프라이트 시트와 라벨은 make_minion_sheet.py, make_labels.py로 만든다)
"""

import os

import pico2d

# 스프라이트 시트 규격
SHEET_FILE = 'minion_sheet.png'
FRAME_SIZE = 200      # 한 셀(프레임)의 픽셀 크기
FRAMES_PER_ROW = 8    # 한 행에 들어가는 프레임 수
TOTAL_ROWS = 5        # 시트에 담긴 애니메이션(행) 수
LABEL_DIR = 'labels'  # make_labels.py가 만든 애니메이션 이름 이미지 폴더

# 화면 배치: 캔버스는 800x600이고, 좌표 원점은 왼쪽 아래다.
CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
CENTER_X = CANVAS_WIDTH // 2
CENTER_Y = CANVAS_HEIGHT // 2

# 3배 확대하면 600x600으로 그려져 화면 높이의 100%,
# 너비의 75%를 차지한다(실제 캐릭터가 그 안에서 약 60% x 80% 크기).
CHARACTER_SCALE = 3
CHARACTER_SIZE = FRAME_SIZE * CHARACTER_SCALE

# 화면 아래쪽에 그릴 바닥 높이와 반복 진행 막대 한 칸의 너비
GROUND_HEIGHT = 20
PROGRESS_SEGMENT = 40

# 시트의 각 행에 해당하는 애니메이션: (행 인덱스, 이름)
# make_minion_sheet.py의 ANIMATIONS 순서와 같아야 한다.
ANIMATIONS = [
    (0, 'idle'),    # 0행: 가만히 있기
    (1, 'walk'),    # 1행: 걷기
    (2, 'run'),     # 2행: 뛰기
    (3, 'jump'),    # 3행: 점프
    (4, 'attack'),  # 4행: 공격
]

# 재생 설정: 애니메이션 하나를 5회 반복한 뒤 1초 동안 멈춘다.
REPEAT_COUNT = 5
PAUSE_SECONDS = 1.0
FRAME_DELAY = 0.08

if not os.path.exists(SHEET_FILE):
    raise SystemExit('%s 이(가) 없습니다. python make_minion_sheet.py 를 먼저 실행하세요.'
                     % SHEET_FILE)

pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
sheet = pico2d.load_image(SHEET_FILE)

# 재생 중인 애니메이션 이름을 표시할 라벨 이미지(없으면 표시하지 않는다)
labels = {}
for row, name in ANIMATIONS:
    label_path = os.path.join(LABEL_DIR, name + '.png')
    if os.path.exists(label_path):
        labels[name] = pico2d.load_image(label_path)


def draw_ground():
    """화면 맨 아래에 바닥을 그린다."""
    pico2d.draw_rectangle(0, 0, CANVAS_WIDTH, GROUND_HEIGHT,
                          118, 158, 110, filled=True)


def draw_character(row, frame):
    """시트의 (row행, frame번째) 셀을 화면 중앙에 확대해서 그린다.

    pico2d는 이미지를 자를 때도 아래쪽을 기준으로 좌표를 받으므로
    맨 위 행(0행)은 bottom = (전체 행 수 - 1 - row) * FRAME_SIZE 이다.
    """
    sheet.clip_draw(frame * FRAME_SIZE,
                    (TOTAL_ROWS - 1 - row) * FRAME_SIZE,
                    FRAME_SIZE, FRAME_SIZE,
                    CENTER_X, CENTER_Y,
                    CHARACTER_SIZE, CHARACTER_SIZE)


def draw_hud(name, repeat):
    """화면 위에는 애니메이션 이름, 아래에는 5회 반복 진행 막대를 그린다."""
    if name in labels:
        labels[name].draw(CENTER_X, CANVAS_HEIGHT - 48)
    start_x = CENTER_X - (REPEAT_COUNT * PROGRESS_SEGMENT) // 2
    for i in range(REPEAT_COUNT):
        x = start_x + i * PROGRESS_SEGMENT
        r, g, b = (255, 210, 40) if i <= repeat else (92, 122, 92)
        pico2d.draw_rectangle(x, 6, x + PROGRESS_SEGMENT - 14, 14,
                              r, g, b, filled=True)


def draw_frame(row, frame, name='', repeat=0):
    """한 프레임을 완성해 화면에 그린다(바닥 -> 캐릭터 -> 안내 표시)."""
    pico2d.clear_canvas()
    draw_ground()
    draw_character(row, frame)
    draw_hud(name, repeat)
    pico2d.update_canvas()


# 5종 애니메이션을 순서대로 무한 반복한다.
while True:
    for row, name in ANIMATIONS:
        for repeat in range(REPEAT_COUNT):
            for frame in range(FRAMES_PER_ROW):
                draw_frame(row, frame, name, repeat)
                pico2d.delay(FRAME_DELAY)
        pico2d.delay(PAUSE_SECONDS)

pico2d.close_canvas()
