import sqlite3

db_path = r'D:\Documents\Programació\JMEJCat\dist\JMEJCat\data\tramitacio.db'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Find records with null id
cursor.execute("SELECT rowid, * FROM tramitacio WHERE id IS NULL")
rows = cursor.fetchall()
print(f'Records amb id=NULL: {len(rows)}')
for r in rows:
    d = dict(r)
    print(f'  rowid={d["rowid"]}  {d["numero"]}/{d["any"]}  color={d["color"]}')

# Also check for any data integrity issues
cursor.execute("SELECT COUNT(*) FROM tramitacio")
total = cursor.fetchone()[0]
print(f'\nTotal records: {total}')

# Check unique constraint
cursor.execute("SELECT numero, any, COUNT(*) as cnt FROM tramitacio GROUP BY numero, any HAVING cnt > 1")
dups = cursor.fetchall()
print(f'\nDuplicats (numero+any): {len(dups)}')
for d in dups:
    print(f'  {d["numero"]}/{d["any"]} -> {d["cnt"]} cops')

db.close()
