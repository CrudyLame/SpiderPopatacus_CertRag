import streamlit as st
import pandas as pd
import io
import os
from utils import convert_docx_to_text
import pandas as pd
from utils import generate_pdf_report
from rag import CertRAG

cert_rag = CertRAG(rag_type="default")


def process_single_requirement(text):
    compliance_result = cert_rag.cert_documents(text)
    return {
        "Объект": compliance_result["object"],
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
            verdict_icon = (
                "✅"
                if result.get("Тип") in ["0", "1"]
                else "❔" if result.get("Тип") == "2" else "❌"
            )
            st.header(f"Результат проверки {verdict_icon}")

            if "Рекомендация" in result:
                st.markdown(f"**Рекомендация:** {result['Рекомендация']}")

            for key, value in result.items():
                if key != "Рекомендация":
                    if key == "Комментарий":

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
            # results = [cert_rag.cert_documents(text) for _, text in files_text]
            results = [
                {"filename": filename, **cert_rag.cert_documents(text)}
                for filename, text in files_text
            ]

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
            df.rename(columns={"object": "Объект"}, inplace=True)
            df.rename(columns={"type": "Тип"}, inplace=True)
            df.rename(columns={"comment": "Комментарий"}, inplace=True)
            df.rename(columns={"filename": "Файл"}, inplace=True)
            st.dataframe(df, width=1000)

            pdf_buffer = generate_pdf_report(df, correct_count, violation_count)

            st.download_button(
                label="Скачать (PDF)",
                data=pdf_buffer,
                file_name="report.pdf",
                mime="application/pdf",
            )

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
