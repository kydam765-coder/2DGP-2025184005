"""미니언 스프라이트 시트 애니메이션 뷰어.

minion_sheet.png(8열 x 5행, 셀 200x200)의 각 행에 담긴 애니메이션을
화면 중앙에서 큰 크기로 재생한다.

- 5종(idle / walk / run / jump / attack)을 차례로 무한 반복한다.
- 각 애니메이션은 5회 반복한 뒤 1초 동안 멈춘다.
- 캐릭터는 3배 확대해 화면의 절반 이상을 차지한다.
"""

import pico2d

# 스프라이트 시트 규격
SHEET_FILE = 'minion_sheet.png'
FRAME_SIZE = 200     # 한 셀(프레임)의 픽셀 크기
FRAMES_PER_ROW = 8   # 한 행에 들어가는 프레임 수
TOTAL_ROWS = 5       # 시트에 담긴 애니메이션(행) 수

pico2d.open_canvas(800, 600)
sheet = pico2d.load_image(SHEET_FILE)
