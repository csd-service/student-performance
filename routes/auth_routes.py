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

        print("🟡 [DEBUG] Username submitted:", username)
        print("🟡 [DEBUG] Password submitted (plaintext):", password)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            print("🟢 [DEBUG] Account found in DB:", account)
            print("🟢 [DEBUG] Stored hashed password:", account['password'])

            password_match = bcrypt.check_password_hash(account['password'], password)
            print("🟢 [DEBUG] Password match result:", password_match)

            if password_match:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['role'] = account['role']

                print("✅ [DEBUG] Login successful. Role:", account['role'])

                # Redirect based on stored role in database
                if account['role'] == 'Student':
                    return redirect(url_for('auth.student_dashboard'))
                elif account['role'] == 'Teacher':
                    return redirect(url_for('auth.teacher_dashboard'))
            else:
                print("❌ [DEBUG] Password incorrect")
        else:
            print("❌ [DEBUG] No account found for username:", username)

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
    print(analysis_data)

    if analysis_data:
        try:
            return render_template('analysis.html', analysis=analysis_data, semester=semester)
        except Exception as e:
            print(f"Template rendering error: {str(e)}")
            flash("Error rendering analysis template.")
            return redirect(url_for('auth.teacher_dashboard'))
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

            df = pd.read_excel(filepath, engine='openpyxl')

            utils = StudentPerformanceUtils(mysql)
            df = utils.calculate_sgpa(df)

            columns = [(col, 'FLOAT') if 'Marks' in col else (col, 'VARCHAR(100)') for col in df.columns]
            success, table_name = utils.create_semester_table(semester, columns)
            if not success:
                return jsonify({'status': 'error', 'message': f'Error creating table: {table_name}'})
            
            success, message = utils.insert_semester_data(table_name, df)
            if not success:
                return jsonify({'status': 'error', 'message': f'Error inserting data: {message}'})

            # Add a small delay to ensure data is committed
            from time import sleep
            sleep(1)
            
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

@auth_bp.route('/check_attendance/<semester>')
def check_attendance(semester):
    if 'loggedin' not in session or session.get('role') != 'Student':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    analyzer = AttendanceAnalyzer(mysql)
    data = analyzer.get_attendance_data(semester)
    has_data = data is not None
    return jsonify({'status': 'success', 'has_data': has_data})

@auth_bp.route('/student_attendance/<semester>', methods=['GET', 'POST'])
def student_attendance(semester):
    if 'loggedin' not in session or session.get('role') != 'Student':
        flash("Please log in as a Student.")
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        usn = request.form.get('usn')
        if not usn:
            flash("Please enter your USN")
            return redirect(url_for('auth.student_attendance', semester=semester))

        analyzer = AttendanceAnalyzer(mysql)
        attendance_data = analyzer.get_attendance_data(semester, usn)

        if not attendance_data:
            flash("No attendance data found for the given USN")
            return redirect(url_for('auth.student_attendance', semester=semester))

        return render_template('student_attendance.html', data=attendance_data[0], semester=semester)

    return render_template('student_attendance_form.html', semester=semester)

@auth_bp.route('/check_teacher_semester/<semester>')
def check_teacher_semester(semester):
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    table_type = request.args.get('type', 'performance')
    table_name = f"sem_{semester}" if table_type == 'performance' else f"attendance_sem_{semester}"

    cursor = mysql.connection.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    has_data = cursor.fetchone() is not None
    cursor.close()

    return jsonify({
        'status': 'success',
        'has_data': has_data,
        'redirect': url_for('auth.analysis', semester=semester) if has_data and table_type == 'performance' else url_for('auth.attendance', semester=semester) if has_data else None
    })

@auth_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'Please login first'})
        
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        semester = data.get('semester')
        feedback_text = data.get('feedback')
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO feedback (name, email, semester, feedback_text) VALUES (%s, %s, %s, %s)',
            (name, email, semester, feedback_text)
        )
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'message': 'Feedback submitted successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@auth_bp.route('/get_feedback')
def get_feedback():
    if 'loggedin' not in session or session.get('role') != 'Teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM feedback ORDER BY id DESC')
        feedback = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'status': 'success',
            'feedback': feedback
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })