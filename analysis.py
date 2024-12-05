import re
import pandas as pd

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

def extract_subject_credits(column_name):
    """Extract subject name and credits from column name."""
    match = re.match(r'(.*?)\s*\((\d+)\)', column_name)
    if match:
        subject = match.group(1).strip()
        credits = int(match.group(2))
        return subject, credits
    return None, None

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

def calculate_sgpa(df):
    """Calculate SGPA for each student in the DataFrame."""
    # Extract subject credits dynamically starting from the third column
    subject_credits = {
        column: credits for column, (subject, credits) in 
        ((col, extract_subject_credits(col)) for col in df.columns[2:]) if credits is not None
    }

    # Calculate SGPA for each student
    sgpa_values = []
    for index, row in df.iterrows():
        total_credits = sum(subject_credits.values())
        total_grade_points = sum(get_grade_point(row[subject]) * subject_credits[subject] for subject in subject_credits)
        sgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0
        sgpa_values.append(sgpa)
    
    df['SGPA'] = sgpa_values
    return df

def get_subject_analysis(df):
    """Perform comprehensive subject-wise analysis."""
    analysis = {
        'total_students': len(df),
        'subjects': [],
        'top_performers': {},
    }

    # Overall Top Performers
    top_sgpa_performers = df.nlargest(5, 'SGPA')[['Student Name', 'USN', 'SGPA']]
    analysis['top_performers']['overall'] = [
        {
            'name': row['Student Name'],
            'usn': row['USN'],
            'sgpa': row['SGPA']
        } for _, row in top_sgpa_performers.iterrows()
    ]

    # Subject-wise analysis
    for col in df.columns[2:]:  # Start from the third column
        subject, credits = extract_subject_credits(col)
        if subject and credits:
            # Get top 5 performers for this subject
            top_performers = df.nlargest(5, col)[['Student Name', 'USN', col]]
            
            subject_stats = {
                'name': subject,
                'credits': credits,
                'top_performers': [
                    {
                        'name': row['Student Name'],
                        'usn': row['USN'],
                        'marks': row[col]
                    } for _, row in top_performers.iterrows()
                ],
            }
            analysis['subjects'].append(subject_stats)
    
    return analysis