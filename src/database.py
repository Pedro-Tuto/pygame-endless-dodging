import sqlite3
from datetime import datetime

DB_PATH = "scores.db"


def init_db():
    """Cria o banco e as tabelas se ainda não existirem."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS score_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL,
            timestamp TEXT    NOT NULL,
            pontos    INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            username     TEXT    PRIMARY KEY,
            total_pontos INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def save_score(username, pontos):
    """Insere log de partida e atualiza o cumulativo do usuário."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO score_logs (username, timestamp, pontos) VALUES (?, ?, ?)",
        (username, datetime.now().isoformat(timespec='seconds'), pontos)
    )
    # UPSERT: cria linha ou soma ao total existente
    conn.execute("""
        INSERT INTO user_stats (username, total_pontos) VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET total_pontos = total_pontos + ?
    """, (username, pontos, pontos))
    conn.commit()
    conn.close()


def get_scores(page=0, per_page=8):
    """Retorna (linhas, total) ordenados por pontos desc para a página dada."""
    conn = sqlite3.connect(DB_PATH)
    offset = page * per_page
    rows = conn.execute(
        "SELECT username, timestamp, pontos FROM score_logs "
        "ORDER BY pontos DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM score_logs").fetchone()[0]
    conn.close()
    return rows, total


def get_top_cumulative(limit=3):
    """Retorna os top N usuários por pontuação total acumulada."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT username, total_pontos FROM user_stats "
        "ORDER BY total_pontos DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows