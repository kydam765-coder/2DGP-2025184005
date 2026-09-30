from PIL import Image

CELL = 100
COLS = 8
ROWS = 4
GRID = 25
SCALE = CELL // GRID

FUR = (146, 104, 53, 255)
FUR_DARK = (120, 86, 44, 255)
BELLY = (186, 146, 92, 255)
EAR_INNER = (100, 72, 44, 255)
NOSE = (88, 58, 38, 255)
EYE = (32, 26, 20, 255)
MOUTH = (70, 46, 30, 255)
OUTLINE = (70, 50, 30, 255)


def ell(px, py, rx, ry):
    pts = set()
    for x in range(px - rx, px + rx + 1):
        for y in range(py - ry, py + ry + 1):
            if ((x - px) / rx) ** 2 + ((y - py) / ry) ** 2 <= 1:
                pts.add((x, y))
    return pts


def rect_pts(x0, x1, y0, y1):
    pts = set()
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            pts.add((x, y))
    return pts


def leg_pts(x0, c, lift, shift):
    top = c - 1
    bottom = c + 7 - lift
    x0 = x0 + round(shift)
    return rect_pts(x0, x0 + 1, top, bottom)


def capybara_frame(body_dy, head_shift, hind_lift, front_lift, hind_shift,
                   front_shift, ear_down, mouth_open):
    c = 15 + body_dy
    grid = {}

    body = ell(8, c + 1, 7, 5)
    belly = ell(8, c + 4, 5, 2)
    head = rect_pts(12 + head_shift, 21 + head_shift, c - 7, c - 1)
    head |= ell(17 + head_shift, c - 5, 5, 3)
    snout = rect_pts(20 + head_shift, 22 + head_shift, c - 6, c - 3)
    ears = ell(14 + head_shift, c - 8, 2, 2)
    ears |= ell(17 + head_shift, c - 9, 2, 2)
    inner = ell(14 + head_shift, c - 8, 1, 1)
    inner |= ell(17 + head_shift, c - 9, 1, 1)
    eye = rect_pts(17 + head_shift, 17 + head_shift, c - 5, c - 5)
    nostril = rect_pts(21 + head_shift, 21 + head_shift, c - 6, c - 5)
    mouth = rect_pts(18 + head_shift, 19 + head_shift, c - 1, c - 1)

    for p in body:
        grid[p] = FUR
    for p in belly:
        grid[p] = BELLY
    for p in ears:
        grid[p] = EAR_INNER
    for p in inner:
        grid[p] = EAR_INNER
    for p in head:
        grid[p] = FUR
    for p in snout:
        grid[p] = OUTLINE
    for p in nostril:
        grid[p] = MOUTH
    for p in eye:
        grid[p] = EYE
    if mouth_open:
        for p in mouth:
            grid[p] = MOUTH

    hind = leg_pts(4, c, hind_lift, hind_shift)
    front = leg_pts(11, c, front_lift, front_shift)
    for p in hind:
        grid.setdefault(p, FUR_DARK)
    for p in front:
        grid.setdefault(p, FUR)

    if ear_down:
        for p in ell(14 + head_shift, c - 6, 2, 1):
            grid[p] = FUR

    img = Image.new('RGBA', (GRID, GRID), (0, 0, 0, 0))
    for (x, y), color in grid.items():
        if 0 <= x < GRID and 0 <= y < GRID:
            img.putpixel((x, y), color)
    return img.resize((CELL, CELL), Image.NEAREST)


def walk_frames():
    hind_lift = [0, 0, 0, 1, 2, 3, 2, 1]
    front_lift = [3, 2, 1, 0, 0, 0, 1, 2]
    hind_shift = [0, 1, 1, 1, 0, -1, -1, -1]
    front_shift = [-1, -1, -1, 0, 0, 1, 1, 1]
    frames = []
    for i in range(COLS):
        frames.append(capybara_frame(
            body_dy=0, head_shift=0,
            hind_lift=hind_lift[i], front_lift=front_lift[i],
            hind_shift=hind_shift[i], front_shift=front_shift[i],
            ear_down=False, mouth_open=False))
    return frames


def run_frames():
    hind_lift = [0, 1, 2, 3, 3, 2, 1, 0]
    front_lift = [3, 2, 1, 0, 0, 1, 2, 3]
    hind_shift = [1, 2, 1, 0, -2, -1, 0, 2]
    front_shift = [-2, -1, 0, 1, 2, 1, 0, -1]
    frames = []
    for i in range(COLS):
        frames.append(capybara_frame(
            body_dy=0, head_shift=1,
            hind_lift=hind_lift[i], front_lift=front_lift[i],
            hind_shift=hind_shift[i], front_shift=front_shift[i],
            ear_down=True, mouth_open=False))
    return frames


def jump_frames():
    arc = [0, -1, -2, -3, -4, -3, -2, -1]
    head_shift = [0, 0, 1, 2, 1, 1, 2, 1]
    frames = []
    for i in range(COLS):
        up = arc[i]
        frames.append(capybara_frame(
            body_dy=up, head_shift=head_shift[i],
            hind_lift=3 if up else 1, front_lift=3 if up else 1,
            hind_shift=1 if i % 2 else 0, front_shift=0 if i % 2 else 1,
            ear_down=False, mouth_open=False))
    return frames


def attack_frames():
    thrust = [0, 1, 2, 3, 4, 4, 3, 2]
    body_dy = [0, 0, 0, 0, 0, -1, -1, -1]
    frames = []
    for i in range(COLS):
        t = thrust[i]
        frames.append(capybara_frame(
            body_dy=body_dy[i], head_shift=t,
            hind_lift=0, front_lift=0,
            hind_shift=-1 if t > 2 else 0, front_shift=min(1, t // 3),
            ear_down=t > 1, mouth_open=t > 2))
    return frames


def main():
    anims = [walk_frames(), run_frames(), jump_frames(), attack_frames()]
    sheet = Image.new('RGBA', (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    for r, frames in enumerate(anims):
        for c, frame in enumerate(frames):
            sheet.paste(frame, (c * CELL, r * CELL))
    sheet.save('capybara_sheet.png')


if __name__ == '__main__':
    main()