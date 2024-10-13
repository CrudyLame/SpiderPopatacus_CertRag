from llm import LLMModel
from store import FAISSVectorStore
from typing import List
from raptor.raptor import (
    BaseSummarizationModel,
    BaseQAModel,
    BaseEmbeddingModel,
    RetrievalAugmentationConfig,
)


def reranker(query, retrieved_segments):
    from sentence_transformers import CrossEncoder

    cross_encoder_model = CrossEncoder("cross-encoder/stsb-roberta-base")

    sentence_pairs = [[query, segment] for segment in retrieved_segments]
    similarity_scores = cross_encoder_model.predict(sentence_pairs)

    scored_segments = list(zip(retrieved_segments, similarity_scores))
    scored_segments.sort(key=lambda x: x[1], reverse=True)

    print("Top 5 segments with CrossEncoder scores:")
    for segment, score in scored_segments[:5]:
        print(f"\t{score:.3f}\t{segment[:50]}...")

    print("\n\n========\n")
    return [segment for segment, _ in scored_segments]


class CertRAG:
    def __init__(self, rag_type: str = "default"):
        self.llm = LLMModel()
        self.faiss_vector_store = FAISSVectorStore(index_path="db/faiss_index")
        self.rag_type = rag_type
        # ADD prod raptor as alernative rag

    def cert_documents(self, data: str):
        retrieved_objects = self.faiss_vector_store.search_similar(data, k=6)
        retrieved_segments = [obj for obj, score in retrieved_objects]
        reranked_segments = reranker(data, retrieved_segments)[:2]
        for segment in reranked_segments:
            print(segment)
            print("================================================")
        return self.llm.check_use_case_compliance(data, reranked_segments)

    def banch_documents(self, data: List[str]):
        results = []
        for use_case in data:
            results.append(self.cert_documents(use_case))
        return results
