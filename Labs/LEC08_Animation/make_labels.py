"""애니메이션 이름 라벨 이미지 생성기.

animation_viewer.py가 화면에 애니메이션 이름을 표시할 수 있도록
labels/ 폴더에 이름별 PNG를 만들어 둔다. (한글 폰트가 없으면 건너뛴다)
"""

from PIL import Image, ImageDraw, ImageFont
import os

LABEL_DIR = 'labels'
LABEL_SIZE = (280, 72)
FONT_PATH = 'C:/Windows/Fonts/malgunbd.ttf'
FONT_SIZE = 40
FILL = (255, 255, 255, 255)
STROKE = (24, 24, 32, 255)
STROKE_WIDTH = 2
PLATE = (26, 30, 44, 200)   # 반투명 배경판
PLATE_EDGE = (255, 214, 64, 255)  # 배경판 테두리(미니언 노란색)
PLATE_MARGIN = 5             # 화면 바깥 여백
PLATE_RADIUS = 18            # 배경판 모서리 둥글림

NAMES = [
    ('idle', '가만히 있기'),
    ('walk', '걷기'),
    ('run', '뛰기'),
    ('jump', '점프'),
    ('attack', '공격'),
]


def load_font():
    try:
        return ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        print('폰트를 찾을 수 없어 라벨을 만들지 않습니다: %s' % FONT_PATH)
        return None


def make_label(text, font):
    """둥근 배경판 위에 흰 글씨를 가운데 정렬로 그은 라벨 이미지를 만든다."""
    image = Image.new('RGBA', LABEL_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width, height = LABEL_SIZE
    draw.rounded_rectangle(
        [PLATE_MARGIN, PLATE_MARGIN, width - PLATE_MARGIN, height - PLATE_MARGIN],
        radius=PLATE_RADIUS, fill=PLATE, outline=PLATE_EDGE, width=2)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font,
                                            stroke_width=STROKE_WIDTH)
    x = (width - (right - left)) / 2 - left
    y = (height - (bottom - top)) / 2 - top
    draw.text((x, y), text, font=font, fill=FILL,
              stroke_width=STROKE_WIDTH, stroke_fill=STROKE)
    return image


def main():
    font = load_font()
    if font is None:
        return
    if not os.path.isdir(LABEL_DIR):
        os.makedirs(LABEL_DIR)
    for key, text in NAMES:
        path = os.path.join(LABEL_DIR, key + '.png')
        make_label(text, font).save(path)
        print('%s 저장' % path)


if __name__ == '__main__':
    main()
