# ensure_database.py
import os
import sys
import sqlite3

def ensure_db_directory():
    # Lấy thư mục làm việc hiện tại hoặc thư mục người dùng nếu không có quyền ghi
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Thử tạo file tạm để kiểm tra quyền ghi
        test_file = os.path.join(app_dir, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        return app_dir
    except:
        # Nếu không có quyền ghi, sử dụng thư mục người dùng
        user_dir = os.path.join(os.path.expanduser('~'), 'TuVanTamLy')
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir

def get_db_path():
    db_dir = ensure_db_directory()
    return os.path.join(db_dir, 'teen_counseling.db')