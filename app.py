from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
from datetime import datetime
import uuid
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import custom modules
from database import init_db, get_db_connection
from user_manager import login_required, admin_required, register_user, authenticate_user
from stats_manager import (get_user_count, get_message_count, get_active_users, 
                         get_sentiment_distribution, get_message_history, 
                         get_top_active_users, get_all_users)
from database import (create_chat_session, get_user_sessions, get_session_by_id, 
                    update_session_activity, save_chat_message, get_session_messages,delete_chat_session)
import os
import sys

# Thiết lập đường dẫn cơ sở
if getattr(sys, 'frozen', False):
    # Nếu ứng dụng đã đóng gói
    base_dir = sys._MEIPASS
else:
    # Nếu đang chạy từ script
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Thiết lập đường dẫn cho templates và static
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

# Tạo ứng dụng Flask với đường dẫn tùy chỉnh
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

app.secret_key = os.urandom(24)

# Initialize database
init_db()

# Đọc API Key từ file config
config_path = os.path.join(base_dir, 'config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

GOOGLE_API_KEY = config.get("GOOGLE_API_KEY")

# Cấu hình Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Thiết lập model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# Khởi tạo mô hình
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Home route - Main chat interface
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get active session or create new one
    active_session_id = session.get('active_session')
    if not active_session_id:
        # Create new session
        session_id, session_db_id = create_chat_session(session['user_id'])
        session['active_session'] = session_id
        session['active_session_db_id'] = session_db_id
    else:
        # Validate session exists and belongs to user
        db_session = get_session_by_id(active_session_id)
        if not db_session or db_session['user_id'] != session['user_id']:
            # Create new session if invalid
            session_id, session_db_id = create_chat_session(session['user_id'])
            session['active_session'] = session_id
            session['active_session_db_id'] = session_db_id
    
    # Get user's chat sessions
    user_sessions = get_user_sessions(session['user_id'])
    
    # Get messages for current session
    messages = []
    if 'active_session_db_id' in session:
        messages = get_session_messages(session['active_session_db_id'])
    
    return render_template('index.html', 
                          username=session.get('username'),
                          active_session=session.get('active_session'),
                          sessions=user_sessions,
                          messages=messages)

# API endpoint for chat
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Update session activity
    update_session_activity(session['active_session'])
    
    try:
        # Lấy lịch sử tin nhắn hiện tại của phiên
        chat_history = []
        if 'active_session_db_id' in session:
            messages = get_session_messages(session['active_session_db_id'])
            for msg in messages:
                chat_history.append({"role": "user", "parts": [msg['user_message']]})
                chat_history.append({"role": "model", "parts": [msg['ai_response']]})
        
        # Khởi tạo chat với lịch sử tin nhắn (nếu có)
        if chat_history:
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(user_message)
        else:
            # Nếu là tin nhắn đầu tiên, tạo lời giới thiệu phù hợp
            system_prompt = """Bạn là một chuyên gia tư vấn tâm lý chuyên về tuổi dậy thì, 
            bạn sẽ cung cấp lời khuyên hữu ích, nhẹ nhàng, và phù hợp với lứa tuổi. 
            Đảm bảo giọng điệu thân thiện và thấu hiểu. 
            Tránh đưa ra lời khuyên y khoa hoặc chuyên môn vượt quá phạm vi tâm lý học.
            Nếu gặp vấn đề nghiêm trọng về sức khỏe tâm thần, luôn khuyến khích người dùng tìm kiếm sự giúp đỡ từ chuyên gia thực tế.
            Trả lời bằng tiếng Việt với giọng điệu thân thiện, nhẹ nhàng."""
            
            chat = model.start_chat(history=[
                {"role": "user", "parts": ["Hãy giới thiệu vai trò của bạn"]},
                {"role": "model", "parts": [system_prompt]}
            ])
            response = chat.send_message(user_message)
        
        ai_response = response.text
        
        # Phân tích cảm xúc đơn giản (trong ứng dụng thực, nên sử dụng NLP)
        sentiment = "neutral"
        positive_words = ["vui", "hạnh phúc", "tốt", "tuyệt", "thích", "yêu", "hài lòng"]
        negative_words = ["buồn", "chán", "khó", "tệ", "ghét", "sợ", "lo", "không thích"]
        
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in positive_words):
            sentiment = "positive"
        elif any(word in message_lower for word in negative_words):
            sentiment = "negative"
        
        # Lưu vào cơ sở dữ liệu
        save_chat_message(
            session['active_session_db_id'], 
            user_message, 
            ai_response, 
            sentiment
        )
        
        return jsonify({
            'message': ai_response
        })
    
    except Exception as e:
        print(f"Error with Gemini API: {str(e)}")
        return jsonify({
            'message': "Xin lỗi, đã có lỗi xảy ra khi xử lý tin nhắn của bạn. Vui lòng thử lại sau."
        })
