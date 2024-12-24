from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import yaml
import os
import urllib.request
import logging
import joblib  # Atau import pickle jika Anda menggunakan pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import pandas as pd

# upload joblib dan kosakata
loaded_model = joblib.load('logreg.joblib')
tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
dictionary_path = "colloquial-indonesian-lexicon.csv"
df_dict = pd.read_csv(dictionary_path)

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

# input preprocessing
def preprocess_text(text):
    # 1. Case Folding
    text = text.lower()

    # 2. Cleaning (Remove punctuation, numbers, etc.)
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # 3. Normalisasi (mengganti slang)
    slang_dict = pd.Series(df_dict['formal'].values, index=df_dict['slang']).to_dict()
    slang_tambahan ={
        'knp' : 'kenapa',
        'lu' : 'kamu',
        'lu??':'kamu',
        'lo': 'kamu',
        'kayak':'seperti',
        'sdm' : 'sumber daya manusia',
        'javva' : 'jawa',
        'j4w4' : 'jawa',
        'c1n4' : 'cina',
        'cino' : 'cina',
        'jawir': 'jawa',
        'bisa' : 'dapat',
        'bodo' : 'bodoh',
        'wana' : 'jawa',
    }
    slang_dict.update(slang_tambahan)
    text = " ".join([slang_dict.get(word, word) for word in text.split()])

    # 4. Tokenization (split)
    tokens = text.split()  # Ganti word_tokenize dengan split()

    # 5. Stop Word Removal
    stop_words = set(stopwords.words('indonesian'))
    tokens = [word for word in tokens if word not in stop_words]

    # 6. Stemming
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    # Gabungkan token kembali menjadi string
    return " ".join(tokens)

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
            
            # AI detect
            input_text = caption
            processed_text = preprocess_text(input_text)
            
            try:
                text_vector = tfidf_vectorizer.transform([processed_text])  # Transformasi teks menggunakan tfidf_vectorizer
            except Exception as e:
                print("Terjadi kesalahan saat transformasi:", e)
            
            # Prediksi
            try:
                prediction = loaded_model.predict(text_vector)[0]
                if prediction == 0:              
                    # Check if image is provided
                    if image:
                        try:
                            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
                            cur = mysql.connection.cursor()
                            cur.execute("INSERT INTO posts(caption, image, user_id) VALUES(%s, %s, %s)", (caption, image.filename, session['id']))
                            mysql.connection.commit()
                            cur.close()
                            flash('Upload successful', 'success')
                        except Exception as e:
                            app.logger.error(f"Error during file upload: {e}")
                            flash('Upload failed', 'danger')
                    else:
                        flash('No image selected for uploading', 'danger')
                else:
                    flash('Teks terdeteksi sebagai SARA', 'sara')
                    return redirect(url_for('upload-page'))
            except Exception as e:
                print("Prediksi gagal:", e)
            
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
    
    