import sqlite3
from flask import g

DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                profile_pic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

def get_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

def create_user(id_, name, email, profile_pic):
    db = get_db()
    try:
        db.execute(
            'INSERT OR REPLACE INTO users (id, name, email, profile_pic) VALUES (?, ?, ?, ?)',
            (id_, name, email, profile_pic)
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()