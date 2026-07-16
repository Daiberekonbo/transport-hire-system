import sqlite3
import os
path = os.path.abspath('thms.db')
print('DB:', path)
conn = sqlite3.connect(path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in c.fetchall()]
print('tables:', tables)
for tbl in tables:
    try:
        c.execute(f'SELECT count(*) FROM "{tbl}"')
        cnt = c.fetchone()[0]
    except Exception as e:
        cnt = f'ERR {e}'
    print(f'{tbl}: {cnt}')
conn.close()
