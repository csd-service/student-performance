from flask import Blueprint, render_template, request, redirect, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

auth = Blueprint('auth', __name__)

# Ensure MySQL instance is accessible globally
mysql = None

def init_mysql(app_mysql):
    global mysql
    mysql = app_mysql

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'role' in request.form:
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not role:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect('/auth/signin')
        
        return render_template('auth/signup.html', msg=msg)
    
    return render_template('auth/signup.html')

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']

            if account['role'] == 'Student':
                return redirect('/dashboard/student')
            elif account['role'] == 'Teacher':
                return redirect('/dashboard/teacher')
        else:
            msg = 'Incorrect username/password!'
            return render_template('auth/signin.html', msg=msg)

    return render_template('auth/signin.html')

@auth.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/auth/signin')
