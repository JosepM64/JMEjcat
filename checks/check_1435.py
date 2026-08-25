import sqlite3, traceback

db_path = r'D:\Documents\Programació\JMEJCat\dist\JMEJCat\data\tramitacio.db'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cursor = db.cursor()

cursor.execute('SELECT * FROM tramitacio WHERE numero = ? AND any = ?', ('1435', 2023))
row = cursor.fetchone()
if row:
    d = dict(row)
    for k, v in d.items():
        print(f'{k}: {repr(v)[:200]}')
    print(f'type(any): {type(d["any"])}')
    print(f'type(numero): {type(d["numero"])}')
else:
    print('No trobat')

db.close()
