import os
from fpdf import FPDF

# Function to escape characters that FPDF cannot handle
def escape_special_characters(content):
    # Replace unsupported characters with '?'
    return ''.join([char if ord(char) < 256 else '?' for char in content])

# Function to write code from any file type to PDF
def write_code_to_pdf(folder_path, output_pdf):
    # Create an instance of FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Set font for the PDF (monospace font for code)
    pdf.set_font("Courier", size=10)
    
    # Loop through all files in the directory
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Write the file name as a header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, f"File: {file_path}", ln=True, align='L')
            
            # Read the content of the file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Escape any special characters that may not be supported by FPDF
                content = escape_special_characters(content)
                
                # Write the file content to the PDF
                pdf.set_font("Courier", size=10)
                pdf.multi_cell(0, 10, content)
                pdf.ln(10)  # Add space between files
            except Exception as e:
                # If there's an error reading the file (e.g., binary files)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 10, f"Error reading file {file_path}: {str(e)}")
                pdf.ln(10)  # Add space between files
    
    # Output the PDF to a file
    pdf.output(output_pdf)
    print(f"PDF generated: {output_pdf}")

# Example usage
folder_path = r'D:\project'  # Replace with your project folder path (use raw string for Windows paths)
output_pdf = 'project_code.pdf'  # The output PDF file
write_code_to_pdf(folder_path, output_pdf)
