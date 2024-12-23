from flask_mysqldb import MySQL
import MySQLdb.cursors
import pandas as pd
import plotly.express as px
import json

class StudentAnalyzer:
    def __init__(self, mysql):
        self.mysql = mysql

    def check_semester_data(self, semester):
        """Check if data exists for given semester"""
        cursor = self.mysql.connection.cursor()
        try:
            cursor.execute(f"SHOW TABLES LIKE 'sem_{semester}'")
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def get_student_data(self, semester, usn):
        """Retrieve student data for given semester and USN"""
        cursor = self.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Get table columns first
            cursor.execute(f"DESCRIBE sem_{semester}")
            columns = [row['Field'] for row in cursor.fetchall()]
            
            # Get student data
            cursor.execute(f"SELECT * FROM sem_{semester} WHERE usn = %s", (usn,))
            data = cursor.fetchone()
            
            if not data:
                return None
                
            # Process data for analysis
            subject_data = {}
            subject_marks = []
            
            for col in columns:
                if col not in ['id', 'student_name', 'usn', 'sgpa', 'result', 'overall_grade']:
                    subject_name = col.replace('_', ' ').title()
                    marks = data[col]
                    subject_data[subject_name] = marks
                    subject_marks.append({
                        'subject': subject_name,
                        'marks': marks
                    })
            
            # Generate performance graphs
            graphs = self.generate_graphs(subject_marks, data)
            
            return {
                'student_info': {
                    'name': data['student_name'],
                    'usn': data['usn'],
                    'sgpa': data['sgpa'],
                    'result': data['result'],
                    'overall_grade': data['overall_grade']
                },
                'subject_data': subject_data,
                'graphs': graphs
            }
        finally:
            cursor.close()

    def generate_graphs(self, subject_marks, student_data):
        """Generate analysis graphs"""
        graphs = {}
        
        # Subject performance bar chart
        df_subjects = pd.DataFrame(subject_marks)
        fig_subjects = px.bar(
            df_subjects, 
            x='subject', 
            y='marks',
            title='Subject-wise Performance',
            labels={'subject': 'Subjects', 'marks': 'Marks'},
            color='marks',
            color_continuous_scale='blues'
        )
        graphs['subject_performance'] = json.loads(fig_subjects.to_json())
        
        # Performance distribution pie chart
        grade_data = [
            {'grade': 'Above 75%', 'count': len([m for m in subject_marks if m['marks'] > 75])},
            {'grade': '60-75%', 'count': len([m for m in subject_marks if 60 <= m['marks'] <= 75])},
            {'grade': 'Below 60%', 'count': len([m for m in subject_marks if m['marks'] < 60])}
        ]
        df_grades = pd.DataFrame(grade_data)
        fig_grades = px.pie(
            df_grades,
            values='count',
            names='grade',
            title='Performance Distribution',
            color_discrete_sequence=px.colors.sequential.Blues
        )
        graphs['grade_distribution'] = json.loads(fig_grades.to_json())
        
        return graphs