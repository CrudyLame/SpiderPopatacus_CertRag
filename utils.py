import os
from docx import Document as DocxDocument
from PyPDF2 import PdfReader

def convert_docx_to_text(file_path):
    doc = DocxDocument(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def convert_pdf_to_text(file_path):
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages])

def load_documents_from_directory(directory_path):
    documents = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename.endswith(".docx"):
            text = convert_docx_to_text(file_path)
        elif filename.endswith(".pdf"):
            text = convert_pdf_to_text(file_path)
        elif filename.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            continue
        documents.append({"content": text, "metadata": {"source": filename}})
    return documents