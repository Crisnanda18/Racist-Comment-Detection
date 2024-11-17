from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import yaml

app = Flask(__name__)
app.secret_key = 'secret'


def get_greeting():
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        return "Good Morning"
    elif hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

# Config MYSQL
with open('db.yaml', 'r') as file:
    db = yaml.safe_load(file)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

@app.route('/auth', methods=['GET', 'POST'], endpoint='auth')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'], endpoint='register')
def register():
    if request.method == 'POST':
        userDetails = request.form
        name = userDetails['username']
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful', 'success')
        return redirect('auth')

@app.route('/login', methods=['POST'], endpoint='login')
def login():
    if request.method == 'POST':
        userDetails = request.form
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        if resultValue > 0:
            user = cur.fetchone()
            if password == user[3]:  # Accessing the password field correctly
                session['name'] = user[1]
                session['email'] = user[2]
                return redirect(url_for('main'))
            else:
                return redirect(url_for('login'))
        else:
            return 'ERROR'
    return render_template('login.html')

@app.route('/main', methods=['GET'], endpoint='main')
def feeds():
    if 'name' in session:
        greeting = get_greeting()
        return render_template('socmed.html', greeting=greeting, name=session['name'],email=session['email'])
    else:
        return redirect(url_for('auth'))

@app.route('/migrate')
def migrate():
    cur = mysql.connection.cursor()
    sql_user = "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), password VARCHAR(255))"
    sql_posts = """
    CREATE TABLE IF NOT EXISTS posts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        caption VARCHAR(255) NULL,
        image VARCHAR(255) NULL,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """
    sql_comments = """
    CREATE TABLE IF NOT EXISTS comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        comment VARCHAR(255) NULL,
        post_id INT,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(post_id) REFERENCES posts(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """
    cur.execute(sql_user)
    cur.execute(sql_posts)
    cur.execute(sql_comments)
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('auth'))

@app.route('/')
def homepage():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)