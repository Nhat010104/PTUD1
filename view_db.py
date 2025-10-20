"""Simple web interface to view database"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("DATABASE VIEWER - PTUD1 Project")
print("="*80)

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nTables: {', '.join([t[0] for t in tables])}")

# Show users
print("\n" + "="*80)
print("USERS TABLE")
print("="*80)
cursor.execute("SELECT id, email, phone_number, created_at FROM user")
users = cursor.fetchall()

if users:
    print(f"\n{'ID':<5} {'Email':<30} {'Phone':<15} {'Created At':<25}")
    print("-" * 80)
    for user in users:
        user_id, email, phone, created = user
        email_display = email if email else "-"
        phone_display = phone if phone else "-"
        print(f"{user_id:<5} {email_display:<30} {phone_display:<15} {created:<25}")
    print(f"\nTotal: {len(users)} users")
else:
    print("\nNo users found")

# Show descriptions
print("\n" + "="*80)
print("DESCRIPTIONS TABLE")
print("="*80)
cursor.execute("SELECT COUNT(*) FROM description")
desc_count = cursor.fetchone()[0]
print(f"Total descriptions: {desc_count}")

if desc_count > 0:
    cursor.execute("""
        SELECT d.id, u.email, u.phone_number, d.source, d.style, 
               substr(d.content, 1, 50) as preview, d.timestamp
        FROM description d
        LEFT JOIN user u ON d.user_id = u.id
        ORDER BY d.timestamp DESC
        LIMIT 5
    """)
    descriptions = cursor.fetchall()
    print(f"\n{'ID':<5} {'User':<25} {'Source':<8} {'Style':<15} {'Preview':<30} {'Time':<20}")
    print("-" * 130)
    for desc in descriptions:
        desc_id, email, phone, source, style, preview, timestamp = desc
        user_display = email if email else (phone if phone else "Anonymous")
        print(f"{desc_id:<5} {user_display:<25} {source:<8} {style:<15} {preview:<30} {timestamp:<20}")

print("\n" + "="*80)
conn.close()
