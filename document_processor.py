import PyPDF2
import pandas as pd
import openpyxl
import chardet
from google_vision import detect_text_pdf, read_text_from_image
import pandas as pd
def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def process_document(file_path,watermark):
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        return detect_text_pdf(file_path,watermark)
    elif file_extension in ['xlsx', 'xls']:
        return process_excel(file_path)
    elif file_extension == 'csv':
        return process_csv(file_path)
    elif file_extension == 'txt':
        return process_txt(file_path)
    elif file_extension== 'docx':
        return process_docx(file_path)
    elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'tif', 'webp', 'ico', 'heic', 'heif', 'svg', 'raw', 'arw', 'cr2', 'nef', 'orf', 'sr2']:
        result = read_text_from_image(file_path)
        print(result)
        return result
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
def process_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def process_excel(file_path):
    df = pd.read_excel(file_path)
    return df.to_string()

def process_docx(file_path):
    doc = openpyxl.load_workbook(file_path)
    text = ""
    for sheet in doc.worksheets:
        for row in sheet.rows:
            for cell in row:
                text += str(cell.value) + " "
    return text
    
def process_csv(file_path):
    encoding = detect_encoding(file_path)
    df = pd.read_csv(file_path, encoding=encoding)
    return df.to_string()

def process_txt(file_path):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='replace') as file:
        return file.read()