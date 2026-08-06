import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec


load_dotenv()


class RAG:
    """
    Encapsulates the complete Retrieval-Augmented Generation workflow.

    Responsibilities:
    - Load PDF documents
    - Split documents into semantic chunks
    - Generate vector embeddings
    - Store and retrieve vectors from Pinecone
    - Generate context-aware responses using an LLM
    """

    def __init__(self,api_key: str, pinecone_api_key: str):

        self.client = OpenAI(api_key=api_key)

        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )
        self.pc = Pinecone(api_key=pinecone_api_key)

        self.index_name = "rag-index"

        existing_indexes = [
            index["name"]
            for index in self.pc.list_indexes()
        ]

        if self.index_name not in existing_indexes:

            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

        self.index = self.pc.Index(self.index_name)

    # Load PDF

    def load_document(self, folder_path):
        docs = []
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                path = os.path.join(folder_path, filename)
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
        return docs


    # Split PDF

    def chunk_document(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = splitter.split_documents(documents)

        return chunks

    # Create embeddings

    def embedding(self, chunks):

        texts = [doc.page_content for doc in chunks]

        embeddings = self.embedding_model.embed_documents(texts)

        return embeddings

    # Store vectors in Pinecone

    def vector_database(self, chunks):

        embeddings = self.embedding(chunks)

        vectors = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

            vectors.append(
                {
                    "id": f"chunk-{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk.page_content,
                        "page": chunk.metadata.get("page", 0)
                    }
                }
            )

        self.index.upsert(vectors=vectors)

        print("Documents uploaded successfully!")

    # Retrieve similar chunks
    def query_processing(self, query):

        query_embedding = self.embedding_model.embed_query(query)

        result = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )

        return result.matches
        
    # Generate answer

    def response_generation(self, query):

        matches = self.query_processing(query)

        context = ""

        for match in matches:
            context += match["metadata"]["text"] + "\n\n"

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
        "- Do not invent information."
    ),
},
                {
                    "role": "user",
                    "content": f"""
                                Context:
                                {context}

                                Question:
                                {query}
                                """
                                                }
                                            ]
                                        )

        return response.choices[0].message.content