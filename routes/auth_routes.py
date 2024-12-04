from flask import Blueprint, render_template, request, redirect, session
from extensions import mysql
import MySQLdb.cursors
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
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
            return redirect('/signin')
        
        return render_template('signup.html', msg=msg)
    
    return render_template('signup.html')

@auth_bp.route('/signin', methods=['GET', 'POST'])
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
                return redirect('/student_dashboard')
            elif account['role'] == 'Teacher':
                return redirect('/teacher_dashboard')
        else:
            msg = 'Incorrect username/password!'
            return render_template('signin.html', msg=msg)
    
    return render_template('signin.html')

@auth_bp.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' in session and session.get('role') == 'Student':
        return render_template('student_dashboard.html', username=session['username'])
    return redirect('/signin')

@auth_bp.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session.get('role') == 'Teacher':
        return render_template('teacher_dashboard.html', username=session['username'])
    return redirect('/signin')

@auth_bp.route('/upload_marks', methods=['GET'])
def upload_marks():
    # Render the upload_marks.html template
    return render_template('upload_marks.html')



