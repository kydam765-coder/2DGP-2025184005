"""애니메이션 이름 라벨 이미지 생성기.

animation_viewer.py가 화면에 애니메이션 이름을 표시할 수 있도록
labels/ 폴더에 이름별 PNG를 만들어 둔다. (한글 폰트가 없으면 건너뛴다)
"""

from PIL import Image, ImageDraw, ImageFont
import os

LABEL_DIR = 'labels'
LABEL_SIZE = (280, 72)
FONT_PATH = 'C:/Windows/Fonts/malgunbd.ttf'
FONT_SIZE = 44
FILL = (255, 255, 255, 255)
STROKE = (30, 30, 40, 255)

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
    """검은 테두리 + 흰 글씨의 가운데 정렬 라벨 이미지를 만든다."""
    image = Image.new('RGBA', LABEL_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = (LABEL_SIZE[0] - (right - left)) / 2 - left
    y = (LABEL_SIZE[1] - (bottom - top)) / 2 - top
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            draw.text((x + dx, y + dy), text, font=font, fill=STROKE)
    draw.text((x, y), text, font=font, fill=FILL)
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
