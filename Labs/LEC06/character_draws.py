# 실습 과제 진행
from pico2d import*
import math

open_canvas(800, 600)

character = load_image('character.png')

def move_circle():
    print('CIRCLE')

    for degree in range(0,360,5):
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
    for x in range(50, 750, 5):
        draw_character(x, 550)

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.05)


def move_right():
    print('RIGHT')
    for y in range(550, 150, -5):
        draw_character(750, y)

def move_bottom():
    pass

def move_left():
    pass



def move_triangle():
    print('TRIANGLE')
    pass


while True:
    move_circle()
    move_rectangle()
    move_triangle()

close_canvas()
