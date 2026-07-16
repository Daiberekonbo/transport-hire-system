import os
import shutil
import sqlite3
from datetime import datetime

DB_FILE = os.path.abspath("thms.db")
BACKUP_FILE = DB_FILE + ".backup." + datetime.utcnow().strftime("%Y%m%d%H%M%S")

print(f"Backing up database: {DB_FILE}")
shutil.copy2(DB_FILE, BACKUP_FILE)
print(f"Backup created: {BACKUP_FILE}\n")

conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

before = {}
for table in ["drivers", "audit_logs"]:
    c.execute(f"SELECT COUNT(*) FROM {table}")
    before[table] = c.fetchone()[0]

print("Before cleanup:")
for table, count in before.items():
    print(f"  {table}: {count}")

print("\nDeleting archived drivers and audit log records...")

c.execute("DELETE FROM drivers WHERE status = 'archived'")
removed_drivers = c.rowcount
c.execute("DELETE FROM audit_logs")
removed_audit_logs = c.rowcount

conn.commit()

print("\nCleanup complete.")
print(f"  Archived drivers deleted: {removed_drivers}")
print(f"  Audit log records deleted: {removed_audit_logs}")

print("\nAfter cleanup:")
for table in ["drivers", "audit_logs"]:
    c.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {c.fetchone()[0]}")

conn.close()
