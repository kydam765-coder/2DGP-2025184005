# -*- coding: utf-8 -*-
"""피코의 캠핑장 습격 — 실행 파일.

    python main.py

WASD 이동  ·  E 음식 줍기/배 위 낚시 홀드→초록 구간에서 떼기  ·  Q 낚싯배 타기·낚시터 하선  ·  X 수풀 앉기  ·  R 다시 시작  ·  ESC 종료
"""
import pico2d
from pico2d import (SDLK_a, SDLK_d, SDLK_e, SDLK_LEFT, SDLK_LSHIFT,
                    SDLK_q, SDLK_RSHIFT, SDLK_RIGHT, SDLK_r, SDLK_x,
                    SDLK_s, SDLK_DOWN, SDLK_UP, SDLK_w, SDLK_ESCAPE,
                    SDL_KEYDOWN, SDL_KEYUP, SDL_QUIT, close_canvas,
                    get_events, get_time, hide_lattice, open_canvas,
                    update_canvas)

from game import Game

KEYMAP = {
    SDLK_a: "left", SDLK_LEFT: "left",
    SDLK_d: "right", SDLK_RIGHT: "right",
    SDLK_w: "up", SDLK_UP: "up",
    SDLK_s: "down", SDLK_DOWN: "down",
    SDLK_e: "collect",
    SDLK_x: "sit",
    SDLK_q: "boat",
    SDLK_r: "restart",
    SDLK_LSHIFT: "sprint", SDLK_RSHIFT: "sprint",
}
ONESHOT = {"collect", "restart", "sit", "boat"}
# collect(E)는 음식 줍기엔 press, 낚시 게이지엔 hold 로 둘 다 필요하다.
HOLDS = {"left", "right", "up", "down", "sprint", "collect"}


def main():
    open_canvas(1280, 720)
    hide_lattice()
    game = Game()

    hold = set()
    press = set()
    running = True
    last = get_time()

    while running:
        for e in get_events():
            if e.type == SDL_QUIT:
                running = False
            elif e.type == SDL_KEYDOWN:
                if e.key == SDLK_ESCAPE:
                    running = False
                    continue
                act = KEYMAP.get(e.key)
                if act is None:
                    continue
                if act in ONESHOT:
                    press.add(act)
                if act in HOLDS:
                    hold.add(act)
            elif e.type == SDL_KEYUP:
                act = KEYMAP.get(e.key)
                if act in HOLDS:
                    hold.discard(act)

        now = get_time()
        dt = min(0.05, max(0.0, now - last))
        last = now

        game.update(dt, hold, press)
        game.render()
        update_canvas()
        press.clear()

    close_canvas()


if __name__ == "__main__":
    main()
