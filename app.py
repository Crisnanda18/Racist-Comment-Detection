from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import yaml
import os
import urllib.request
import logging


app = Flask(__name__)
app.secret_key = 'secret'
upload_folder = 'static/uploads'
try:
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
except Exception as e:
    app.logger.error(f"Error creating upload folder: {e}")
app.config['UPLOAD_FOLDER'] = upload_folder
logging.basicConfig(level=logging.DEBUG)


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
                session['id'] = user[0]
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
        sql = "SELECT * FROM posts JOIN users ON posts.user_id = users.id"
        cur = mysql.connection.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        posts =[]
        for row in rows:
            post = {
                'id': row[0],
                'caption': row[1],
                'image': row[2],
                'user_id': row[3],
                'created_at': row[4],
                'name': row[6],
            }
            posts.append(post)
        greeting = get_greeting()
        return render_template('socmed.html', greeting=greeting, name=session['name'], email=session['email'], posts=posts)
    else:
        return redirect(url_for('auth'))
    
@app.route('/main/upload-page', methods=['GET'], endpoint='upload-page')
def upload_page():
    if 'name' in session:
        greeting = get_greeting()
        return render_template('upload.html', greeting=greeting, name=session['name'],email=session['email'])
    else:
        return redirect(url_for('auth'))

@app.route('/main/upload', methods=['POST'], endpoint='upload')
def upload():
    if 'name' in session:
        if request.method == 'POST':
            userDetails = request.form
            caption = userDetails['caption']
            image = request.files['image']
            try:
                if image:
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO posts(caption, image, user_id) VALUES(%s, %s, %s)", (caption, image.filename, session['id']))
                    mysql.connection.commit()
                    cur.close()
                    flash('Upload successful', 'success')
                else:
                    flash('No image selected for uploading', 'danger')
            except Exception as e:
                app.logger.error(f"Error during file upload: {e}")
                flash('Upload failed', 'danger')
            response = redirect(url_for('main'))
            app.logger.debug(f"Upload response status code: {response.status_code}")
            return response
    else:
        return redirect(url_for('auth'))

@app.route('/main/post/<int:post_id>', methods=['GET'], endpoint='post-detail')
def post(post_id):
    if 'name' in session:
        greeting = get_greeting()
        post_id = post_id
        cur = mysql.connection.cursor()
        sql = "SELECT * FROM posts JOIN users ON posts.user_id = users.id WHERE posts.id = %s"
        cur.execute(sql, [post_id])
        postDetail = cur.fetchone()
        sql = "SELECT * FROM comments JOIN users ON comments.user_id = users.id WHERE post_id = %s"
        cur.execute(sql, [post_id])
        comments = cur.fetchall()
        if postDetail:
            post_data = {
                'id': postDetail[0],
                'caption': postDetail[1],
                'image': postDetail[2],
                'user_id': postDetail[3],
                'created_at': postDetail[4],
                'name': postDetail[6],
            }
            
        if comments:
            comments_data = []
            for comment in comments:
                comment_data = {
                    'id': comment[0],
                    'comment': comment[1],
                    'post_id': comment[2],
                    'user_id': comment[3],
                    'created_at': comment[4],
                    'name': comment[6],
                }
                comments_data.append(comment_data)
        else:
            return render_template('comments.html', greeting=greeting, name=session['name'], email=session['email'], post=post_data)
            
        return render_template('comments.html', greeting=greeting, name=session['name'], email=session['email'], post=post_data, comments=comments_data)
    else:
        return redirect(url_for('auth'))
    

@app.route('/main/post/<int:post_id>/comment', methods=['POST'], endpoint='comment')
def comment(post_id):
    if 'name' in session:
        if request.method == 'POST':
            userDetails = request.form
            comment_text = userDetails.get('comment')
            user_id = session['id']

            # Log the comment details for debugging
            app.logger.debug(f"User ID: {user_id}, Post ID: {post_id}, Comment: {comment_text}")

            try:
                if comment_text:
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO comments(comment, post_id, user_id) VALUES(%s, %s, %s)", (comment_text, post_id, user_id))
                    mysql.connection.commit()
                    cur.close()

                    if cur.rowcount > 0:
                        flash('Comment successful', 'success')
                    else:
                        flash('Comment failed', 'danger')
                else:
                    flash('Comment text cannot be empty', 'danger')
            except Exception as e:
                app.logger.error(f"Error posting comment: {e}")
                flash('Comment failed', 'danger')
            response = redirect(url_for('post-detail', post_id=post_id))
            app.logger.debug(f"Comment response status code: {response.status_code}")
            return response
    else:
        return redirect(url_for('auth'))


@app.route('/migrate')
def migrate():
    cur = mysql.connection.cursor()
    sql_db = "CREATE DATABASE IF NOT EXISTS sara"
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
    cur.execute(sql_db)
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
    
    