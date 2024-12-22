from flask import Blueprint, render_template
import MySQLdb.cursors
import pandas as pd

class StudentAnalysis:
    def __init__(self, mysql):
        self.mysql = mysql

    def get_semester_analysis(self, semester_number):
        """Get comprehensive analysis for a specific semester."""
        cursor = self.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        table_name = f"sem_{semester_number}"
        
        try:
            # Get basic statistics
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_students,
                    ROUND(COUNT(CASE WHEN result = 'Pass' THEN 1 END) * 100.0 / COUNT(*), 2) as pass_percentage
                FROM {table_name}
            """)
            basic_stats = cursor.fetchone()

            # Get top performers overall
            cursor.execute(f"""
                SELECT student_name as name, usn, sgpa, result
                FROM {table_name}
                WHERE result = 'Pass'
                ORDER BY sgpa DESC
                LIMIT 5
            """)
            top_performers = cursor.fetchall()

            # Get subject names (excluding standard columns)
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            all_columns = cursor.fetchall()
            subject_columns = [col['Field'] for col in all_columns 
                             if col['Field'] not in ['id', 'student_name', 'usn', 'sgpa', 'result', 'overall_grade']]

            # Get subject-wise analysis
            subjects_analysis = []
            for subject in subject_columns:
                # Get top performers in each subject
                cursor.execute(f"""
                    SELECT student_name as name, usn, {subject} as marks
                    FROM {table_name}
                    WHERE {subject} >= 40
                    ORDER BY {subject} DESC
                    LIMIT 5
                """)
                subject_top_performers = cursor.fetchall()

                # Get pass/fail count for subject
                cursor.execute(f"""
                    SELECT 
                        COUNT(CASE WHEN {subject} >= 40 THEN 1 END) as pass_count,
                        COUNT(CASE WHEN {subject} < 40 THEN 1 END) as fail_count
                    FROM {table_name}
                """)
                subject_stats = cursor.fetchone()

                subjects_analysis.append({
                    'name': subject,
                    'top_performers': subject_top_performers,
                    'pass_count': subject_stats['pass_count'],
                    'fail_count': subject_stats['fail_count']
                })

            # Get grade distribution
            cursor.execute(f"""
                SELECT overall_grade, COUNT(*) as count
                FROM {table_name}
                GROUP BY overall_grade
                ORDER BY overall_grade
            """)
            grade_distribution = {row['overall_grade']: row['count'] 
                                for row in cursor.fetchall()}

            # Prepare chart data
            pass_fail_chart = {
                'labels': ['Pass', 'Fail'],
                'data': [
                    basic_stats['pass_percentage'],
                    100 - basic_stats['pass_percentage']
                ]
            }

            subject_pass_fail = {
                'labels': [subj['name'] for subj in subjects_analysis],
                'pass_data': [subj['pass_count'] for subj in subjects_analysis],
                'fail_data': [subj['fail_count'] for subj in subjects_analysis]
            }

            return {
                'total_students': basic_stats['total_students'],
                'pass_percentage': basic_stats['pass_percentage'],
                'top_performers': {'overall': top_performers},
                'subjects': subjects_analysis,
                'overall_grade_distribution': grade_distribution,
                'pass_fail_chart': pass_fail_chart,
                'subject_pass_fail_chart': subject_pass_fail
            }

        except Exception as e:
            print(f"Error in analysis: {str(e)}")
            return None
        finally:
            cursor.close()