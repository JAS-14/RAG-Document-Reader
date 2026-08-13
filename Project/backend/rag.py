import json
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pinecone import Pinecone, ServerlessSpec

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder


load_dotenv()


class RAG:
    """
    Encapsulates the complete Retrieval-Augmented Generation workflow.

    Pipeline:
      load -> chunk -> embed -> upsert (dense, Pinecone) + index (sparse, BM25)
            -> hybrid retrieve (RRF fusion) -> cross-encoder rerank
            -> cited answer generation

    Also exposes `evaluate()` to score the pipeline end-to-end with RAGAS.
    """

    def __init__(
        self,
        api_key: str,
        pinecone_api_key: str,
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        store_path: str = "chunk_store.json",
    ):
        self.client = OpenAI(api_key=api_key)

        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )
        self.pc = Pinecone(api_key=pinecone_api_key)

        self.index_name = "rag-index"

        existing_indexes = [index["name"] for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        self.index = self.pc.Index(self.index_name)

        # Local cross-encoder reranker. Runs on CPU, no extra API cost/key needed.
        self.reranker = CrossEncoder(rerank_model)

        self.bm25 = None
        self.bm25_corpus: List[Dict[str, Any]] = []  # [{id, text, page, source}]

        self.store_path = store_path
        self._load_store()

    def _load_store(self):
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                self.bm25_corpus = json.load(f)
            self._rebuild_bm25()

    def _save_store(self):
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.bm25_corpus, f)

    def _rebuild_bm25(self):
        if not self.bm25_corpus:
            self.bm25 = None
            return
        tokenized_corpus = [r["text"].lower().split() for r in self.bm25_corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def _load_single_pdf(self, path: str, source_name: str):
        loader = PyPDFLoader(path)
        loaded = loader.load()
        for d in loaded:
            d.metadata["source"] = source_name
        return loaded

    def load_document(self, folder_path: str):
        """Load every PDF in a folder. Used for bulk/initial ingestion (see vector_database)."""
        docs = []
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                docs.extend(self._load_single_pdf(os.path.join(folder_path, filename), filename))
        return docs

    def chunk_document(
        self,
        documents,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_chars: int = 40,
    ):
        """
        Structure-aware recursive chunking.

        Improvements over a plain fixed-size splitter:
        - Sentence/clause-aware separator priority (paragraph -> line ->
          sentence -> clause -> word) so chunks don't get cut mid-sentence.
        - Smaller chunk_size (800 vs 1000) with overlap (150) gives tighter,
          more precise retrieval units, which matters more once we're
          reranking a wider candidate pool rather than trusting top-k alone.
        - Any resulting chunk shorter than `min_chunk_chars` (e.g. a stray
          header or page-break artifact) gets merged into the previous chunk
          instead of becoming a near-empty, useless vector.
        - Every chunk is tagged with a stable chunk_id + source filename +
          page number so it can be cited in the final answer.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""],
        )
        raw_chunks = splitter.split_documents(documents)

        merged = []
        for chunk in raw_chunks:
            if merged and len(chunk.page_content.strip()) < min_chunk_chars:
                merged[-1].page_content += " " + chunk.page_content.strip()
            else:
                merged.append(chunk)

        for i, chunk in enumerate(merged):
            source = chunk.metadata.get("source", "doc")
            page = chunk.metadata.get("page", 0)
            chunk.metadata["chunk_id"] = f"{source}-p{page}-{i}"

        return merged

    def embedding(self, chunks):
        texts = [doc.page_content for doc in chunks]
        return self.embedding_model.embed_documents(texts)

    def _chunks_to_records(self, chunks, embeddings):
        vectors, records = [], []
        for chunk, emb in zip(chunks, embeddings):
            cid = chunk.metadata["chunk_id"]
            record = {
                "id": cid,
                "text": chunk.page_content,
                "page": chunk.metadata.get("page", 0),
                "source": chunk.metadata.get("source", "unknown"),
            }
            vectors.append({"id": cid, "values": emb, "metadata": record})
            records.append(record)
        return vectors, records

    def vector_database(self, chunks):
        """
        Bulk (re)ingestion: wipes the ENTIRE index and rebuilds it from the
        given chunks. Useful for a full rebuild (e.g. after changing the
        chunking strategy) but NOT what day-to-day uploads should call --
        use add_document() for that, which only touches one file's chunks.
        """
        try:
            self.index.delete(delete_all=True)
        except Exception as e:
            # Pinecone raises if the index/namespace is already empty on some
            # plans -- safe to ignore, there's nothing to clear.
            print(f"Index clear skipped (likely already empty): {e}")

        embeddings = self.embedding(chunks)
        vectors, records = self._chunks_to_records(chunks, embeddings)

        if vectors:
            self.index.upsert(vectors=vectors)

        self.bm25_corpus = records
        self._rebuild_bm25()
        self._save_store()

        print(f"Uploaded {len(vectors)} chunks to Pinecone and indexed them for BM25.")

    def add_document(self, file_path: str) -> int:
        """
        Incrementally ingest a single PDF: chunk -> embed -> upsert just this
        file's vectors, without touching anything else already indexed.

        If this filename was already indexed, its old chunks are removed
        first (by exact chunk ID, not a full index wipe) so a re-upload
        replaces that file's content instead of duplicating or stacking on
        top of it. Returns the number of chunks indexed.
        """
        source_name = os.path.basename(file_path)

        self.delete_document(source_name)

        docs = self._load_single_pdf(file_path, source_name)
        chunks = self.chunk_document(docs)
        embeddings = self.embedding(chunks)
        vectors, records = self._chunks_to_records(chunks, embeddings)

        if vectors:
            self.index.upsert(vectors=vectors)

        self.bm25_corpus.extend(records)
        self._rebuild_bm25()
        self._save_store()

        print(f"Indexed {len(vectors)} chunks from '{source_name}'.")
        return len(vectors)

    def delete_document(self, source_name: str) -> int:
        """
        Remove every chunk belonging to one source filename, from both
        Pinecone and the local BM25 store, without affecting any other
        document. Returns the number of chunks removed.

        Deletes by explicit chunk ID (collected from the local store) rather
        than a Pinecone metadata filter, since filtered delete isn't
        guaranteed to be available on every Pinecone plan/index type --
        delete-by-ID always is.
        """
        ids_to_delete = [r["id"] for r in self.bm25_corpus if r["source"] == source_name]

        if ids_to_delete:
            self.index.delete(ids=ids_to_delete)

        self.bm25_corpus = [r for r in self.bm25_corpus if r["source"] != source_name]
        self._rebuild_bm25()
        self._save_store()

        return len(ids_to_delete)

    # ------------------------------------------------------------------
    # Retrieval: hybrid search (dense + sparse, fused with RRF) + rerank
    # ------------------------------------------------------------------

    def _dense_search(self, query: str, top_k: int = 10):
        query_embedding = self.embedding_model.embed_query(query)
        result = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        return [(m["id"], m["metadata"]) for m in result.matches]

    def _sparse_search(self, query: str, top_k: int = 10):
        if self.bm25 is None:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.bm25_corpus[i]["id"], self.bm25_corpus[i]) for i in ranked_idx]

    def hybrid_search(self, query: str, top_k: int = 10, rrf_k: int = 60):
        """
        Fuse dense (Pinecone cosine) and sparse (BM25) rankings with
        Reciprocal Rank Fusion (RRF):

            score(doc) = sum over each ranker of  1 / (rrf_k + rank_in_that_ranker)

        RRF is used instead of a weighted blend of raw scores because cosine
        similarity and BM25 scores live on different, incomparable scales.
        RRF only needs each ranker's *rank order*, so it's robust without any
        score normalization or per-dataset tuning. `rrf_k` (60 is the
        standard default from the original RRF paper) just controls how
        quickly the weight of lower ranks decays.
        """
        dense_results = self._dense_search(query, top_k=top_k)
        sparse_results = self._sparse_search(query, top_k=top_k)

        fused_scores: Dict[str, float] = {}
        doc_lookup: Dict[str, Dict[str, Any]] = {}

        for rank, (doc_id, meta) in enumerate(dense_results):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            doc_lookup[doc_id] = meta

        for rank, (doc_id, meta) in enumerate(sparse_results):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            doc_lookup.setdefault(doc_id, meta)

        ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        return [doc_lookup[i] for i in ranked_ids]

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 5):
        """
        Cross-encoder reranking over the fused hybrid candidates.

        Hybrid search is tuned for *recall* (cast a wide net across dense +
        keyword signals); the RRF score is only a rough proxy for relevance.
        A cross-encoder jointly attends over (query, passage) pairs and
        produces a much more accurate relevance score, so it's used to
        re-sort and trim the candidate pool down to what actually gets sent
        to the LLM.
        """
        if not candidates:
            return []
        pairs = [(query, c["text"]) for c in candidates]
        scores = self.reranker.predict(pairs)
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)[:top_n]

    def query_processing(self, query: str, hybrid_top_k: int = 10, rerank_top_n: int = 5):
        candidates = self.hybrid_search(query, top_k=hybrid_top_k)
        return self.rerank(query, candidates, top_n=rerank_top_n)

    # ------------------------------------------------------------------
    # Generation with inline citations
    # ------------------------------------------------------------------

    def _generate_from_chunks(self, query: str, top_chunks: List[Dict[str, Any]]):
        if not top_chunks:
            return {"answer": "I don't know based on the provided context.", "sources": []}

        context_blocks = []
        sources = []
        for i, chunk in enumerate(top_chunks, start=1):
            label = f"[{i}]"
            # Defensive .get() with defaults: guards against any leftover
            # vectors from an older metadata schema (or a partially-failed
            # upsert) missing a field, instead of crashing the whole request.
            text = chunk.get("text", "")
            source = chunk.get("source", "unknown")
            page = chunk.get("page", 0)

            context_blocks.append(f"{label} (source: {source}, page {page})\n{text}")
            sources.append(
                {
                    "label": label,
                    "source": source,
                    "page": page,
                    "snippet": text[:200],
                    "relevance_score": chunk.get("rerank_score"),
                }
            )

        context = "\n\n".join(context_blocks)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant.\n\n"
                        "Rules:\n"
                        "- Answer only using the provided context.\n"
                        "- If the answer is not present in the context, reply: "
                        "'I don't know based on the provided context.'\n"
                        "- Format the answer using Markdown bullet points.\n"
                        "- Keep each bullet concise.\n"
                        "- Highlight important terms using **bold**.\n"
                        "- Do not invent information.\n"
                        "- After every claim, cite the source using its bracketed "
                        "label exactly as given in the context, e.g. [1]. Use "
                        "multiple labels like [1][2] if a claim draws on more "
                        "than one source."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
                                Context:
                                {context}

                                Question:
                                {query}
                                """,
                },
            ],
        )

        return {"answer": response.choices[0].message.content, "sources": sources}

    def response_generation(self, query: str):
        top_chunks = self.query_processing(query)
        return self._generate_from_chunks(query, top_chunks)

    # ------------------------------------------------------------------
    # Evaluation harness (RAGAS)
    # ------------------------------------------------------------------

    def evaluate(self, test_set: List[Dict[str, str]]):
        """
        Run the actual end-to-end pipeline (retrieval + rerank + generation,
        not a mock) over a labeled test set and score it with RAGAS.

        test_set: list of {"question": str, "ground_truth": str}

        Metrics:
        - faithfulness:      is the answer grounded in the retrieved context
                              (i.e. did the model hallucinate)?
        - answer_relevancy:  does the answer actually address the question?
        - context_precision: how much of the retrieved context is relevant?
        - context_recall:    did retrieval surface the info needed to answer
                              (vs. missing it entirely)?

        Requires: pip install ragas datasets
        """
        from datasets import Dataset
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        questions, answers, contexts_list, ground_truths = [], [], [], []

        for item in test_set:
            question = item["question"]
            top_chunks = self.query_processing(question)
            result = self._generate_from_chunks(question, top_chunks)

            questions.append(question)
            answers.append(result["answer"])
            contexts_list.append([c["text"] for c in top_chunks])
            ground_truths.append(item["ground_truth"])

        eval_dataset = Dataset.from_dict(
            {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
                "ground_truth": ground_truths,
            }
        )

        results = ragas_evaluate(
            eval_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )

        return results.to_pandas()


if __name__ == "__main__":
    # Example: incrementally ingest every PDF currently in uploads/, then run
    # a small evaluation over a hand-labeled test set.
    # Set OPENAI_API_KEY / PINECONE_API_KEY first.
    rag = RAG(api_key=os.getenv("OPENAI_API_KEY"), pinecone_api_key=os.getenv("PINECONE_API_KEY"))

    upload_folder = "uploads"
    for filename in os.listdir(upload_folder):
        if filename.endswith(".pdf"):
            rag.add_document(os.path.join(upload_folder, filename))

    test_set = [
        {"question": "What is this document about?", "ground_truth": "..."},
        # add more labeled question / ground_truth pairs
    ]

    df = rag.evaluate(test_set)
    print(df)