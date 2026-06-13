import sys
import os
import pygame
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ww2.game.game_state import GameState
from ww2.ui.renderer import Renderer
from ww2.ui.input_handler import InputHandler
from ww2.ui.colors import *

SCENARIO_LIST = ["france1940", "barbarossa1941", "normandy1944", "pacific1942"]


def get_fonts():
    try:
        title = pygame.font.SysFont("Microsoft YaHei", 48, bold=True)
        btn = pygame.font.SysFont("Microsoft YaHei", 26)
        desc = pygame.font.SysFont("Microsoft YaHei", 16)
        large = pygame.font.SysFont("Microsoft YaHei", 48, bold=True)
        med = pygame.font.SysFont("Microsoft YaHei", 24)
    except:
        title = pygame.font.Font(None, 48)
        btn = pygame.font.Font(None, 28)
        desc = pygame.font.Font(None, 18)
        large = pygame.font.Font(None, 48)
        med = pygame.font.Font(None, 24)
    return title, btn, desc, large, med


def show_menu_screen(screen):
    screen.fill(DARK_GRAY)
    ft, fb, fd, _, _ = get_fonts()

    title = ft.render("二战战棋", True, YELLOW)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 30))

    scenario_names = {
        "france1940": "法国战役 - 1940",
        "barbarossa1941": "巴巴罗萨行动 - 1941",
        "normandy1944": "诺曼底登陆 - 1944",
        "pacific1942": "太平洋战争 - 1942",
    }

    buttons = []
    y = 110
    for key in SCENARIO_LIST:
        rect = pygame.Rect(screen.get_width() // 2 - 180, y, 360, 45)
        buttons.append((rect, key))
        pygame.draw.rect(screen, BUTTON_BG, rect, border_radius=6)
        txt = fb.render(scenario_names[key], True, WHITE)
        screen.blit(txt, (rect.x + 20, rect.y + 10))
        y += 55

    y += 15
    instructions = [
        "操作说明:",
        "  鼠标左键 - 选择单位 / 移动 / 攻击",
        "  鼠标右键拖拽 - 平移地图",
        "  结束阶段 - 从移动切换到战斗",
        "  结束回合 - 结束你的回合，AI 执行",
    ]
    for line in instructions:
        txt = fd.render(line, True, GRAY)
        screen.blit(txt, (screen.get_width() // 2 - 180, y))
        y += 22

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, key in buttons:
                    if rect.collidepoint(event.pos):
                        return key
        pygame.time.wait(30)


def show_game_over(screen, game_state):
    screen.fill(DARK_GRAY)
    fl, fm = get_fonts()[3:]

    p_vp = game_state.player_vp
    a_vp = game_state.ai_vp
    if p_vp > a_vp:
        result = "胜 利 !"
        color = GREEN
    elif p_vp < a_vp:
        result = "战 败"
        color = RED
    else:
        result = "平 局"
        color = YELLOW

    txt = fl.render(result, True, color)
    screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, 100))

    txt = fm.render(f"我方得分: {p_vp}  |  敌方得分: {a_vp}", True, WHITE)
    screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, 180))

    txt = fm.render(f"总回合数: {game_state.turn_number}", True, GRAY)
    screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, 230))

    txt = fm.render("点击任意位置返回主菜单...", True, GRAY)
    screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, 300))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True
        pygame.time.wait(30)


def run():
    pygame.init()
    screen = pygame.display.set_mode((1200, 750))
    pygame.display.set_caption("二战战棋 - 战役级")
    clock = pygame.time.Clock()

    game_state = GameState()
    renderer = Renderer(screen)
    input_handler = InputHandler(renderer)

    running = True

    while running:
        scenario_key = show_menu_screen(screen)
        if scenario_key is None:
            break

        game_state.load_scenario(scenario_key)
        game_state.start_turn()
        game_state.check_victory()

        m = game_state.map
        map_w = m.hex_size * 1.732 * m.cols
        map_h = m.hex_size * 1.5 * m.rows
        renderer.map_offset_x = 40
        renderer.map_offset_y = (screen.get_height() - map_h) // 2

        game_running = True
        while game_running:
            dt = clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                    running = False
                    break

                result = input_handler.handle_event(event, game_state)
                if result in ("new_game", "game_over"):
                    game_running = False

            if game_state.is_game_over():
                game_state.check_victory()
                if not show_game_over(screen, game_state):
                    running = False
                game_running = False

            renderer.render(game_state)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(run())
