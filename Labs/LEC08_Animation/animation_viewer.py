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

pico2d.close_canvas()