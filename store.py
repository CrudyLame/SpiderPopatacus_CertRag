import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from llm import LLMModel
from utils import load_documents_from_directory
from tqdm import tqdm
import json

class FAISSVectorStore:
    def __init__(self, model_name_or_path="sentence-transformers/all-MiniLM-L6-v2", index_path="data/faiss_index", documents_path="RegDocs"):
        self.model_name_or_path = model_name_or_path
        self.index_path = index_path
        self.documents_path = documents_path
        self.llm_model = LLMModel(model_type="CHATGPT-4o-mini", temperature=0.05)  # ПОТОМ МОЖНО БУДЕТ ЗДЕСЬ ИНИЦИАЛИЗИРОВАТЬ ПРИ ПОМОЩИ обычной 4o, но пока чтобы делать больше экспериментов юзаем 4o-mini

        # Проверяем, существует ли FAISS индекс
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path,
                HuggingFaceEmbeddings(model_name=model_name_or_path),
                allow_dangerous_deserialization=True,
            )
            print(f"Loaded existing FAISS index from {self.index_path}")
        else:
            documents = load_documents_from_directory(self.documents_path)
            if documents:
                self.create_faiss_index(documents)
                self.vector_store = FAISS.load_local(
                    self.index_path,
                    HuggingFaceEmbeddings(model_name=model_name_or_path),
                    allow_dangerous_deserialization=True,
                )
            else:
                raise FileNotFoundError("No FAISS index found and no documents available to create one.")

    def create_faiss_index(self, documents):
        # Разбиение документов на части
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=220, chunk_overlap=100
        )

        doc_splits = []
        for doc in documents:
            doc_obj = Document(page_content=doc["content"], metadata=doc["metadata"])
            splits = text_splitter.split_documents([doc_obj])
            doc_splits.extend(splits)

        # Создание документов для FAISS
        documents_for_faiss = []
        for i, split in enumerate(doc_splits):
            documents_for_faiss.append(Document(page_content=split.page_content, metadata={"chunk_id": i+1}))

        # Создание векторного хранилища FAISS
        embedding_model = HuggingFaceEmbeddings(model_name=self.model_name_or_path)
        vector_store = FAISS.from_documents(documents_for_faiss, embedding_model)

        # Сохранение индекса
        vector_store.save_local(self.index_path)
        print(f"FAISS index saved to {self.index_path}")

    def search_similar(self, query, k=2):
        results = self.vector_store.similarity_search_with_score(query=query, k=k)
        return [(doc.page_content, score) for doc, score in results]
