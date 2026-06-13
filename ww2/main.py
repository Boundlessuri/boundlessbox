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
        small = pygame.font.SysFont("Microsoft YaHei", 18)
    except:
        title = pygame.font.Font(None, 48)
        btn = pygame.font.Font(None, 28)
        desc = pygame.font.Font(None, 18)
        large = pygame.font.Font(None, 48)
        med = pygame.font.Font(None, 24)
        small = pygame.font.Font(None, 16)
    return title, btn, desc, large, med, small


def show_help_screen(screen):
    """Display game instructions / help screen."""
    screen.fill(DARK_GRAY)
    ft, fb, fd, fl, fm, fs = get_fonts()

    title = ft.render("游戏说明", True, YELLOW)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 20))

    help_text = [
        ("一、游戏概述", [
            "本游戏为二战题材的六角格回合制战役级战棋。",
            "指挥一个国家的军队，占领胜利点(VPs)以取得胜利。",
            "7个可选阵营：德国、苏联、美国、英国、法国、日本、中国。",
        ]),
        ("二、基本操作", [
            "左键点击己方单位 → 选中 (显示绿色移动范围 + 红色可攻击目标)",
            "左键绿色格子 → 移动单位",
            "左键红色敌方单位 → 发起攻击",
            "右键拖拽 → 平移地图",
            "结束回合 → AI 自动执行，下一回合开始",
        ]),
        ("三、单位属性", [
            "每个兵牌显示: 攻击力 (左) / 防御力 (右)",
            "每个单位有 2 步兵力，损1步后属性减半",
            "黄色斜线 = 兵力受损",
            "红色圆点 = 已行动完毕",
        ]),
        ("四、战斗系统", [
            "战斗使用 1d6 (六面骰子) + 修正值判定。",
            "兵力比 ≥ 3:1 → 大概率歼灭防御方",
            "兵力比 ≥ 2:1 → 可能歼灭或击退",
            "兵力比 = 1:1 → 可能交换损失或击退",
            "兵力比 ≤ 1:2 → 进攻方危险",
            "",
            "修正值:",
            "  +1 包围 (防御方邻接4格被占)",
            "  -1 防御方在城市/山地",
        ]),
        ("五、地形效果", [
            "平原: 移1 防+0 | 森林: 移2 防+1 | 丘陵: 移2 防+2",
            "山地: 移3 防+3 | 城市: 移1 防+3 | 海洋/河流: 不可通行",
        ]),
        ("六、胜利条件", [
            "回合结束时，将己方单位移动到胜利点(黄圈)即可占领。",
            "达到最大回合数后，VP多的一方获胜。",
            "消灭敌方所有单位也可立即获胜。",
        ]),
    ]

    y = 75
    panel_x = 30
    max_w = screen.get_width() - 60

    for section_title, lines in help_text:
        txt = fm.render(section_title, True, ORANGE)
        screen.blit(txt, (panel_x, y))
        y += 28
        for line in lines:
            color = WHITE if not line.startswith(" ") else GRAY
            txt = fs.render(line, True, color)
            screen.blit(txt, (panel_x + 15, y))
            y += 20
        y += 8

    # Back button
    btn_rect = pygame.Rect(screen.get_width() // 2 - 100, screen.get_height() - 60, 200, 40)
    pygame.draw.rect(screen, BUTTON_BG, btn_rect, border_radius=6)
    txt = fb.render("返回主菜单", True, WHITE)
    screen.blit(txt, (btn_rect.x + (btn_rect.w - txt.get_width()) // 2,
                      btn_rect.y + (btn_rect.h - txt.get_height()) // 2))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.collidepoint(event.pos):
                    return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        pygame.time.wait(30)


def show_menu_screen(screen):
    screen.fill(DARK_GRAY)
    ft, fb, fd, _, _, _ = get_fonts()

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

    y += 5
    # Help button
    help_rect = pygame.Rect(screen.get_width() // 2 - 80, y, 160, 38)
    buttons.append((help_rect, "__help__"))
    pygame.draw.rect(screen, (80, 80, 60), help_rect, border_radius=6)
    txt = fb.render("游戏说明", True, YELLOW)
    screen.blit(txt, (help_rect.x + (help_rect.w - txt.get_width()) // 2,
                      help_rect.y + (help_rect.h - txt.get_height()) // 2))

    y += 50
    instructions = [
        "操作提示:",
        "  左键 = 选兵/移动/攻击  |  右键拖拽 = 平移地图",
        "  移动后直接点红色目标即可攻击  |  结束回合让AI行动",
    ]
    for line in instructions:
        txt = fd.render(line, True, GRAY)
        screen.blit(txt, (screen.get_width() // 2 - 250, y))
        y += 22

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, key in buttons:
                    if rect.collidepoint(event.pos):
                        if key == "__help__":
                            if not show_help_screen(screen):
                                return None
                            # Redraw menu
                            return show_menu_screen(screen)
                        return key
        pygame.time.wait(30)


def show_game_over(screen, game_state):
    screen.fill(DARK_GRAY)
    fl, fm = get_fonts()[3:5]

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
                elif result == "show_help":
                    if not show_help_screen(screen):
                        running = False
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
