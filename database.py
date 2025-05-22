import sqlite3
import os
from datetime import datetime
import uuid
from ensure_database import get_db_path

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        conn = get_db_connection()
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
        if not os.path.exists(schema_path) and getattr(sys, 'frozen', False):
            schema_path = os.path.join(sys._MEIPASS, 'schema.sql')
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print(f"Database initialized at {db_path}")
        
        # Tạo tài khoản admin
        create_admin_if_not_exists()

def create_admin_if_not_exists():
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if not admin:
        from werkzeug.security import generate_password_hash
        admin_password = generate_password_hash('admin123')
        
        conn.execute(
            'INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
            ('admin', admin_password, 'admin@example.com', 1)
        )
        
        # Get admin ID
        admin_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Create user stats for admin
        conn.execute(
            'INSERT INTO user_stats (user_id, login_count, last_login) VALUES (?, ?, ?)',
            (admin_id, 1, datetime.now())
        )
        
        conn.commit()
        print("Admin user created")
    
    conn.close()
# User functions
def create_user(username, password_hash, email):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            (username, password_hash, email)
        )
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.execute(
            'INSERT INTO user_stats (user_id, login_count, last_login) VALUES (?, ?, ?)',
            (user_id, 1, datetime.now())
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def update_login_stats(user_id):
    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE user_stats 
        SET login_count = login_count + 1, last_login = ? 
        WHERE user_id = ?
        ''', 
        (datetime.now(), user_id)
    )
    conn.commit()
    conn.close()

# Chat session functions
def create_chat_session(user_id):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO chat_sessions (user_id, session_id) VALUES (?, ?)',
        (user_id, session_id)
    )
    conn.commit()
    session_db_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return session_id, session_db_id
def delete_chat_session(session_id, user_id):
    """Xóa một phiên chat và tất cả tin nhắn liên quan"""
    conn = get_db_connection()
    
    # Lấy session_db_id từ session_id
    session_db = conn.execute(
        'SELECT id FROM chat_sessions WHERE session_id = ? AND user_id = ?',
        (session_id, user_id)
    ).fetchone()
    
    if not session_db:
        conn.close()
        return False
    
    session_db_id = session_db['id']
    
    # Xóa tất cả tin nhắn liên quan đến phiên chat
    conn.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_db_id,))
    
    # Xóa phiên chat
    conn.execute('DELETE FROM chat_sessions WHERE id = ?', (session_db_id,))
    
    conn.commit()
    conn.close()
    return True
    
def get_user_sessions(user_id):
    conn = get_db_connection()
    sessions = conn.execute(
        'SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY last_active DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return sessions

def get_session_by_id(session_id):
    conn = get_db_connection()
    session = conn.execute(
        'SELECT * FROM chat_sessions WHERE session_id = ?',
        (session_id,)
    ).fetchone()
    conn.close()
    return session

def update_session_activity(session_id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE chat_sessions SET last_active = ? WHERE session_id = ?',
        (datetime.now(), session_id)
    )
    conn.commit()
    conn.close()

# Chat message functions
def save_chat_message(session_db_id, user_message, ai_response, sentiment=None):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO chat_messages (session_id, user_message, ai_response, sentiment) VALUES (?, ?, ?, ?)',
        (session_db_id, user_message, ai_response, sentiment)
    )
    # Update user stats
    user_id = conn.execute('SELECT user_id FROM chat_sessions WHERE id = ?', (session_db_id,)).fetchone()[0]
    conn.execute(
        'UPDATE user_stats SET total_messages = total_messages + 1 WHERE user_id = ?',
        (user_id,)
    )
    conn.commit()
    conn.close()

def get_session_messages(session_db_id):
    conn = get_db_connection()
    messages = conn.execute(
        'SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp',
        (session_db_id,)
    ).fetchall()
    conn.close()
    return messages