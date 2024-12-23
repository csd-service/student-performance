from flask import Blueprint, render_template, request, redirect, session, flash, url_for, current_app, jsonify
import MySQLdb.cursors
import pandas as pd
import os
from werkzeug.utils import secure_filename
import re
from utils import StudentPerformanceUtils
from analysis import StudentAnalysis
from student_analysis import StudentAnalyzer
from attendance import AttendanceAnalyzer

auth_bp = Blueprint('auth', __name__)
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# Initialize MySQL and Bcrypt
mysql = None
bcrypt = None

def init_mysql(app_mysql):
    global mysql
    mysql = app_mysql

def init_bcrypt(app_bcrypt):
    global bcrypt
    bcrypt = app_bcrypt

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            # Hash the password before storing
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', 
                         (username, hashed_password, role))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('auth.signin'))
        return render_template('signup.html', msg=msg)
    return render_template('signup.html')

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account and bcrypt.check_password_hash(account['password'], password):
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

@auth_bp.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('auth.signin'))

@auth_bp.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' in session and session.get('role') == 'Student':
        return render_template('student_dashboard.html', username=session['username'])
    flash("Please log in as a Student.")
    return redirect(url_for('auth.signin'))

@auth_bp.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session.get('role') == 'Teacher':
        return render_template('teacher_dashboard.html', username=session['username'])
    flash("Please log in as a Teacher.")
    return redirect(url_for('auth.signin'))

@auth_bp.route('/check_semester/<semester>')
def check_semester(semester):
    if 'loggedin' not in session or session.get('role') != 'Student':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    analyzer = StudentAnalyzer(mysql)
    has_data = analyzer.check_semester_data(semester)
    return jsonify({'status': 'success', 'has_data': has_data})

@auth_bp.route('/student_analysis/<semester>', methods=['GET', 'POST'])
def student_analysis(semester):
    if 'loggedin' not in session or session.get('role') != 'Student':
        flash("Please log in as a Student.")
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        usn = request.form.get('usn')
        if not usn:
            flash("Please enter your USN")
            return redirect(url_for('auth.student_analysis', semester=semester))

        analyzer = StudentAnalyzer(mysql)
        student_data = analyzer.get_student_data(semester, usn)

        if not student_data:
            flash("No data found for the given USN")
            return redirect(url_for('auth.student_analysis', semester=semester))

        return render_template('student_analysis.html', student_data=student_data)

    return render_template('student_usn_form.html', semester=semester)

@auth_bp.route('/analysis/<semester>')
def analysis(semester):
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        flash("Please log in as a Teacher.")
        return redirect(url_for('auth.signin'))
    
    analyzer = StudentAnalysis(mysql)
    analysis_data = analyzer.get_semester_analysis(semester)
    
    if analysis_data:
        return render_template('analysis.html', analysis=analysis_data)
    else:
        flash("Error retrieving analysis data.")
        return redirect(url_for('auth.teacher_dashboard'))

@auth_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access.'})

    if 'file' not in request.files or 'semester' not in request.form:
        return jsonify({'status': 'error', 'message': 'Missing file or semester information'})

    file = request.files['file']
    semester = request.form['semester']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            df = pd.read_excel(filepath)
            utils = StudentPerformanceUtils(mysql)
            df = utils.calculate_sgpa(df)
            
            columns = [(col, 'FLOAT') if 'Marks' in col else (col, 'VARCHAR(100)') for col in df.columns]
            success, response = utils.create_semester_table(semester, columns)
            if not success:
                return jsonify({'status': 'error', 'message': f'Error creating table: {response}'})
            
            success, response = utils.insert_semester_data(response, df)
            if not success:
                return jsonify({'status': 'error', 'message': f'Error inserting data: {response}'})
            
            return jsonify({
                'status': 'success', 
                'message': 'Data processed successfully!',
                'redirect': url_for('auth.analysis', semester=semester)
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'})
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    return jsonify({'status': 'error', 'message': 'Allowed file types are xlsx, xls'})

@auth_bp.route('/teacher')
def teacher():
    return render_template('teacher.html')

@auth_bp.route('/attendance/<semester>')
def attendance(semester):
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        flash("Please log in as a Teacher.")
        return redirect(url_for('auth.signin'))
    
    analyzer = AttendanceAnalyzer(mysql)
    attendance_data = analyzer.get_attendance_data(semester)
    
    if attendance_data:
        return render_template('attendance.html', data=attendance_data, semester=semester)
    else:
        return render_template('attendance.html', data=None, semester=semester)

@auth_bp.route('/upload_attendance', methods=['POST'])
def upload_attendance():
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access.'})

    if 'file' not in request.files or 'semester' not in request.form:
        return jsonify({'status': 'error', 'message': 'Missing file or semester information'})

    file = request.files['file']
    semester = request.form['semester']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            analyzer = AttendanceAnalyzer(mysql)
            success, message = analyzer.process_attendance_file(filepath, semester)
            
            if success:
                return jsonify({
                    'status': 'success', 
                    'message': message,
                    'redirect': url_for('auth.attendance', semester=semester)
                })
            else:
                return jsonify({'status': 'error', 'message': message})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'})
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    return jsonify({'status': 'error', 'message': 'Allowed file types are xlsx, xls'})