# 실습 과제 진행
from pico2d import*
import math

open_canvas(800, 600)

character = load_image('character.png')

def move_circle():
    print('CIRCLE')

    for degree in range(0,360,4):
        theta = math.radians(degree)
        x = 400 + 200 * math.cos(theta)
        y = 300 + 200 * math.sin(theta)

        draw_character(x, y)
    
def move_rectangle():
    print('RECTANGLE')
    move_top()
    move_right()
    move_bottom()
    move_left()

def move_top():
    print('TOP')
    for x in range(50, 751, 5):
        draw_character(x, 550)

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.05)


def move_right():
    print('RIGHT')
    for y in range(550, 149, -5):
        draw_character(750, y)

def move_bottom():
    print('BOTTOM')
    for x in range(750, 49, -5):
        draw_character(x, 150)

def move_left():
    print('LEFT')
    for y in range(150, 551, 5):
        draw_character(50, y)


def move_triangle():
    print('TRIANGLE')
    for x in range(50, 751, 5):
        draw_character(x, 150)

    for t in range(0, 101):
        x = 750 - 350 * t / 100
        y = 150 + 400 * t / 100
        draw_character(x, y)

    for i in range(0, 101):
        x = 400 - 350 * i / 100
        y = 550 - 400 * i / 100
        draw_character(x, y)



while True:
    move_circle()
    move_rectangle()
    move_triangle()

close_canvas()
