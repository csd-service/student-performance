from flask import Flask, render_template, request
from extensions import mysql
from routes.auth_routes import auth_bp
import os
from attendance_analysis import process_attendance  # Import the new file

app = Flask(__name__)

# Secret Key Configuration
app.secret_key = '123456789'

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@555'
app.config['MYSQL_DB'] = 'user_database'

# Initialize MySQL with the app
mysql.init_app(app)

# File upload folder configuration
app.config['UPLOAD_FOLDER'] = 'attendance'  # Folder for attendance sheets

# Ensure the folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Register blueprints
app.register_blueprint(auth_bp)

# Home route
@app.route('/')
def home():
    return render_template('index.html')  # Render the index.html file

# Route to handle attendance uploads
@app.route('/upload_attendance', methods=['GET', 'POST'])
def upload_attendance():
    if request.method == 'POST':
        # Check if the file is present in the request
        if 'attendanceSheet' not in request.files:
            return "No file part in the request", 400

        file = request.files['attendanceSheet']
        
        # Check if a file is selected
        if file.filename == '':
            return "No file selected", 400

        # Save the file in the configured upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Process the uploaded file and analyze attendance
        attendance_analysis = process_attendance(file_path)

        # Render the attendance analysis page
        return render_template('attendance.html', analysis=attendance_analysis)

    # Render the file upload form
    return render_template('upload_attendance.html')

if __name__ == '__main__':
    app.run(debug=True)
