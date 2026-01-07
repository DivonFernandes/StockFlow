import sqlite3

db = sqlite3.connect("database.db")
with open("schema.sql") as f:
    db.executescript(f.read())
db.commit()
db.close()
