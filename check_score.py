import sqlite3

conn = sqlite3.connect("scores.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM score_logs;")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
