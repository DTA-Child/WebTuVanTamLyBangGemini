import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin():
    conn = sqlite3.connect('teen_counseling.db')
    conn.row_factory = sqlite3.Row
    
    # Kiểm tra xem admin đã tồn tại chưa
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if admin:
        print("Admin user already exists")
        # Cập nhật mật khẩu cho admin
        admin_password = generate_password_hash('admin123')
        conn.execute(
            'UPDATE users SET password = ? WHERE username = ?',
            (admin_password, 'admin')
        )
        conn.commit()
        print("Admin password updated")
    else:
        # Tạo user admin mới
        admin_password = generate_password_hash('admin123')
        conn.execute(
            'INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
            ('admin', admin_password, 'admin@example.com', 1)
        )
        
        # Lấy ID của admin vừa tạo
        admin_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Tạo thống kê cho admin
        conn.execute(
            'INSERT INTO user_stats (user_id, login_count, last_login) VALUES (?, ?, ?)',
            (admin_id, 1, datetime.now())
        )
        
        conn.commit()
        print("Admin user created")
    
    conn.close()

if __name__ == "__main__":
    create_admin()