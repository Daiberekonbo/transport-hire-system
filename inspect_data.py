import sqlite3, os
path = os.path.abspath('thms.db')
conn = sqlite3.connect(path)
c = conn.cursor()
print('DRIVERS')
for row in c.execute('SELECT id, full_name, phone, status, date_registered, date_archived FROM drivers ORDER BY id'):
    print(row)
print('\nAUDIT LOGS')
for row in c.execute("SELECT id, user_id, action, entity_type, entity_id, created_at FROM audit_logs ORDER BY id"):
    print(row)
print('\nUSERS')
for row in c.execute('SELECT id, username, role, is_active, created_at FROM users ORDER BY id'):
    print(row)
print('\nBUSINESS SETTINGS')
for row in c.execute('SELECT * FROM business_settings'):
    print(row)
print('\nAPP PREFERENCES')
for row in c.execute('SELECT * FROM app_preferences'):
    print(row)
conn.close()
