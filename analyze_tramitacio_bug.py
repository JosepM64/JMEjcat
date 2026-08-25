"""Script per analitzar i netejar registres de tramitació amb info bloquejada."""
import sqlite3

db_path = r'D:\Documents\Programació\JMEJCat\dist\JMEJCat\data\tramitacio.db'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cursor = db.cursor()

cursor.execute("SELECT id, numero, any, info FROM tramitacio WHERE info != '' AND info IS NOT NULL")
records = cursor.fetchall()
print(f"Total records amb info no buida: {len(records)}\n")

for r in records:
    info_preview = r['info'][:80].replace('\n', ' | ')
    print(f"  ID={r['id']:>4}  {r['numero']}/{r['any']:>4}  -> {info_preview}...")

print("\n---\n")

# Mostrar detall dels registres problemàtics
for r in records:
    if (r['numero'] == '1477' and r['any'] == 2025) or (r['numero'] == '1066' and r['any'] == 2011):
        print(f"\n=== {r['numero']}/{r['any']} (ID={r['id']}) ===")
        print(r['info'])
        print()

db.close()
