import sqlite3
conn = sqlite3.connect('vehicle_detection.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('=== All Tables ===')
for table in tables:
    print(f'- {table[0]}')
print()

# Check each table schema and data
for table_name in [t[0] for t in tables]:
    print(f'\n=== Table: {table_name} ===')
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print('Columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'Row Count: {count}')
    
    if count > 0:
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 2')
        rows = cursor.fetchall()
        for row in rows:
            print(f'  Sample: {row}')
conn.close()
