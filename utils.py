import os
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def convert_docx_to_text(file_path):
    doc = DocxDocument(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def generate_pdf_report(data, correct_count, violation_count):
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    style_heading = styles["Heading1"]
    style_heading.fontName = "DejaVuSans"
    style_normal = styles["Normal"]
    style_normal.fontName = "DejaVuSans"

    elements = []
    elements.append(Paragraph("Отчет: ", style_heading))
    elements.append(
        Paragraph(f"✅ Корректных требований: {correct_count}", style_normal)
    )
    elements.append(Paragraph(f"❌ Нарушений: {violation_count}", style_normal))

    table_data = [data.columns.tolist()] + data.values.tolist()

    table = Table(table_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)

    pdf_buffer.seek(0)
    return pdf_buffer


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
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
        else:
            continue
        documents.append({"content": text, "metadata": {"source": filename}})
    return documents
