from flask import Blueprint, jsonify, current_app
import pandas as pd
import os
from werkzeug.utils import secure_filename

class AttendanceAnalyzer:
    def __init__(self, mysql):
        self.mysql = mysql

    def create_attendance_table(self, semester):
        cursor = self.mysql.connection.cursor()
        table_name = f"attendance_sem_{semester}"
        
        try:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usn VARCHAR(20),
                    student_name VARCHAR(100)
                )
            """)
            
            # Get all dates from the DataFrame to create dynamic columns
            self.mysql.connection.commit()
            return True, table_name
        except Exception as e:
            return False, str(e)

    def process_attendance_file(self, file_path, semester):
        try:
            df = pd.read_excel(file_path)
            
            # Validate basic columns
            if 'USN' not in df.columns or 'Student Name' not in df.columns:
                return False, "Missing USN or Student Name columns"
            
            # Create base table
            success, table_name = self.create_attendance_table(semester)
            if not success:
                return False, table_name
            
            cursor = self.mysql.connection.cursor()
            
            # Add date columns dynamically
            date_columns = [col for col in df.columns if col not in ['USN', 'Student Name']]
            for date_col in date_columns:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN `{date_col}` VARCHAR(1)")
                except:
                    pass  # Column might already exist
            
            # Insert data
            for _, row in df.iterrows():
                columns = ['usn', 'student_name'] + [f'`{date}`' for date in date_columns]
                values = [row['USN'], row['Student Name']] + [row[date] for date in date_columns]
                placeholders = ','.join(['%s'] * len(values))
                
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    ({','.join(columns)})
                    VALUES ({placeholders})
                """, values)
            
            self.mysql.connection.commit()
            return True, "Attendance data processed successfully"
            
        except Exception as e:
            return False, str(e)

    def get_attendance_data(self, semester, usn=None):
        cursor = self.mysql.connection.cursor()
        table_name = f"attendance_sem_{semester}"
        
        try:
            if usn:
                cursor.execute(f"SELECT * FROM {table_name} WHERE usn = %s", (usn,))
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            return None