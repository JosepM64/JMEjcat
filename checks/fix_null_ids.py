import sqlite3

db_path = r'D:\Documents\Programació\JMEJCat\dist\JMEJCat\data\tramitacio.db'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Find max id
cursor.execute("SELECT MAX(id) as max_id FROM tramitacio")
max_id = cursor.fetchone()['max_id'] or 0
print(f'Current max ID: {max_id}')

# Find records with null id
cursor.execute("SELECT rowid, numero, any FROM tramitacio WHERE id IS NULL")
rows = cursor.fetchall()
print(f'Records amb id=NULL: {len(rows)}')

next_id = max_id + 1
for r in rows:
    print(f'  Assignant ID={next_id} a {r["numero"]}/{r["any"]} (rowid={r["rowid"]})')
    cursor.execute("UPDATE tramitacio SET id = ? WHERE rowid = ?", (next_id, r['rowid']))
    next_id += 1

db.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM tramitacio WHERE id IS NULL")
remaining = cursor.fetchone()[0]
print(f'\nIDs assignats. Restants amb id=NULL: {remaining}')

db.close()
