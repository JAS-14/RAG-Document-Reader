from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from model import RAGhistory
from database import SessionLocal
import os
from rag import RAG
from dotenv import load_dotenv
from .auth import get_current_user
from starlette import status
from pydantic import BaseModel

router = APIRouter(
    prefix="/Ask",
    tags=['AskMe']
)


class SearchRequest(BaseModel):
    query: str


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Single shared RAG instance for the process lifetime.
#
# The original code did `rag = RAG(api_key, pinecone_api_key)` inside
# search_file(), i.e. on every request. That re-opens the Pinecone client
# connection AND reloads the cross-encoder reranker model from disk on every
# single search — by far the most expensive part of a request. It's created
# lazily on first use and reused after that.
_rag_instance: Optional[RAG] = None


def get_rag() -> RAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAG(api_key, pinecone_api_key)
    return _rag_instance


@router.get("/", status_code=status.HTTP_200_OK)
async def chat(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(RAGhistory).filter(RAGhistory.user_id == user.get('id')).all()


@router.post("/upload")
async def upload_file(user: user_dependency, file: UploadFile = File(...)):
    """
    Save the uploaded PDF and incrementally ingest just this file (chunk ->
    embed -> upsert). This does NOT touch any other document already in the
    index. Re-uploading the same filename replaces only that file's chunks
    (see RAG.add_document / delete_document) instead of re-processing and
    re-upserting every PDF ever uploaded, which is what happened before.
    """
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    rag = get_rag()
    chunk_count = rag.add_document(file_path)

    return {
        "message": f"'{file.filename}' uploaded and indexed successfully",
        "chunks_indexed": chunk_count,
    }


@router.get("/documents")
async def list_documents(user: user_dependency):
    """List distinct source filenames currently indexed — useful for a document-management UI."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    rag = get_rag()
    sources = sorted({r["source"] for r in rag.bm25_corpus})
    return {"documents": sources}


@router.delete("/documents/{filename}")
async def delete_document(filename: str, user: user_dependency):
    """Remove a single document's chunks from the index without affecting anything else."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    rag = get_rag()
    deleted_count = rag.delete_document(filename)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"No indexed chunks found for '{filename}'")

    return {"message": f"Removed {deleted_count} chunks for '{filename}'"}


@router.post("/search")
async def search_file(request: SearchRequest, db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    rag = get_rag()

    if rag.bm25 is None:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet. Upload a PDF via /Ask/upload first.",
        )

    result = rag.response_generation(request.query)

    rag_record = RAGhistory(
        user_id=user.get('id'),
        query=request.query,
        answer=result["answer"], 
    )

    db.add(rag_record)
    db.commit()
    db.refresh(rag_record)

    return {
        "query": request.query,
        "answer": result["answer"],
        "sources": result["sources"],
    }


@router.get("/history")
def get_history(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return db.query(RAGhistory).filter(RAGhistory.user_id == user.get("id")).all()


@router.delete("/delete_history")
async def delete_history(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    db.query(RAGhistory).filter(RAGhistory.user_id == user.get('id')).delete()
    db.commit()

    return {"message": "Chat history deleted"}