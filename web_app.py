import streamlit as st
import pandas as pd
import io

# from docx import Document
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import tempfile
from typing import List, Dict
from utils import convert_docx_to_text
import pandas as pd
import random

from rag import CertRAG

cert_rag = CertRAG(rag_type="default")


def process_single_requirement(text):
    compliance_result = cert_rag.cert_documents(text)
    return {
        "Объект": compliance_result["object"],
        # "Регламент": compliance_result["regulation_paragraph"],
        "Тип": compliance_result["type"],
        "Комментарий": compliance_result["comment"],
    }


st.set_page_config(layout="wide")
st.title("📋 Система проверки требований 📋")

tab1, tab2, tab3 = st.tabs(["Новое требование", "Загрузка требований", "Справка"])

with tab1:
    requirement_text = st.text_area("Введите текст требования:")
    if st.button("Проверить 🔎"):
        if requirement_text:
            result = process_single_requirement(requirement_text)
            # Determine the verdict icon
            verdict_icon = (
                "✅"
                if result.get("Тип") in ["0", "1"]
                else "❔" if result.get("Тип") == "2" else "❌"
            )
            st.header(f"Результат проверки {verdict_icon}")

            if "Рекомендация" in result:
                st.markdown(f"**Рекомендация:** {result['Рекомендация']}")

            # Display other items
            for key, value in result.items():
                if key != "Рекомендация":
                    if key == "Комментарий":
                        # Translate the comment to Russian
                        translation_prompt = f"Translate the following text from English to Russian:\n\n{value}\n\nTranslation:"
                        russian_translation = cert_rag.llm.generate_response(
                            translation_prompt, {}
                        )
                        st.markdown(f"**{key}:** {russian_translation}")
                    else:
                        st.markdown(f"**{key}:** {value}")
        else:
            st.warning("Пожалуйста, введите текст требования.")

with tab2:
    # st.header("Загрузка имеющихся требований")
    uploaded_files = st.file_uploader(
        "Загрузите файлы требований (.docx или .txt)",
        accept_multiple_files=True,
        type=["docx", "txt"],
    )
    folder_path = st.text_input("Или укажите путь к папке с требованиями:")

    if st.button("Проверить все 🔎"):
        files_text = []
        if uploaded_files:
            for file in uploaded_files:
                files_text.append((file.name, convert_docx_to_text(file)))
        elif folder_path:
            for filename in os.listdir(folder_path):
                if filename.endswith(".docx") or filename.endswith(".txt"):
                    with open(os.path.join(folder_path, filename), "rb") as file:
                        files_text.append((filename, convert_docx_to_text(file)))

        if files_text:
            results = [cert_rag.cert_documents(text) for _, text in files_text]
            for result in results:
                if result.get("comment"):
                    translation_prompt = f"Translate the following text from English to Russian:\n\n{result['comment']}\n\nTranslation:"
                    result["comment"] = cert_rag.llm.generate_response(
                        translation_prompt, {}
                    )
            st.header("📊 Отчет:")
            correct_count = sum(1 for r in results if r["type"] in ["0", "1", "2"])
            violation_count = len(results) - correct_count
            st.markdown(f"**✅ Корректных требований:** {correct_count}")
            st.markdown(f"**❌ Нарушений:** {violation_count}")

            df = pd.DataFrame(results)
            st.dataframe(df, width=1000)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Report", index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="Скачать (Excel)",
                data=excel_buffer,
                file_name="report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning(
                "Нет файлов для анализа. Пожалуйста, загрузите файлы или укажите корректный путь к папке."
            )

with tab3:
    st.markdown("## 📚 Справка ")
    st.markdown(
        """
        Тип 0: Разрабатываемая система не относится к сертифицируемым объектам. Проверка не требуется.
        """
    )
    st.markdown(
        """
        Тип 1: В кейсе упоминаются сертифицируемые объекты, регламенты соблюдены.
        """
    )
    st.markdown(
        """
        Тип 2: В кейсе упоминаются сертифицируемые объекты, но регламенты накладывают ограничения на сертификацию. В кейсе не описаны эти ограничения. Можно дополнить кейс описаниями ограничений из регламентов.
        """
    )
    st.markdown(
        """
        Тип 3: В кейсе упоминаются сертифицируемые объекты, но требования к разработке ПРОТИВОРЕЧАТ регламентам сертификации. Требуются исправления.
        """
    )
