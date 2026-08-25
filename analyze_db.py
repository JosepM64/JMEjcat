import sqlite3
from pathlib import Path

# Analizar jmejcat.db
db_path = Path(r"D:\Documents\Programació\JMEJCat\data\jmejcat.db")
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("=== jmejcat.db ===")
    print(f"Archivo: {db_path}")
    print(f"Tamaño: {db_path.stat().st_size} bytes")

    # Tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"Tablas: {[t[0] for t in tables]}")

    # Esquema de notes
    cur.execute("SELECT sql FROM sqlite_master WHERE name='notes'")
    schema = cur.fetchone()
    if schema:
        print("\nEsquema de 'notes':")
        print(schema[0])

    # Contenido de notes
    cur.execute("SELECT COUNT(*) FROM notes")
    count = cur.fetchone()[0]
    print(f"\nNúmero de notas: {count}")

    if count > 0:
        cur.execute("SELECT id, title FROM notes LIMIT 3")
        rows = cur.fetchall()
        print("Primeras 3 notas:")
        for row in rows:
            print(f"  ID {row[0]}: {row[1]}")

    conn.close()
except Exception as e:
    print(f"ERROR analizando jmejcat.db: {e}")

print("\n" + "=" * 50 + "\n")

# Analizar tramitacio.db
db_path2 = Path(r"D:\Documents\Programació\JMEJCat\data\tramitacio.db")
try:
    conn2 = sqlite3.connect(db_path2)
    cur2 = conn2.cursor()

    print("=== tramitacio.db ===")
    print(f"Archivo: {db_path2}")
    print(f"Tamaño: {db_path2.stat().st_size} bytes")

    # Tablas
    cur2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables2 = cur2.fetchall()
    print(f"Tablas: {[t[0] for t in tables2]}")

    # Esquema de tramitacio
    cur2.execute("SELECT sql FROM sqlite_master WHERE name='tramitacio'")
    schema2 = cur2.fetchone()
    if schema2:
        print("\nEsquema de 'tramitacio':")
        print(schema2[0])

    # Contenido
    cur2.execute("SELECT COUNT(*) FROM tramitacio")
    count2 = cur2.fetchone()[0]
    print(f"\nNúmero de tràmits: {count2}")

    if count2 > 0:
        cur2.execute("SELECT * FROM tramitacio LIMIT 1")
        row = cur2.fetchone()
        print("Primer tràmit (RAW):")
        print(row)

    conn2.close()
except Exception as e:
    print(f"ERROR analizando tramitacio.db: {e}")
