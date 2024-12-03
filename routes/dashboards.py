from flask import Blueprint, render_template, session, redirect

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' in session and session['role'] == 'Student':
        return render_template('student_dashboard.html', username=session['username'])
    return redirect('/signin')

@dashboard_bp.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session['role'] == 'Teacher':
        return render_template('teacher_dashboard.html', username=session['username'])
    return redirect('/signin')
