# Student Performance Analyzer (SPA) 📊

A comprehensive web-based platform for tracking and analyzing student academic performance and attendance data. Built with Flask and designed for educational institutions.

## 🌟 Features

- **User Authentication**
  - Separate dashboards for students and teachers
  - Secure login and registration system
  - Role-based access control

- **Performance Analysis**
  - Upload and process student performance data
  - Generate comprehensive analysis reports
  - Individual student performance tracking
  - Grade distribution visualization

- **Attendance Management**
  - Track and analyze attendance patterns
  - Generate attendance reports
  - View individual student attendance records

## 🛠️ Technology Stack

- **Frontend**
  - HTML5
  - CSS3 (Separate styles for teacher and student views)
  - JavaScript

- **Backend**
  - Python
  - Flask
  - Pandas (for data analysis)

## 📁 Project Structure

```
Student_Performance_Analyzer/
├── app.py                    # Main Flask application entry point
├── utils.py                  # Utility functions for data processing
├── analysis.py              # Class for analyzing student performance
├── student_analysis.py      # Class for individual student analytics
├── attendance.py            # Class for attendance management
├── uploads/                 # Temporary folder for file uploads
├── static/                  # Static files (CSS, JS, images)
│   ├── images/             # Image assets
│   ├── teacher_style.css   # Teacher dashboard styling
│   └── student_style.css   # Student dashboard styling
├── templates/              # HTML templates
│   ├── index.html         # Landing page
│   ├── signin.html        # Login page
│   ├── signup.html        # Registration page
│   ├── teacher_dashboard.html
│   ├── student_dashboard.html
│   ├── analysis.html      # Performance analysis page
│   ├── attendance.html    # Attendance tracking page
│   ├── student_analysis.html
│   ├── student_attendance.html
│   └── student_usn_form.html
└── routes/                # Route handlers
    └── auth_routes.py     # Authentication routes
```

## 💻 Usage

### Teacher Access:
1. Register/Login as a teacher
2. Access the teacher dashboard
3. Upload student performance data
4. View analysis reports
5. Track attendance

### Student Access:
1. Register/Login as a student
2. View personal dashboard
3. Check individual performance metrics
4. View attendance records