@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def api_admin_stats():
    # Lấy khoảng thời gian từ query parameter, mặc định là 7 ngày
    days = request.args.get('days', default=7, type=int)
    # Giới hạn tối đa là 30 ngày để tránh quá tải
    if days > 30:
        days = 30
    
    # Lấy dữ liệu thống kê
    total_users = get_user_count()
    total_messages = get_message_count()
    active_users = get_active_users(7)
    
    sentiment_dist = get_sentiment_distribution()
    # Chuyển đổi đối tượng sentiment thành dictionary đơn giản
    sentiment = {
        'positive': sentiment_dist.get('positive', 0),
        'negative': sentiment_dist.get('negative', 0),
        'neutral': sentiment_dist.get('neutral', 0)
    }
    
    message_history = get_message_history(days)
    top_users = get_top_active_users(10)
    
    # Tạo đối tượng stats
    stats = {
        'total_users': total_users,
        'total_messages': total_messages,
        'active_users': active_users,
        'sentiment': sentiment,
        'message_history': message_history,
        'top_users': top_users,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'days': days
    }
    
    return jsonify(stats)

# Switch chat session
@app.route('/switch_session/<session_id>')
@login_required
def switch_session(session_id):
    # Verify session belongs to user
    db_session = get_session_by_id(session_id)
    if db_session and db_session['user_id'] == session['user_id']:
        session['active_session'] = session_id
        session['active_session_db_id'] = db_session['id']
    
    return redirect(url_for('index'))

# Create new session
@app.route('/new_session')
@login_required
def new_session():
    session_id, session_db_id = create_chat_session(session['user_id'])
    session['active_session'] = session_id
    session['active_session_db_id'] = session_db_id
    return redirect(url_for('index'))
#Delete session
@app.route('/delete_session/<session_id>', methods=['POST'])
@login_required
def delete_session(session_id):
    # Kiểm tra xem phiên chat có thuộc về người dùng hiện tại không
    db_session = get_session_by_id(session_id)
    if not db_session or db_session['user_id'] != session['user_id']:
        flash('Không thể xóa phiên chat này')
        return redirect(url_for('index'))
    
    # Xóa phiên chat
    success = delete_chat_session(session_id, session['user_id'])
    
    if success:
        
        
        flash('Đã xóa phiên chat thành công')
    else:
        flash('Không thể xóa phiên chat')
    
    return redirect(url_for('index'))
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        success, user = authenticate_user(username, password)
        
        if success:
            # Store user in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Đăng nhập không thành công. Kiểm tra lại tên người dùng và mật khẩu.')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if not username or not password or not email:
            flash('Tất cả các trường đều phải được điền.')
            return render_template('signup.html')
        
        success, result = register_user(username, password, email)
        
        if success:
            flash('Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect(url_for('login'))
        else:
            flash(result)
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': get_user_count(),
        'total_messages': get_message_count(),
        'active_users': get_active_users(7),
        'sentiment': get_sentiment_distribution(),
        'message_history': get_message_history(7),  # Chỉ lấy 7 ngày gần nhất
        'top_users': get_top_active_users(10),
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    return render_template('admin.html', stats=stats)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    app.run(debug=True)