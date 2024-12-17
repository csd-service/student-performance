from flask import Blueprint, render_template, request, redirect, session, flash, url_for, current_app
from extensions import mysql
import MySQLdb.cursors
import re
import pandas as pd
import os
from werkzeug.utils import secure_filename
from analysis import allowed_file, calculate_sgpa, get_subject_analysis  # Assuming helper functions exist

# Blueprint setup
auth_bp = Blueprint('auth', __name__)

# Route to show file upload page (Performance link)
@auth_bp.route('/upload_sheet', methods=['GET'])
def upload_sheet():
    if 'loggedin' in session and session.get('role') == 'Teacher':
        return render_template('upload_sheet.html')
    flash("Please log in as a Teacher to access this page.")
    return redirect(url_for('auth.signin'))

# File upload processing route
@auth_bp.route('/process-upload', methods=['POST'])
def upload_file():
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        flash("Unauthorized access.")
        return redirect(url_for('auth.signin'))
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):  # Validate file type (e.g., xlsx)
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            df = pd.read_excel(filepath)
            df = calculate_sgpa(df)  # Process SGPA
            df.to_excel(filepath, index=False)
            flash('File successfully uploaded and SGPA calculated.')
            return redirect(url_for('auth.analyze_data', filename=filename))
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(request.url)
    else:
        flash('Allowed file types are xlsx, xls')
        return redirect(request.url)

# Route to analyze uploaded file
@auth_bp.route('/analyze/<filename>')
def analyze_data(filename):
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File not found')
        return redirect(url_for('auth.upload_sheet'))
    
    try:
        df = pd.read_excel(filepath)
        analysis = get_subject_analysis(df)  # Function to analyze data
        return render_template('analysis.html', analysis=analysis)
    except Exception as e:
        flash(f'Error analyzing data: {str(e)}')
        return redirect(url_for('auth.upload_sheet'))

# Signup route
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
            return redirect(url_for('auth.signin'))
        
        return render_template('signup.html', msg=msg)
    
    return render_template('signup.html')

# Signin route
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
                return redirect(url_for('auth.student_dashboard'))
            elif account['role'] == 'Teacher':
                return redirect(url_for('auth.teacher_dashboard'))
        else:
            msg = 'Incorrect username/password!'
            return render_template('signin.html', msg=msg)
    
    return render_template('signin.html')

# Student Dashboard route
@auth_bp.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' in session and session.get('role') == 'Student':
        return render_template('student_dashboard.html', username=session['username'])
    flash("Please log in as a Student.")
    return redirect(url_for('auth.signin'))

# Teacher Dashboard route
@auth_bp.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session.get('role') == 'Teacher':
        return render_template('teacher_dashboard.html', username=session['username'])
    flash("Please log in as a Teacher.")
    return redirect(url_for('auth.signin'))
