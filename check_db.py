import sqlite3

conn = sqlite3.connect("scholarship.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM scholarship")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
