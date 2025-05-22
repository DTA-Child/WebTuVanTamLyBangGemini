from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import functools
from database import get_user_by_username, create_user, update_login_stats

def login_required(view):  # Thêm dấu hai chấm ở đây
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('is_admin') != 1:
            flash('Không có quyền truy cập vào trang quản trị!')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

def register_user(username, password, email):
    # Check if username already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return False, "Tên người dùng đã tồn tại"
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    # Create user
    user_id = create_user(username, password_hash, email)
    if user_id:
        return True, user_id
    return False, "Đăng ký không thành công. Email có thể đã được sử dụng."

def authenticate_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        # Update login stats
        update_login_stats(user['id'])
        return True, user
    return False, None