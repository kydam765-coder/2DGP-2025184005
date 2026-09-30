import math
import random

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

pico2d.close_canvas()