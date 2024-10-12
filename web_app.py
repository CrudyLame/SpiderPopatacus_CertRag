import streamlit as st
import pandas as pd
import io
# from docx import Document
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import tempfile

from rag import CertRAG

cert_rag = CertRAG(rag_type="default")

def analyze_requirement(text):
    # Placeholder function for requirement analysis
    # In a real implementation, this would use NLP techniques
    if "тормозная система" in text.lower():
        return "тормозная система", "Требования к тормозной системе: ...", "Соблюдается", ""
    return "Неизвестный объект", "Нет данных", "Не соблюдается", "Уточните объект сертификации"

def process_single_requirement(text):
    compliance_result = cert_rag.cert_documents(text)
    return {
        "Объект": compliance_result["object"],
        "Регламент": compliance_result["regulation"],
        "Вердикт": compliance_result["verdict"],
        "Рекомендация": compliance_result["recommendation"]
    }

def process_file(file):
    # if file.name.endswith('.docx'):
    #     doc = Document(file)
    #     text = "\n".join([para.text for para in doc.paragraphs])
    # else:
    text = file.getvalue().decode()
    return process_single_requirement(text)

def generate_pdf_report(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    data_list = [[k, v] for item in data for k, v in item.items()]
    t = Table(data_list)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

st.title("Система проверки требований на соответствие регламентам сертификации")

tab1, tab2 = st.tabs(["Новое требование", "Загрузка требований"])

with tab1:
    requirement_text = st.text_area("Введите текст требования:")
    if st.button("Проверка"):
        if requirement_text:
            result = process_single_requirement(requirement_text)
            st.header("Результат проверки")
            
            if "Рекомендация" in result:
                st.markdown(f"**Рекомендация:** {result['Рекомендация']}")
            
            # Display other items
            for key, value in result.items():
                if key != "Рекомендация":
                    st.markdown(f"**{key}:** {value}")
        else:
            st.warning("Пожалуйста, введите текст требования.")

with tab2:
    st.header("Загрузка имеющихся требований")
    uploaded_files = st.file_uploader("Загрузите файлы требований (.docx или .txt)", accept_multiple_files=True, type=['docx', 'txt'])
    folder_path = st.text_input("Или укажите путь к папке с требованиями:")

    if st.button("Анализировать файлы"):
        results = []
        if uploaded_files:
            for file in uploaded_files:
                results.append(process_file(file))
        elif folder_path:
            for filename in os.listdir(folder_path):
                if filename.endswith('.docx') or filename.endswith('.txt'):
                    with open(os.path.join(folder_path, filename), 'rb') as file:
                        results.append(process_file(file))
        
        if results:
            st.write("Краткий отчет:")
            correct_count = sum(1 for r in results if r['Вердикт'] == 'Соблюдается')
            violation_count = len(results) - correct_count
            st.write(f"Корректных требований: {correct_count}")
            st.write(f"Нарушений: {violation_count}")

            df = pd.DataFrame(results)
            st.dataframe(df)

            pdf_buffer = generate_pdf_report(results)
            st.download_button(
                label="Скачать подробный отчет (PDF)",
                data=pdf_buffer,
                file_name="report.pdf",
                mime="application/pdf"
            )

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="Скачать подробный отчет (Excel)",
                data=excel_buffer,
                file_name="report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Нет файлов для анализа. Пожалуйста, загрузите файлы или укажите корректный путь к папке.")
