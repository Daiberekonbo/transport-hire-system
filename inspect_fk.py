import sqlite3, os
path = os.path.abspath('thms.db')
conn = sqlite3.connect(path)
c = conn.cursor()
for table in ['contracts', 'payments', 'expenses', 'vehicle_events', 'capital_adjustments']:
    print('TABLE', table)
    try:
        c.execute(f"PRAGMA foreign_key_list('{table}')")
        for row in c.fetchall():
            print(row)
    except Exception as e:
        print('ERR', e)
    print()
conn.close()
