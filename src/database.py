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
            total_pontos INTEGER NOT NULL DEFAULT 0,
            moedas       INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            username  TEXT NOT NULL,
            item_id   TEXT NOT NULL,
            item_type TEXT NOT NULL, -- 'skin' ou 'bg'
            PRIMARY KEY (username, item_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_config (
            username      TEXT PRIMARY KEY,
            selected_skin TEXT DEFAULT 'bird_img',
            selected_bg   TEXT DEFAULT 'bg_img'
        )
    """)
    conn.commit()
    conn.close()


def get_user_data(username):
    """Retorna moedas, skin selecionada e bg selecionado do usuário."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO user_stats (username, moedas) VALUES (?, 0)", (username,))
    conn.execute("INSERT OR IGNORE INTO user_config (username) VALUES (?)", (username,))
    conn.commit()

    stats = conn.execute("SELECT moedas FROM user_stats WHERE username = ?", (username,)).fetchone()
    config = conn.execute("SELECT selected_skin, selected_bg FROM user_config WHERE username = ?", (username,)).fetchone()
    inventory = conn.execute("SELECT item_id FROM inventory WHERE username = ?", (username,)).fetchall()
    conn.close()
    
    owned_items = [i[0] for i in inventory]
    return {
        "moedas": stats[0],
        "skin": config[0],
        "bg": config[1],
        "owned": owned_items
    }


def buy_item(username, item_id, item_type, price):
    """Realiza a compra de um item se o usuário tiver saldo."""
    conn = sqlite3.connect(DB_PATH)
    moedas = conn.execute("SELECT moedas FROM user_stats WHERE username = ?", (username,)).fetchone()[0]
    
    if moedas >= price:
        conn.execute("UPDATE user_stats SET moedas = moedas - ? WHERE username = ?", (price, username))
        conn.execute("INSERT OR IGNORE INTO inventory (username, item_id, item_type) VALUES (?, ?, ?)", 
                     (username, item_id, item_type))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def select_item(username, item_id, item_type):
    """Equipa um item."""
    conn = sqlite3.connect(DB_PATH)
    if item_type == 'skin':
        conn.execute("UPDATE user_config SET selected_skin = ? WHERE username = ?", (item_id, username))
    else:
        conn.execute("UPDATE user_config SET selected_bg = ? WHERE username = ?", (item_id, username))
    conn.commit()
    conn.close()

def save_score(username, pontos):
    """Insere log de partida e atualiza o cumulativo e moedas do usuário."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO score_logs (username, timestamp, pontos) VALUES (?, ?, ?)",
        (username, datetime.now().isoformat(timespec='seconds'), pontos)
    )
    # UPSERT: cria linha ou soma ao total existente
    # Moedas ganhas = pontos / 5 (divisão inteira)
    moedas_ganhas = pontos // 5
    conn.execute("""
        INSERT INTO user_stats (username, total_pontos, moedas) VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET 
            total_pontos = total_pontos + ?,
            moedas = moedas + ?
    """, (username, pontos, moedas_ganhas, pontos, moedas_ganhas))
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