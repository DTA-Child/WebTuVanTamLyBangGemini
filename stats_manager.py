from database import get_db_connection
from datetime import datetime, timedelta

def get_user_count():
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0').fetchone()[0]
    conn.close()
    return count

def get_message_count():
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM chat_messages').fetchone()[0]
    conn.close()
    return count

def get_active_users(days=7):
    cutoff_date = datetime.now() - timedelta(days=days)
    conn = get_db_connection()
    count = conn.execute(
        '''
        SELECT COUNT(DISTINCT user_id) FROM user_stats 
        WHERE last_login > ?
        ''', 
        (cutoff_date,)
    ).fetchone()[0]
    conn.close()
    return count

def get_sentiment_distribution():
    conn = get_db_connection()
    results = conn.execute(
        '''
        SELECT sentiment, COUNT(*) as count 
        FROM chat_messages 
        WHERE sentiment IS NOT NULL 
        GROUP BY sentiment
        '''
    ).fetchall()
    conn.close()
    
    # Chuyển đổi thành dictionary đơn giản
    distribution = {
        'positive': 0,
        'negative': 0,
        'neutral': 0
    }
    
    for row in results:
        sentiment = row['sentiment']
        count = row['count']
        if sentiment in distribution:
            distribution[sentiment] = count
    
    return distribution

def get_message_history(days=7):
    conn = get_db_connection()
    now = datetime.now()
    history = []
    
    for i in range(days):
        date = now - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        count = conn.execute(
            '''
            SELECT COUNT(*) FROM chat_messages 
            WHERE DATE(timestamp) = DATE(?)
            ''', 
            (date_str,)
        ).fetchone()[0]
        history.append({'date': date_str, 'count': count})
    
    conn.close()
    # Đảo ngược mảng để hiển thị từ ngày cũ đến ngày mới
    return list(reversed(history))

def get_top_active_users(limit=10):
    conn = get_db_connection()
    users = conn.execute(
        '''
        SELECT u.username, s.total_messages, s.login_count
        FROM user_stats s
        JOIN users u ON s.user_id = u.id
        WHERE u.is_admin = 0
        ORDER BY s.total_messages DESC
        LIMIT ?
        ''',
        (limit,)
    ).fetchall()
    conn.close()
    
    # Chuyển đổi Row objects thành dictionaries
    return [{'username': user['username'], 
             'total_messages': user['total_messages'], 
             'login_count': user['login_count']} for user in users]

def get_all_users():
    conn = get_db_connection()
    users = conn.execute(
        '''
        SELECT u.id, u.username, u.email, u.created_at, 
               s.total_messages, s.login_count, s.last_login
        FROM users u
        LEFT JOIN user_stats s ON u.id = s.user_id
        WHERE u.is_admin = 0
        ORDER BY s.total_messages DESC
        '''
    ).fetchall()
    conn.close()
    
    # Chuyển đổi Row objects thành dictionaries
    return [{
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'created_at': user['created_at'],
        'total_messages': user['total_messages'] or 0,
        'login_count': user['login_count'] or 0,
        'last_login': user['last_login']
    } for user in users]