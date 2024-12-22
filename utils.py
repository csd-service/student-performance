from flask_mysqldb import MySQL
import MySQLdb
import re
import pandas as pd

class StudentPerformanceUtils:
    def __init__(self, mysql):
        self.mysql = mysql

    def create_semester_table(self, semester_number, columns):
        cursor = self.mysql.connection.cursor()
        table_name = f"sem_{semester_number}"
        used_columns = set()

        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_name VARCHAR(100),
                usn VARCHAR(20),
                sgpa FLOAT,
                result VARCHAR(20),
                overall_grade VARCHAR(10)
            """
            used_columns.update(['id', 'student_name', 'usn', 'sgpa', 'result', 'overall_grade'])
            
            # Process subject columns
            for col_name, _ in columns[2:]:
                if col_name.lower() in used_columns:
                    continue
                    
                subject_name = re.sub(r'\(\d+\)', '', col_name).strip()
                valid_column = re.sub(r'[^a-zA-Z0-9_]', '_', subject_name).lower()
                
                if valid_column not in used_columns:
                    create_table_sql += f",\n            {valid_column} FLOAT"
                    used_columns.add(valid_column)
            
            create_table_sql += "\n        )"
            
            cursor.execute(create_table_sql)
            self.mysql.connection.commit()
            
            # Debug: Print table structure
            cursor.execute(f"DESCRIBE {table_name}")
            print(f"Table structure for {table_name}:")
            for row in cursor.fetchall():
                print(row)
                
            return True, table_name
            
        except Exception as e:
            return False, str(e)
        finally:
            cursor.close()

    def insert_semester_data(self, table_name, df):
        """
        Insert data from DataFrame into the semester table.

        Args:
            table_name: Name of the table to insert data into
            df: Pandas DataFrame containing the data
        """
        cursor = self.mysql.connection.cursor()

        try:
            # Prepare column names
            columns = ['student_name', 'usn']
            subject_columns = []

            # Process subject columns
            for col in df.columns[2:-3]:  # Exclude student_name, usn, and last 3 columns
                subject_name = re.sub(r'\(\d+\)', '', col).strip()
                valid_column = re.sub(r'[^a-zA-Z0-9_]', '_', subject_name)
                subject_columns.append(valid_column)

            columns.extend(subject_columns)
            columns.extend(['sgpa', 'result', 'overall_grade'])

            # Create the insert query
            placeholders = ','.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

            # Prepare and execute batch insert
            values = []
            for _, row in df.iterrows():
                row_data = [row['Student Name'], row['USN']]
                row_data.extend(row[df.columns[2:-3]])
                row_data.extend([row['SGPA'], row['Result'], row['Overall Grade']])
                values.append(tuple(row_data))

            cursor.executemany(insert_query, values)
            self.mysql.connection.commit()
            return True, "Data inserted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            cursor.close()

    @staticmethod
    def extract_subject_credits(column_name):
        """Extract subject name and credits from column name."""
        match = re.search(r'(.*?)\((\d+)\)', column_name)
        if match:
            subject_name = match.group(1).strip()
            credits = int(match.group(2))
            return subject_name, credits
        return None, None

    @staticmethod
    def get_grade_point(marks):
        """Calculate grade point based on marks."""
        if marks >= 90:
            return 10
        elif marks >= 80:
            return 9
        elif marks >= 70:
            return 8
        elif marks >= 60:
            return 7
        elif marks >= 50:
            return 6
        elif marks >= 40:
            return 5
        else:
            return 0  # Fail

    @staticmethod
    def calculate_overall_grade(sgpa):
        """Calculate overall student grade based on SGPA."""
        if sgpa >= 9.0:
            return 'A+'
        elif sgpa >= 8.0:
            return 'A'
        elif sgpa >= 7.0:
            return 'B+'
        elif sgpa >= 6.0:
            return 'B'
        elif sgpa >= 5.0:
            return 'C+'
        elif sgpa >= 4.0:
            return 'C'
        else:
            return 'F'

    def calculate_sgpa(self, df):
        """Calculate SGPA, Result, and Overall Grade for each student in the DataFrame."""
        # Extract subject credits dynamically starting from the third column
        subject_credits = {
            column: credits for column, (subject, credits) in 
            ((col, self.extract_subject_credits(col)) for col in df.columns[2:]) if credits is not None
        }

        # Calculate SGPA, Result, and Overall Grade for each student
        sgpa_values = []
        result_values = []
        overall_grade_values = []

        for index, row in df.iterrows():
            # Check if student fails in any subject
            subject_failures = [
                subject for subject in subject_credits 
                if row[subject] < 28  # Fail threshold is 28 marks
            ]

            # Determine overall pass/fail
            if subject_failures:
                result = 'Fail'
                sgpa = 0
                overall_grade = 'F'
            else:
                result = 'Pass'
                # Calculate SGPA
                total_credits = sum(subject_credits.values())
                total_grade_points = sum(self.get_grade_point(row[subject]) * subject_credits[subject] 
                                       for subject in subject_credits)
                sgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0

                # Determine overall grade based on SGPA
                overall_grade = self.calculate_overall_grade(sgpa)

            sgpa_values.append(sgpa)
            result_values.append(result)
            overall_grade_values.append(overall_grade)

        # Add SGPA, Result, and Overall Grade columns
        df['SGPA'] = sgpa_values
        df['Result'] = result_values
        df['Overall Grade'] = overall_grade_values

        return df

    def get_semester_analysis(self, semester_number):
        """
        Get analysis data for a specific semester.
        Returns statistics about performance, grade distribution, etc.
        """
        cursor = self.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        table_name = f"sem_{semester_number}"

        try:
            # Get basic statistics
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_students,
                    COUNT(CASE WHEN result = 'Pass' THEN 1 END) as passed_students,
                    COUNT(CASE WHEN result = 'Fail' THEN 1 END) as failed_students,
                    AVG(sgpa) as average_sgpa,
                    MAX(sgpa) as highest_sgpa,
                    MIN(sgpa) as lowest_sgpa
                FROM {table_name}
            """)
            stats = cursor.fetchone()

            # Get grade distribution
            cursor.execute(f"""
                SELECT overall_grade, COUNT(*) as count
                FROM {table_name}
                GROUP BY overall_grade
                ORDER BY overall_grade
            """)
            grade_distribution = cursor.fetchall()

            return {
                'statistics': stats,
                'grade_distribution': grade_distribution
            }
        except Exception as e:
            return None
        finally:
            cursor.close()
