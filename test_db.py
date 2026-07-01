import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("SELECT * FROM employees")
print(cur.fetchall())

conn.close()