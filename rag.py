from llm import LLMModel
from store import FAISSVectorStore
from typing import List

# ADD RERANKER
# ADD RAPTOR

class CertRAG:
    def __init__(self, rag_type: str = "default"):
        self.llm = LLMModel()
        self.faiss_vector_store = FAISSVectorStore(path="db/faiss_index")
        self.rag_type = rag_type
        
    def cert_documents(self, data: str):
        retrieved_objects = self.faiss_vector_store.search_similar(data, k=6)
        retrieved_segments = [obj for obj, score in retrieved_objects]
        for segment in retrieved_segments:
            print(segment)
            print("================================================")
        return self.llm.check_use_case_compliance(data, retrieved_segments)
    
    def banch_documents(self, data: List[str]):
        results = []
        for use_case in data:
            results.append(self.cert_documents(use_case))
        return results
