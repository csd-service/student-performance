from flask import Blueprint, render_template, request, redirect, session, flash, url_for, current_app
from extensions import mysql
import MySQLdb.cursors
import re
import pandas as pd
import os
from werkzeug.utils import secure_filename
from analysis import allowed_file, calculate_sgpa, get_subject_analysis  # assuming calculate_sgpa and analysis functions exist

# Blueprint setup
auth_bp = Blueprint('auth', __name__)

# File upload processing route
@auth_bp.route('/process-upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):  # Validate file type (e.g., xlsx)
            filename = secure_filename(file.filename)  # Sanitize filename
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)  # Path where file will be saved
            
            try:
                # Save the uploaded file temporarily
                file.save(filepath)
                
                # Process the file (calculate SGPA)
                df = pd.read_excel(filepath)
                df = calculate_sgpa(df)  # Assuming calculate_sgpa processes the dataframe
                
                # Save the updated file back to the uploads folder
                df.to_excel(filepath, index=False)  # Save the file with SGPA calculated
                
                flash('File successfully uploaded and SGPA calculated.')  # Notify the user that the file has been uploaded
                return redirect(url_for('auth.analyze_data', filename=filename))  # Redirect to analysis page (optional)
            
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
        else:
            flash('Allowed file types are xlsx, xls')
            return redirect(request.url)
    
    return render_template('upload_marks.html')  # Render the upload page again if request method is GET or there was an error

# Route for analyzing data (assuming you want to show subject analysis after SGPA calculation)
@auth_bp.route('/analyze/<filename>')
def analyze_data(filename):
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File not found')
        return redirect(url_for('auth.upload_marks'))
    
    try:
        # Analyze data from the uploaded file
        df = pd.read_excel(filepath)
        analysis = get_subject_analysis(df)  # Assuming this function returns some analysis data
        return render_template('analysis.html', analysis=analysis)  # Render the analysis page with the data
        
    except Exception as e:
        flash(f'Error analyzing data: {str(e)}')
        return redirect(url_for('auth.upload_marks'))

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
            return redirect('/signin')
        
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
                return redirect('/student_dashboard')
            elif account['role'] == 'Teacher':
                return redirect('/teacher_dashboard')
        else:
            msg = 'Incorrect username/password!'
            return render_template('signin.html', msg=msg)
    
    return render_template('signin.html')

# Student Dashboard route
@auth_bp.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' in session and session.get('role') == 'Student':
        return render_template('student_dashboard.html', username=session['username'])
    return redirect('/signin')

# Teacher Dashboard route
@auth_bp.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session.get('role') == 'Teacher':
        return render_template('teacher_dashboard.html', username=session['username'])
    return redirect('/signin')

# Route for uploading marks (GET request to show upload page)
@auth_bp.route('/upload_marks', methods=['GET'])
def upload_marks():
    return render_template('upload_marks.html')

