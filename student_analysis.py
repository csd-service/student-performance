from flask_mysqldb import MySQL
import MySQLdb.cursors
import pandas as pd
import plotly.express as px
import json

class StudentAnalyzer:
    def __init__(self, mysql):
        self.mysql = mysql

    def check_semester_data(self, semester):
        cursor = self.mysql.connection.cursor()
        cursor.execute(f"SHOW TABLES LIKE 'sem_{semester}'")
        result = cursor.fetchone() is not None
        cursor.close()
        return result

    def get_student_data(self, semester, usn):
        cursor = self.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM sem_{semester} WHERE usn = %s", (usn,))
        data = cursor.fetchone()
        cursor.close()
        
        if not data:
            return None

        # Filter subject columns
        subject_data = {k.replace('_', ' ').title(): v for k, v in data.items() 
                       if k not in ['id', 'student_name', 'usn', 'sgpa', 'result', 'overall_grade']}

        return {
            'student_info': {
                'name': data['student_name'],
                'usn': data['usn'],
                'sgpa': data['sgpa'],
                'result': data['result'],
                'overall_grade': data['overall_grade']
            },
            'subject_data': subject_data
        }