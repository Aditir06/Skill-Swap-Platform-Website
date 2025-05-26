from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'yoursecretkey'

# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    skill_offer TEXT,
                    skill_want TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for('login'))
        except:
            flash("Username already exists!", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT skills.id, users.username, skill_offer, skill_want 
                 FROM skills JOIN users ON skills.user_id = users.id''')
    skills = c.fetchall()
    conn.close()
    return render_template('dashboard.html', skills=skills)

@app.route('/offer', methods=['GET', 'POST'])
def offer_skill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        skill_offer = request.form['skill_offer']
        skill_want = request.form['skill_want']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO skills (user_id, skill_offer, skill_want) VALUES (?, ?, ?)",
                  (session['user_id'], skill_offer, skill_want))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('offer_skill.html')

@app.route('/matches')
def matches():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Get current user's skill offer and want
    c.execute("SELECT skill_offer, skill_want FROM skills WHERE user_id=?", (session['user_id'],))
    my_skills = c.fetchall()

    # Find matching users based on skill_offer/skill_want logic
    matched_users = []
    for offer, want in my_skills:
        c.execute('''
            SELECT users.username, skills.skill_offer, skills.skill_want
            FROM skills
            JOIN users ON users.id = skills.user_id
            WHERE skills.skill_offer=? AND skills.skill_want=? AND users.id != ?
        ''', (want, offer, session['user_id']))
        matched_users.extend(c.fetchall())

    conn.close()
    return render_template('matches.html', matches=matched_users)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True,port=5080)
