from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Initialize database
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                gender TEXT NOT NULL,
                interested_in TEXT NOT NULL,
                profile_pic TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                liked_user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (liked_user_id) REFERENCES users(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)
        conn.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, gender, interested_in, profile_pic FROM users WHERE id != ?', (session['user_id'],))
        users = c.fetchall()
        user_id = session['user_id']
        c.execute('SELECT gender, interested_in FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        filtered_users = [u for u in users if (u[2] in user[1].split(',')) and (user[0] in u[3].split(','))]
        c.execute('SELECT liked_user_id FROM likes WHERE user_id = ?', (user_id,))
        liked_ids = [row[0] for row in c.fetchall()]
        filtered_users = [u for u in filtered_users if u[0] not in liked_ids]
    return render_template('index.html', users=filtered_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        gender = request.form['gender']
        interested_in = ','.join(request.form.getlist('interested_in'))
        profile_pic = request.files['profile_pic']

        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            profile_pic.save(filepath)
        else:
            filename = None

        try:
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO users (username, email, password, gender, interested_in, profile_pic)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, generate_password_hash(password), gender, interested_in, filename))
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, password FROM users WHERE username = ? OR email = ?", (identifier, identifier))
            user = c.fetchone()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT username, email, gender, interested_in, profile_pic FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
    return render_template('profile.html', user=user)

@app.route('/like/<int:user_id>')
def like(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO likes (user_id, liked_user_id) VALUES (?, ?)", (session['user_id'], user_id))
        c.execute("SELECT id FROM likes WHERE user_id = ? AND liked_user_id = ?", (user_id, session['user_id']))
        if c.fetchone():
            flash("It’s a match!", 'success')
        conn.commit()
    return redirect(url_for('index'))

@app.route('/pass/<int:user_id>')
def pass_user(user_id):
    return redirect(url_for('index'))

@app.route('/matches')
def matches():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username, u.profile_pic
            FROM users u
            JOIN likes l1 ON u.id = l1.liked_user_id
            JOIN likes l2 ON u.id = l2.user_id
            WHERE l1.user_id = ? AND l2.liked_user_id = ?
        """, (session['user_id'], session['user_id']))
        matches = c.fetchall()

        selected_match_id = request.args.get('match_id')
        messages = []
        if selected_match_id:
            c.execute("""
                SELECT m.sender_id, m.message, m.timestamp, u.username
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
                ORDER BY m.timestamp
            """, (session['user_id'], selected_match_id, selected_match_id, session['user_id']))
            messages = c.fetchall()
    return render_template('matches.html', matches=matches, messages=messages, selected_match_id=selected_match_id)

@app.route('/send_message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    message = request.form['message']
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                  (session['user_id'], receiver_id, message))
        conn.commit()
    return redirect(url_for('matches', match_id=receiver_id))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=True)