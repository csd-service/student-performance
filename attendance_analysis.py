import pandas as pd
import os

def process_attendance(file_path):
    # Read the uploaded Excel file
    xl = pd.ExcelFile(file_path)
    
    # Dictionary to store results
    attendance_analysis = {}

    # Loop through each sheet (subject)
    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)

        # Analyze the attendance for each student
        for index, row in df.iterrows():
            usn = row[0]
            student_name = row[1]
            total_days = len(row) - 2  # Exclude USN and Name columns
            attendance_count = row[2:].value_counts().get('P', 0)  # Count 'P' (Present) in attendance
            percentage = (attendance_count / total_days) * 100

            # Check if the student's attendance is below 60%
            if percentage < 60:
                if sheet_name not in attendance_analysis:
                    attendance_analysis[sheet_name] = []
                attendance_analysis[sheet_name].append({
                    'usn': usn,
                    'name': student_name,
                    'attendance_percentage': percentage,
                    'attendance_count': attendance_count,
                    'total_days': total_days
                })

    return attendance_analysis
