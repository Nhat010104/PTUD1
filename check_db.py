import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Xem các tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=" * 50)
print("TABLES IN DATABASE:")
print("=" * 50)
for table in tables:
    print(f"- {table[0]}")

print("\n" + "=" * 50)
print("USER TABLE DATA:")
print("=" * 50)

# Xem dữ liệu user
try:
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("\nColumns:", [col[1] for col in columns])
    
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    print(f"\nTotal users: {len(users)}")
    for user in users:
        print(user)
except Exception as e:
    print(f"Error: {e}")

conn.close()
