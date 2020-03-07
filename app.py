from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
# from flask_mysqldb import MySql
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash  import sha256_crypt
import pymysql
import pymysql.cursors
from functools import wraps
from flask_cors import CORS, cross_origin
# pymysql.install_as_MySQLdb()

app = Flask(__name__)

# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, support_credentials=True)

# # Config MySQL
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'sql@2019'
# app.config['MYSQL_DB'] = 'myflaskapp'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# # init MYSQL
# mysql = MySQL(app)

db = pymysql.connect("localhost", "root", "sql@2019", "myflaskapp", cursorclass=pymysql.cursors.DictCursor)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id = id)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('User Name', [validators.Length(min=4, max = 25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords does not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        # cur = mysql.connection.cursor()
        cur = db.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        # mysql.connection.commit()
        db.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        # return redirect(url_for('home'))
        return render_template('register.html', form=form)

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = db.cursor()

        result = cur.execute("SELECT * FROM USERS WHERE username = %s", [username])

        if result>0:
            data = cur.fetchone()
            password = data['password']
        
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('Password matched')
                # return render_template('login.html', error='success')
                session['logged_in'] = True
                session['username'] = username
                flash('you are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                # app.logger.info('Password not matched')
                error = 'Invalid login'
            return render_template('login.html', error='Invalid login')

            cur.close()

        else:
            # flash('Nope', 'danger')
            # app.logger.info('No user found')
            error = 'User not found'
            return render_template('login.html', error='User not found')

    return render_template('login.html')

#cehck session
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized', 'danger')
            return redirect(url_for('login'))
    return wrap

#logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out now', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET'])
@cross_origin(origin='*')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)