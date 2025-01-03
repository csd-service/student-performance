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
            # Get basic statistics with consistent counting
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_students,
                    SUM(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) as passed_students,
                    SUM(CASE WHEN result = 'Fail' OR overall_grade = 'F' THEN 1 ELSE 0 END) as failed_students,
                    AVG(CASE WHEN result = 'Pass' THEN sgpa ELSE 0 END) as average_sgpa,
                    MAX(CASE WHEN result = 'Pass' THEN sgpa ELSE 0 END) as highest_sgpa,
                    MIN(CASE WHEN result = 'Pass' THEN sgpa ELSE 0 END) as lowest_sgpa
                FROM {table_name}
            """)
            basic_stats = cursor.fetchone()
            total_students = basic_stats['total_students']
            passed_students = basic_stats['passed_students']
            failed_students = basic_stats['failed_students']
            pass_percentage = round((passed_students / total_students) * 100, 2) if total_students > 0 else 0

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
                    passed_students,
                    failed_students
                ]
            }

            subject_pass_fail = {
                'labels': [subj['name'] for subj in subjects_analysis],
                'pass_data': [subj['pass_count'] for subj in subjects_analysis],
                'fail_data': [subj['fail_count'] for subj in subjects_analysis]
            }

            # Add SGPA distribution
            cursor.execute(f"""
                SELECT 
                    COUNT(CASE WHEN sgpa BETWEEN 0 AND 2 THEN 1 END) as low,
                    COUNT(CASE WHEN sgpa BETWEEN 2 AND 4 THEN 1 END) as low_mid,
                    COUNT(CASE WHEN sgpa BETWEEN 4 AND 6 THEN 1 END) as mid,
                    COUNT(CASE WHEN sgpa BETWEEN 6 AND 7 THEN 1 END) as mid_high,
                    COUNT(CASE WHEN sgpa BETWEEN 7 AND 8 THEN 1 END) as high,
                    COUNT(CASE WHEN sgpa BETWEEN 8 AND 9 THEN 1 END) as very_high,
                    COUNT(CASE WHEN sgpa BETWEEN 9 AND 10 THEN 1 END) as excellent
                FROM {table_name}
            """)
            sgpa_distribution = cursor.fetchone()

            # Add subject performance analysis - Fix the AVG query
            subject_performance = {
                'labels': [],
                'averages': []
            }
            
            for subject in subject_columns:
                subject_performance['labels'].append(subject.replace('_', ' ').title())
                cursor.execute(f"SELECT ROUND(AVG(`{subject}`), 2) as avg_marks FROM {table_name}")
                result = cursor.fetchone()
                subject_performance['averages'].append(float(result['avg_marks'] or 0))

            # Add subject pass percentage
            subject_pass_percentage = {
                'labels': [col.replace('_', ' ').title() for col in subject_columns],
                'percentages': [],
                'colors': []
            }

            for subject in subject_columns:
                cursor.execute(f"""
                    SELECT 
                        (COUNT(CASE WHEN {subject} >= 40 THEN 1 END) * 100.0 / COUNT(*)) as pass_rate
                    FROM {table_name}
                """)
                pass_rate = round(cursor.fetchone()['pass_rate'], 2)
                subject_pass_percentage['percentages'].append(pass_rate)
                # Color based on pass rate
                color = (
                    'rgba(76, 175, 80, 0.6)' if pass_rate >= 75 else
                    'rgba(255, 152, 0, 0.6)' if pass_rate >= 60 else
                    'rgba(244, 67, 54, 0.6)'
                )
                subject_pass_percentage['colors'].append(color)

            return {
                'total_students': total_students,
                'pass_percentage': pass_percentage,
                'top_performers': {'overall': top_performers},
                'subjects': subjects_analysis,
                'overall_grade_distribution': grade_distribution,
                'pass_fail_chart': pass_fail_chart,
                'subject_pass_fail_chart': subject_pass_fail,
                'sgpa_distribution': sgpa_distribution,
                'subject_performance': subject_performance,
                'subject_pass_percentage': subject_pass_percentage
            }

        except Exception as e:
            print(f"Error in analysis: {str(e)}")
            return None
        finally:
            cursor.close()