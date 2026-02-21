import sqlite3

def init_user_db():
    conn =sqlite3.connect('plants.db',check_same_thread=False)
    c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id Integer primary key autoincrement,email TEXT UNIQUE NOT NULL, password Text NOT NULL, name text NOT NULL,created_at TIMESTAMP default current_timestamp)''')


    c.execute("""
        CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scientific_name TEXT UNIQUE,
        common_name TEXT,
        description TEXT,
        medicinal_uses TEXT,
        properties TEXT,
        parts_used TEXT,
        preparation TEXT,
        market_value TEXT,
        sowing TEXT,
        harvest TEXT,
        toxicity TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plant_name TEXT,
        confidence REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()
