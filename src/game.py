import pygame
import sys
from src.constants import (
    LARGURA, ALTURA,
    verde, verde_claro, vermelho, vermelho_claro,
    azul, azul_claro, roxo, preto, branco, largura_passaro
)
from src.assets import load_assets
from src.ui import button, text_objects
from src.entities import Bird, Obstacle, Background
from src.database import save_score, get_scores, get_top_cumulative, get_user_data, buy_item, select_item

# Cores extras
ouro   = (255, 215, 0)
prata  = (192, 192, 192)
bronze = (205, 127, 50)
cinza  = (90,  90,  90)

FUNDO_SCORES = (15, 15, 45)   # azul escuro para tela de placar


class Game:
    """Gerencia o estado e o loop principal do jogo."""

    def __init__(self):
        pygame.init()
        self.display     = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption('Thrush Rush')
        self.clock       = pygame.time.Clock()
        self.pause       = False
        self.quit_to_menu = False   # sinaliza saída da pausa para o menu
        self.assets      = load_assets()
        pygame.display.set_icon(self.assets['bird_img'])

    # ------------------------------------------------------------------ helpers

    def _draw_text_center(self, text, size=115, y_offset=0, color=preto):
        font = pygame.font.Font('freesansbold.ttf', size)
        superficie, retangulo = text_objects(text, font)
        retangulo.center = (LARGURA // 2, ALTURA // 2 + y_offset)
        self.display.blit(superficie, retangulo)

    def _draw_score(self, count):
        font = pygame.font.SysFont(None, 100)
        text = font.render('Dibrados: ' + str(count), True, verde)
        self.display.blit(text, (0, 0))

    def _draw_hall_of_fame(self):
        """Exibe top 3 por pontuação cumulativa no menu principal."""
        top = get_top_cumulative(3)
        if not top:
            return

        medal_colors = [ouro, prata, bronze]
        labels       = ["1.", "2.", "3."]

        title_font = pygame.font.Font('freesansbold.ttf', 48)
        row_font   = pygame.font.Font('freesansbold.ttf', 42)

        title_surf = title_font.render("ACUMULADO GERAL", True, branco)
        self.display.blit(title_surf, title_surf.get_rect(center=(LARGURA // 2, 390)))

        for i, (username, total) in enumerate(top):
            cor  = medal_colors[i]
            text = f"{labels[i]}  {username}  —  {total} pts"
            surf = row_font.render(text, True, cor)
            self.display.blit(surf, surf.get_rect(center=(LARGURA // 2, 455 + i * 58)))

    # ------------------------------------------------------------------ telas

    def get_username(self):
        """Tela de input do nome antes de jogar. Retorna string ao pressionar Enter."""
        username       = ""
        cursor_visible = True
        cursor_timer   = 0
        background     = Background(self.assets['bg_img'])

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
                cursor_timer   = 0

            background.update()
            background.draw(self.display)
            
            self._draw_text_center("SEU NOME:", size=90, y_offset=-120, color=preto)

            cursor = "|" if cursor_visible else " "
            self._draw_text_center(username + cursor, size=80, y_offset=20, color=preto)

            hint_font = pygame.font.Font('freesansbold.ttf', 40)
            hint_surf, hint_rect = text_objects("Pressione ENTER para continuar", hint_font)
            hint_rect.center = (LARGURA // 2, ALTURA // 2 + 160)
            self.display.blit(hint_surf, hint_rect)

            pygame.display.update()
            self.clock.tick(60)

    def game_intro(self):
        """Tela de menu inicial."""
        pygame.mixer.Sound.play(self.assets['title'])
        background = Background(self.assets['bg_img'])
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            background.update()
            background.draw(self.display)
            
            self._draw_text_center("THRUSH RUSH!", y_offset=-220)
            self._draw_hall_of_fame()

            # Botões do menu principal (Tamanho padrão 370x160)
            if button(self.display, "START",  130, 620, 370, 160, verde,   verde_claro,  'play')   == 'play':
                username = self.get_username()
                self.run(username)
                return

            if button(self.display, "SCORES", 565, 620, 370, 160, azul,    azul_claro,   'scores') == 'scores':
                self.show_scores()

            if button(self.display, "LOJA",   1000, 620, 370, 160, ouro,    (255, 255, 100), 'shop') == 'shop':
                username = self.get_username()
                self.show_shop(username)

            if button(self.display, "SAIR",    565, 800, 370, 160, vermelho, vermelho_claro, 'quit') == 'quit':
                pygame.quit()
                sys.exit()

            pygame.display.update()
            self.clock.tick(15)

    def show_shop(self, username):
        """Tela da Loja de Aventureiros com UI de fantasia polida."""
        skins = [
            {"id": "skin_knight", "name": "passaro Lendário", "price": 2500, "desc": "Armadura vermelha e dourada"},
            {"id": "skin_mage",   "name": "passaro mago",          "price": 3000, "desc": "Roupão azul e cajado"},
            {"id": "skin_rogue",  "name": "passaro Ladino",             "price": 1800, "desc": "Capa preta e adaga"},
            {"id": "skin_druid",  "name": "passaro Druida",             "price": 2200, "desc": "Vestes verdes e lobo"},
            {"id": "skin_paladin","name": "passaro da Luz",    "price": 2000, "desc": "Armadura branca brilhante"},
            {"id": "skin_bard",   "name": "passaro das Nuvens",   "price": 1500, "desc": "Chapéu verde e alaúde"},
        ]
        backgrounds = [
            {"id": "bg_img",      "name": "Planície Pixel",     "price": 0},
            {"id": "bg_night",    "name": "Noite Mística",      "price": 1000},
            {"id": "bg_space",    "name": "Vácuo Arcano",       "price": 3000},
        ]
        
        current_tab = "skin"
        # Cores do tema
        METAL_DOURADO = (212, 175, 55)
        AZUL_PETROLEO = (0, 128, 128)
        AZUL_ESCURO   = (10, 30, 60)
        BRILHO_OURO   = (255, 223, 0)

        while True:
            user_data = get_user_data(username)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            # --- FUNDO (Pixel Art Style) ---
            # Desenha o fundo atual em loop
            bg_loop = Background(self.assets.get(user_data["bg"], self.assets['bg_img']), speed=1)
            bg_loop.draw(self.display)
            
            # Overlay sutil para a loja
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((10, 10, 30, 160))
            self.display.blit(overlay, (0, 0))

            # --- CABEÇALHO (Banner de Metal) ---
            # Banner principal
            pygame.draw.rect(self.display, METAL_DOURADO, (LARGURA//2 - 400, 20, 800, 100), border_radius=10)
            pygame.draw.rect(self.display, AZUL_PETROLEO, (LARGURA//2 - 390, 30, 780, 80), border_radius=8)
            self._draw_text_center("LOJA DE AVENTUREIROS", size=60, y_offset=-430, color=BRILHO_OURO)

            # Contador de Ouro
            gold_rect = pygame.Rect(LARGURA - 350, 35, 320, 70)
            pygame.draw.rect(self.display, METAL_DOURADO, gold_rect, border_radius=15)
            pygame.draw.rect(self.display, AZUL_ESCURO, gold_rect.inflate(-6, -6), border_radius=12)
            gold_font = pygame.font.Font('freesansbold.ttf', 35)
            gold_text = gold_font.render(f"OURO: {user_data['moedas']}", True, branco)
            self.display.blit(gold_text, (LARGURA - 320, 50))

            # --- ABAS ---
            # Personagens
            s_color = BRILHO_OURO if current_tab == "skin" else AZUL_ESCURO
            if button(self.display, "PERSONAGENS", 350, 140, 370, 80, s_color, METAL_DOURADO, 't_skin') == 't_skin':
                current_tab = "skin"
            
            # Cenários
            b_color = BRILHO_OURO if current_tab == "bg" else AZUL_ESCURO
            if button(self.display, "CENÁRIOS", 780, 140, 370, 80, b_color, METAL_DOURADO, 't_bg') == 't_bg':
                current_tab = "bg"

            # --- GRADE 2x3 ---
            items = skins if current_tab == "skin" else backgrounds
            for i, item in enumerate(items):
                col = i % 3
                row = i // 3
                x = 130 + (col * 430)
                y = 250 + (row * 280)
                
                # Painel do Item (Azul com Borda Dourada)
                panel_rect = pygame.Rect(x, y, 380, 250)
                pygame.draw.rect(self.display, METAL_DOURADO, panel_rect, border_radius=10)
                pygame.draw.rect(self.display, AZUL_ESCURO, panel_rect.inflate(-8, -8), border_radius=8)
                
                # Miniatura
                item_img = self.assets.get(item["id"], self.assets['bird_img'])
                thumb_size = (80, 80)
                thumb_img = pygame.transform.scale(item_img, thumb_size)
                self.display.blit(thumb_img, (x + 20, y + 20))

                # Nome e Preço
                name_f = pygame.font.Font('freesansbold.ttf', 24)
                name_s = name_f.render(item["name"], True, BRILHO_OURO)
                self.display.blit(name_s, (x + 115, y + 45))
                
                # Lógica de Botão
                is_owned = item["id"] in user_data["owned"] or item.get("price", 0) == 0
                is_equipped = (user_data["skin"] == item["id"] if current_tab == "skin" else user_data["bg"] == item["id"])
                
                btn_y = y + 150
                if is_equipped:
                    button(self.display, "EQUIPADO", x+40, btn_y, 300, 70, cinza, cinza)
                elif is_owned:
                    if button(self.display, "EQUIPAR", x+40, btn_y, 300, 70, AZUL_PETROLEO, METAL_DOURADO, 'sel') == 'sel':
                        select_item(username, item["id"], current_tab)
                else:
                    price_t = f"{item['price']} OURO"
                    if button(self.display, price_t, x+40, btn_y, 300, 70, METAL_DOURADO, BRILHO_OURO, 'buy') == 'buy':
                        buy_item(username, item["id"], current_tab, item["price"])

            # --- RODAPÉ (Botão Vermelho de Metal) ---
            if button(self.display, "VOLTAR PARA O MENU", LARGURA//2 - 250, 850, 500, 100, vermelho, vermelho_claro, 'back') == 'back':
                return

            pygame.display.update()
            self.clock.tick(30)

    def _draw_shop_button(self, username, item, item_type, x, y, user_data):
        """Helper para desenhar os botões de item na loja com lógica de compra/seleção."""
        is_owned = item["id"] in user_data["owned"] or item["price"] == 0
        is_equipped = (user_data["skin"] == item["id"] if item_type == "skin" 
                      else user_data["bg"] == item["id"])
        
        # Define cor e texto baseado no estado
        if is_equipped:
            msg, color, hover = "EQUIPADO", cinza, cinza
            action = None
        elif is_owned:
            msg, color, hover = f"{item['name']}", azul, azul_claro
            action = 'select'
        else:
            msg, color, hover = f"{item['name']} ({item['price']})", verde, verde_claro
            action = 'buy'

        # Tamanho padrão 370x160
        res = button(self.display, msg, x, y, 370, 160, color, hover, action)
        
        if res == 'select':
            select_item(username, item["id"], item_type)
        elif res == 'buy':
            buy_item(username, item["id"], item_type, item["price"])

    def show_scores(self):
        """Tela de placar com paginação e medalhas para o top 3."""
        page     = 0
        per_page = 8

        while True:
            rows, total      = get_scores(page, per_page)
            total_pages      = max(1, (total + per_page - 1) // per_page)
            has_prev         = page > 0
            has_next         = page < total_pages - 1

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

            # ---- Título e info de página ----
            title_font = pygame.font.Font('freesansbold.ttf', 90)
            t_surf, t_rect = text_objects("PLACAR", title_font)
            t_rect.center  = (LARGURA // 2, 75)
            self.display.blit(t_surf, t_rect)

            info_font = pygame.font.Font('freesansbold.ttf', 38)
            info_text = f"Página {page + 1} de {total_pages}   •   {total} partidas"
            i_surf, i_rect = text_objects(info_text, info_font)
            i_surf = info_font.render(info_text, True, prata)
            self.display.blit(i_surf, i_surf.get_rect(center=(LARGURA // 2, 148)))

            # ---- Cabeçalho das colunas ----
            col_font = pygame.font.Font('freesansbold.ttf', 40)
            cols = [("#", 80), ("JOGADOR", 240), ("PONTOS", 820), ("DATA", 1120)]
            for label, x in cols:
                surf = col_font.render(label, True, verde)
                self.display.blit(surf, (x, 195))
            pygame.draw.line(self.display, branco, (60, 242), (1440, 242), 1)

            # ---- Linhas de dados ----
            row_font = pygame.font.Font('freesansbold.ttf', 38)
            for i, (username, timestamp, pontos) in enumerate(rows):
                global_rank = page * per_page + i  # 0-indexed

                if   global_rank == 0: cor = ouro
                elif global_rank == 1: cor = prata
                elif global_rank == 2: cor = bronze
                else:                  cor = branco

                y        = 258 + i * 72
                date_str = timestamp[:10]

                self.display.blit(row_font.render(str(global_rank + 1), True, cor), (80,   y))
                self.display.blit(row_font.render(username,             True, cor), (240,  y))
                self.display.blit(row_font.render(str(pontos),          True, cor), (820,  y))
                self.display.blit(row_font.render(date_str,             True, cor), (1120, y))

            # ---- Botões de navegação ----
            # Anterior: ativo se tem página anterior, cinza se não
            btn_prev_ic = azul   if has_prev else cinza
            btn_prev_ac = azul_claro if has_prev else cinza
            if button(self.display, "< ANTERIOR", 80,   865, 350, 90, btn_prev_ic, btn_prev_ac, 'prev') == 'prev':
                if has_prev:
                    page -= 1

            if button(self.display, "VOLTAR",     575,  865, 350, 90, verde, verde_claro, 'back') == 'back':
                return

            # Próxima: ativo se tem próxima, cinza se não
            btn_next_ic = azul   if has_next else cinza
            btn_next_ac = azul_claro if has_next else cinza
            if button(self.display, "PROXIMA >", 1070, 865, 350, 90, btn_next_ic, btn_next_ac, 'next') == 'next':
                if has_next:
                    page += 1

            pygame.display.update()
            self.clock.tick(30)

    def crash(self, username, pontos):
        """Tela de game over. Salva o score e oferece jogar de novo ou voltar ao menu."""
        save_score(username, pontos)
        pygame.mixer.Sound.play(self.assets['crash_sound'])
        self._draw_text_center("VOCÊ BATEU")

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if button(self.display, "DE NOVO", 155, 700, 400, 200, verde,    verde_claro,    'main') == 'main':
                self.run(username)
                return

            # SAIR → volta ao menu principal (não fecha o jogo)
            if button(self.display, "SAIR",    955, 700, 400, 200, vermelho, vermelho_claro, 'menu') == 'menu':
                pygame.mixer.music.stop()
                self.game_intro()
                return

            pygame.display.update()
            self.clock.tick(15)

    def paused(self):
        """Tela de pausa."""
        while self.pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self._draw_text_center("PAUSADO")

            if button(self.display, "CONTINUAR", 155, 700, 400, 200, verde,    verde_claro,    'unpause') == 'unpause':
                self.pause = False

            # SAIR → sinaliza para run() que deve voltar ao menu
            if button(self.display, "SAIR",       955, 700, 400, 200, vermelho, vermelho_claro, 'menu') == 'menu':
                self.pause        = False
                self.quit_to_menu = True
                return

            pygame.display.update()
            self.clock.tick(15)

    # ------------------------------------------------------------------ loop principal

    def run(self, username):
        """Loop principal do jogo."""
        pygame.mixer.Sound.stop(self.assets['title'])
        pygame.mixer.music.play(-1)

        # Carrega preferências e moedas do usuário
        user_data = get_user_data(username)
        skin_key  = user_data.get("skin", "bird_img")
        bg_key    = user_data.get("bg", "bg_img")
        
        # Garante que usamos assets válidos
        skin_img = self.assets.get(skin_key, self.assets['bird_img'])
        bg_img   = self.assets.get(bg_key, self.assets['bg_img'])

        background = Background(bg_img)
        bird       = Bird(x=LARGURA * 0.40, y=ALTURA * 0.70, image=skin_img)
        obstacle   = Obstacle()
        dodged     = 0

        while True:
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.pause = True
                    self.paused()
                    # Checa se o jogador pediu para voltar ao menu via pausa
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
                pygame.mixer.Sound.play(self.assets['swoosh'])
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