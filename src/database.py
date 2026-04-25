import sqlite3
from datetime import datetime

DB_PATH = "scores.db"


def init_db():
    """Cria o banco e a tabela se ainda não existirem."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS score_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL,
            timestamp TEXT    NOT NULL,
            score    INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_score(username, score):
    """Insere uma linha de log com username, timestamp atual e pontuação."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO score_logs (username, timestamp, score) VALUES (?, ?, ?)",
        (username, datetime.now().isoformat(timespec='seconds'), score)
    )
    conn.commit()
    conn.close()