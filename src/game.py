import pygame
import sys
from src.constants import (
    LARGURA,
    ALTURA,
    verde,
    verde_claro,
    vermelho,
    vermelho_claro,
    azul,
    azul_claro,
    preto,
    branco,
    largura_passaro,
)
from src.assets import load_assets
from src.ui import button, text_objects
from src.entities import Bird, Obstacle, Background
from src.database import (
    save_score,
    get_scores,
    get_top_cumulative,
    get_user_data,
    buy_item,
    select_item,
)

ouro = (255, 215, 0)
prata = (192, 192, 192)
bronze = (205, 127, 50)
cinza = (90, 90, 90)

FUNDO_SCORES = (15, 15, 45)


class Game:
    """Gerencia o estado e o loop principal do jogo."""

    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Thrush Rush")
        self.clock = pygame.time.Clock()
        self.pause = False
        self.quit_to_menu = False
        self.assets = load_assets()
        pygame.display.set_icon(self.assets["bird_img"])

    # ------------------------------------------------------------------ helpers

    def _draw_text_center(self, text, size=115, y_offset=0, color=preto):
        font = pygame.font.Font("freesansbold.ttf", size)
        superficie, retangulo = text_objects(text, font)
        retangulo.center = (LARGURA // 2, ALTURA // 2 + y_offset)
        self.display.blit(superficie, retangulo)

    def _draw_score(self, count):
        font = pygame.font.SysFont(None, 100)
        text = font.render("Score: " + str(count), True, preto)
        self.display.blit(text, (0, 0))

    def _wait_mouse_release(self):
        """Aguarda o mouse ser solto para evitar click bleed-through entre telas."""
        while pygame.mouse.get_pressed()[0]:
            pygame.event.pump()
            pygame.time.wait(100)

    def _draw_hall_of_fame(self):
        top = get_top_cumulative(3)
        if not top:
            return
        medal_colors = [ouro, prata, bronze]
        labels = ["1.", "2.", "3."]
        title_font = pygame.font.Font("freesansbold.ttf", 48)
        row_font = pygame.font.Font("freesansbold.ttf", 42)

        box_surf = pygame.Surface((760, 260), pygame.SRCALPHA)
        box_surf.fill((100, 130, 160, 190))
        box_rect = box_surf.get_rect(center=(LARGURA // 2, 485))
        self.display.blit(box_surf, box_rect)

        title_surf = title_font.render("ACUMULADO GERAL", True, branco)
        self.display.blit(title_surf, title_surf.get_rect(center=(LARGURA // 2, 390)))
        for i, (username, total) in enumerate(top):
            cor = medal_colors[i]
            text = f"{labels[i]}  {username}  —  {total} pts"
            surf = row_font.render(text, True, cor)
            self.display.blit(surf, surf.get_rect(center=(LARGURA // 2, 455 + i * 58)))

    # ------------------------------------------------------------------ telas

    def get_username(self):
        username = ""
        cursor_visible = True
        cursor_timer = 0
        background = Background(self.assets["bg_img"])

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and username.strip():
                        return username.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif len(username) < 20 and event.unicode.isprintable():
                        username += event.unicode

            cursor_timer += 1
            if cursor_timer >= 30:
                cursor_visible = not cursor_visible
                cursor_timer = 0

            background.update()
            background.draw(self.display)
            self._draw_text_center("SEU NOME:", size=90, y_offset=-120, color=preto)
            cursor = "|" if cursor_visible else " "
            self._draw_text_center(username + cursor, size=80, y_offset=20, color=preto)
            hint_font = pygame.font.Font("freesansbold.ttf", 40)
            hint_surf, hint_rect = text_objects(
                "Pressione ENTER para continuar", hint_font
            )
            hint_rect.center = (LARGURA // 2, ALTURA // 2 + 160)
            self.display.blit(hint_surf, hint_rect)
            pygame.display.update()
            self.clock.tick(60)

    def game_intro(self):
        # Evita que cliques de telas anteriores (loja, crash, pausa) vazem para cá.
        self._wait_mouse_release()

        pygame.mixer.Sound.play(self.assets["title"])
        background = Background(self.assets["bg_img"])

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            background.update()
            background.draw(self.display)
            self._draw_text_center("VOA, PÁSSARO!", y_offset=-220)
            self._draw_hall_of_fame()

            if (
                button(
                    self.display,
                    "START",
                    130,
                    720,
                    370,
                    160,
                    verde,
                    verde_claro,
                    "play",
                )
                == "play"
            ):
                username = self.get_username()
                self.run(username)
                return

            if (
                button(
                    self.display,
                    "SCORES",
                    565,
                    720,
                    370,
                    160,
                    vermelho,
                    vermelho_claro,
                    "scores",
                )
                == "scores"
            ):
                self.show_scores()

            if (
                button(
                    self.display,
                    "LOJA",
                    1000,
                    720,
                    370,
                    160,
                    ouro,
                    (255, 255, 100),
                    "shop",
                )
                == "shop"
            ):
                username = self.get_username()
                self._wait_mouse_release()
                self.show_shop(username)

            pygame.display.update()
            self.clock.tick(15)

    def show_shop(self, username):
        skins = [
            {
                "id": "bird_img",
                "name": "Pássaro Clássico",
                "price": 0,
                "desc": "Visual clássico do passarinho",
            },
            {
                "id": "skin_orange",
                "name": "Pássaro Trump",
                "price": 10,
                "desc": "Laranjão",
            },
            {
                "id": "ghost_bird",
                "name": "Pássaro Fantasma",
                "price": 5,
                "desc": "Transparente e assustador",
            },
            {
                "id": "skin_gold",
                "name": "Pássaro Dourado",
                "price": 15,
                "desc": "golde",
            },
            {
                "id": "skin_crow",
                "name": "Corvo Sombrio",
                "price": 25,
                "desc": "Corvão",
            },
            {
                "id": "skin_bard",
                "name": "Pássaro das Nuvens",
                "price": 1500,
                "desc": "Chapéu verde e alaúde",
            },
        ]
        backgrounds = [
            {"id": "bg_img", "name": "Planície Pixel", "price": 0},
            {"id": "bg_night", "name": "Noite Mística", "price": 10},
            {"id": "bg_space", "name": "Vácuo Arcano", "price": 50},
        ]

        current_tab = "skin"
        METAL_DOURADO = (212, 175, 55)
        AZUL_PETROLEO = (0, 128, 128)
        AZUL_ESCURO = (10, 30, 60)
        BRILHO_OURO = (255, 223, 0)

        while True:
            user_data = get_user_data(username)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            bg_loop = Background(
                self.assets.get(user_data["bg"], self.assets["bg_img"]), speed=1
            )
            bg_loop.draw(self.display)

            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((10, 10, 30, 160))
            self.display.blit(overlay, (0, 0))

            pygame.draw.rect(
                self.display,
                METAL_DOURADO,
                (LARGURA // 2 - 400, 20, 800, 100),
                border_radius=10,
            )
            pygame.draw.rect(
                self.display,
                AZUL_PETROLEO,
                (LARGURA // 2 - 390, 30, 780, 80),
                border_radius=8,
            )
            self._draw_text_center("LOJA", size=60, y_offset=-430, color=BRILHO_OURO)

            gold_rect = pygame.Rect(LARGURA - 350, 35, 320, 70)
            pygame.draw.rect(self.display, METAL_DOURADO, gold_rect, border_radius=15)
            pygame.draw.rect(
                self.display, AZUL_ESCURO, gold_rect.inflate(-6, -6), border_radius=12
            )
            gold_font = pygame.font.Font("freesansbold.ttf", 35)
            gold_text = gold_font.render(f"OURO: {user_data['moedas']}", True, branco)
            self.display.blit(gold_text, (LARGURA - 320, 50))

            s_color = BRILHO_OURO if current_tab == "skin" else AZUL_ESCURO
            if (
                button(
                    self.display,
                    "PERSONAGENS",
                    350,
                    140,
                    370,
                    80,
                    s_color,
                    METAL_DOURADO,
                    "t_skin",
                )
                == "t_skin"
            ):
                current_tab = "skin"

            b_color = BRILHO_OURO if current_tab == "bg" else AZUL_ESCURO
            if (
                button(
                    self.display,
                    "CENÁRIOS",
                    780,
                    140,
                    370,
                    80,
                    b_color,
                    METAL_DOURADO,
                    "t_bg",
                )
                == "t_bg"
            ):
                current_tab = "bg"

            items = skins if current_tab == "skin" else backgrounds
            for i, item in enumerate(items):
                col = i % 3
                row = i // 3
                x = 130 + (col * 430)
                y = 250 + (row * 280)

                panel_rect = pygame.Rect(x, y, 380, 250)
                pygame.draw.rect(
                    self.display, METAL_DOURADO, panel_rect, border_radius=10
                )
                pygame.draw.rect(
                    self.display,
                    AZUL_ESCURO,
                    panel_rect.inflate(-8, -8),
                    border_radius=8,
                )

                item_img = self.assets.get(item["id"], self.assets["bird_img"])
                thumb_img = pygame.transform.scale(item_img, (80, 80))
                self.display.blit(thumb_img, (x + 20, y + 20))

                name_f = pygame.font.Font("freesansbold.ttf", 24)
                name_s = name_f.render(item["name"], True, BRILHO_OURO)
                self.display.blit(name_s, (x + 115, y + 45))

                is_owned = item["id"] in user_data["owned"] or item.get("price", 0) == 0
                is_equipped = (
                    user_data["skin"] == item["id"]
                    if current_tab == "skin"
                    else user_data["bg"] == item["id"]
                )

                btn_y = y + 150
                if is_equipped:
                    button(
                        self.display, "EQUIPADO", x + 40, btn_y, 300, 70, cinza, cinza
                    )
                elif is_owned:
                    if (
                        button(
                            self.display,
                            "EQUIPAR",
                            x + 40,
                            btn_y,
                            300,
                            70,
                            AZUL_PETROLEO,
                            METAL_DOURADO,
                            "sel",
                        )
                        == "sel"
                    ):
                        select_item(username, item["id"], current_tab)
                else:
                    price_t = f"{item['price']} OURO"
                    if (
                        button(
                            self.display,
                            price_t,
                            x + 40,
                            btn_y,
                            300,
                            70,
                            METAL_DOURADO,
                            BRILHO_OURO,
                            "buy",
                        )
                        == "buy"
                    ):
                        buy_item(username, item["id"], current_tab, item["price"])

            if (
                button(
                    self.display,
                    "VOLTAR PARA O MENU",
                    LARGURA // 2 - 300,
                    850,
                    600,
                    100,
                    vermelho,
                    vermelho_claro,
                    "back",
                )
                == "back"
            ):
                return

            pygame.display.update()
            self.clock.tick(30)

    def show_scores(self):
        page = 0
        per_page = 8

        while True:
            rows, total = get_scores(page, per_page)
            total_pages = max(1, (total + per_page - 1) // per_page)
            has_prev = page > 0
            has_next = page < total_pages - 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        return
                    elif event.key == pygame.K_LEFT and has_prev:
                        page -= 1
                    elif event.key == pygame.K_RIGHT and has_next:
                        page += 1

            self.display.fill(FUNDO_SCORES)

            title_font = pygame.font.Font("freesansbold.ttf", 90)
            t_surf, t_rect = text_objects("PLACAR", title_font)
            t_rect.center = (LARGURA // 2, 75)
            self.display.blit(t_surf, t_rect)

            info_font = pygame.font.Font("freesansbold.ttf", 38)
            i_surf = info_font.render(
                f"Página {page + 1} de {total_pages}   •   {total} partidas",
                True,
                prata,
            )
            self.display.blit(i_surf, i_surf.get_rect(center=(LARGURA // 2, 148)))

            col_font = pygame.font.Font("freesansbold.ttf", 40)
            for label, x in [
                ("#", 80),
                ("JOGADOR", 240),
                ("PONTOS", 820),
                ("DATA", 1120),
            ]:
                self.display.blit(col_font.render(label, True, verde), (x, 195))
            pygame.draw.line(self.display, branco, (60, 242), (1440, 242), 1)

            row_font = pygame.font.Font("freesansbold.ttf", 38)
            for i, (username, timestamp, pontos) in enumerate(rows):
                global_rank = page * per_page + i
                cor = (
                    ouro
                    if global_rank == 0
                    else (
                        prata
                        if global_rank == 1
                        else bronze if global_rank == 2 else branco
                    )
                )
                y = 258 + i * 72
                self.display.blit(
                    row_font.render(str(global_rank + 1), True, cor), (80, y)
                )
                self.display.blit(row_font.render(username, True, cor), (240, y))
                self.display.blit(row_font.render(str(pontos), True, cor), (820, y))
                self.display.blit(row_font.render(timestamp[:10], True, cor), (1120, y))

            ic_p = azul if has_prev else cinza
            if (
                button(
                    self.display,
                    "< ANTERIOR",
                    80,
                    865,
                    350,
                    90,
                    ic_p,
                    azul_claro if has_prev else cinza,
                    "prev",
                )
                == "prev"
                and has_prev
            ):
                page -= 1

            if (
                button(
                    self.display,
                    "VOLTAR",
                    575,
                    865,
                    350,
                    90,
                    verde,
                    verde_claro,
                    "back",
                )
                == "back"
            ):
                return

            ic_n = azul if has_next else cinza
            if (
                button(
                    self.display,
                    "PROXIMA >",
                    1070,
                    865,
                    350,
                    90,
                    ic_n,
                    azul_claro if has_next else cinza,
                    "next",
                )
                == "next"
                and has_next
            ):
                page += 1

            pygame.display.update()
            self.clock.tick(30)

    def crash(self, username, pontos):
        save_score(username, pontos)
        pygame.mixer.Sound.play(self.assets["crash_sound"])
        self._draw_text_center("VOCÊ BATEU")

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if (
                button(
                    self.display,
                    "DE NOVO",
                    155,
                    700,
                    400,
                    200,
                    verde,
                    verde_claro,
                    "main",
                )
                == "main"
            ):
                self.run(username)
                return

            if (
                button(
                    self.display,
                    "SAIR",
                    955,
                    700,
                    400,
                    200,
                    vermelho,
                    vermelho_claro,
                    "menu",
                )
                == "menu"
            ):
                pygame.mixer.music.stop()
                self.game_intro()
                return

            pygame.display.update()
            self.clock.tick(15)

    def paused(self):
        while self.pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self._draw_text_center("PAUSADO")

            if (
                button(
                    self.display,
                    "CONTINUAR",
                    155,
                    700,
                    400,
                    200,
                    verde,
                    verde_claro,
                    "unpause",
                )
                == "unpause"
            ):
                self.pause = False

            if (
                button(
                    self.display,
                    "SAIR",
                    955,
                    700,
                    400,
                    200,
                    vermelho,
                    vermelho_claro,
                    "menu",
                )
                == "menu"
            ):
                self.pause = False
                self.quit_to_menu = True
                return

            pygame.display.update()
            self.clock.tick(15)

    # ------------------------------------------------------------------ loop principal

    def run(self, username):
        pygame.mixer.Sound.stop(self.assets["title"])
        pygame.mixer.music.play(-1)

        user_data = get_user_data(username)
        skin_img = self.assets.get(
            user_data.get("skin", "bird_img"), self.assets["bird_img"]
        )
        bg_img = self.assets.get(user_data.get("bg", "bg_img"), self.assets["bg_img"])

        background = Background(bg_img)
        bird = Bird(x=LARGURA * 0.40, y=ALTURA * 0.70, image=skin_img)
        obstacle = Obstacle()
        dodged = 0

        while True:
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.pause = True
                    self.paused()
                    if self.quit_to_menu:
                        self.quit_to_menu = False
                        pygame.mixer.music.stop()
                        self.game_intro()
                        return

            if keys[pygame.K_LEFT]:
                bird.move_left()
            elif keys[pygame.K_RIGHT]:
                bird.move_right()

            background.update()
            background.draw(self.display)
            obstacle.draw(self.display)
            obstacle.move()
            bird.draw(self.display)
            self._draw_score(dodged)

            if bird.x > LARGURA - largura_passaro or bird.x < 0:
                self.crash(username, dodged)
                return

            if obstacle.is_off_screen():
                obstacle.reset()
                dodged += 1
                pygame.mixer.Sound.play(self.assets["swoosh"])
                obstacle.speed += 0.3
                if dodged in range(10, 20):
                    obstacle.width += dodged * 1
                if dodged > 40:
                    obstacle.width = 50

            if obstacle.collides_with(bird):
                self.crash(username, dodged)
                return

            pygame.display.update()
            self.clock.tick(60)
            print(self.clock.get_fps())
