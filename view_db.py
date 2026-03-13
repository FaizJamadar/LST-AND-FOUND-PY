import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# View User table
print("\n--- USERS ---")
cursor.execute("SELECT * FROM user")
for row in cursor.fetchall():
    print(row)

# View Item table
print("\n--- ITEMS ---")
cursor.execute("SELECT * FROM item")
for row in cursor.fetchall():
    print(row)

# View Claim table
print("\n--- CLAIMS ---")
cursor.execute("SELECT * FROM claim")
for row in cursor.fetchall():
    print(row)

conn.close()
