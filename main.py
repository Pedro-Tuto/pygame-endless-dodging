from src.database import init_db
from src.game import Game

if __name__ == "__main__":
    init_db()          # Cria scores.db e a tabela na primeira vez; no-op depois
    Game().game_intro()