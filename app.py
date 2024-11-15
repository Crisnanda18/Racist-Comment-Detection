from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
import yaml
app = Flask(__name__)

# Config MYSQL
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


@app.route('/')
def hello_world():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)