from flask import Flask, request, jsonify
import psycopg2
import os
import bcrypt


app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # ✅ USERS tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ✅ POSTS tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/api')
def home():
    return 'Flask API Çalışıyor'

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli'}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_pw.decode('utf-8')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Kayıt başarılı'}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Kullanıcı adı zaten alınmış'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        if not title or not content:
            return jsonify({'error': 'Başlık ve içerik zorunlu'}), 400

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'message': 'Post başarıyla eklendi'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, title, content, created_at FROM posts ORDER BY id DESC")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify([
                {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'created_at': row[3].isoformat() if row[3] else None
                } for row in rows
            ])
        except Exception as e:
            import traceback
            print("HATA GET /posts:", e)
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500



@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users;")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([u[0] for u in users])  # sadece username'leri döndür

if __name__ == '__main__':
    init_db()  # ✅ Uygulama başlamadan önce tabloyu kontrol et/oluştur
    app.run(host='0.0.0.0', port=80)
