import math
from pico2d import *

open_canvas()

MOVE_STEP = 5
DRAW_DELAY = 0.02

character = load_image('character.png')

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(DRAW_DELAY)

def draw_circle():
    print('CIRCLE')
    for degree in range(0, 360, 5):
        theta = math.radians(degree)
        x = 400 + 200 * math.cos(theta)
        y = 300 + 200 * math.sin(theta)
        draw_character(x, y)

def draw_rectangle():
    print('RECTANGLE')
    move_top()
    move_right()
    move_bottom()
    move_left()

def move_top():
    print('TOP')
    for x in range(50, 750, 5):
        draw_character(x, 550)

def move_right():
    print('RIGHT')
    for y in range(550, 50, -5):
        draw_character(750, y)

def move_bottom():
    print('BOTTOM')
    for x in range(750, 50, -5):
        draw_character(x, 50)

def move_left():
    print('LEFT')
    for y in range(50, 550, 5):
        draw_character(50, y)

def move_line(x1, y1, x2, y2, step):
    for i in range(step + 1):
        t = i / step
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        draw_character(x, y)

def draw_triangle():
    print('TRIANGLE')
    move_line(400, 550, 50, 50, 70)
    move_line(50, 50, 750, 50, 70)
    move_line(750, 50, 400, 550, 70)

while True:
    draw_circle()
    draw_rectangle()
    draw_triangle()