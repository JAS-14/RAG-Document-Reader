from fastapi import APIRouter,Depends ,File ,UploadFile
from typing import Annotated
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
from pydantic import BaseModel

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


db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict , Depends(get_current_user)]
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

@router.get("/",status_code=status.HTTP_200_OK)
async def chat(db:db_dependency , user:user_dependency):
    if user is None:
        raise HTTPException(status_code=401,details='Authentication Failed')
    return db.query(RAGhistory).filter(RAGhistory.user_id==user.get('id')).all()

@router.post("/upload")
async def upload_file(file:UploadFile=File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path , "wb") as buffer:
        buffer.write(await file.read())
    print("Succesfully uploaded the file")


@router.post("/search")
async def search_file(request: SearchRequest, db: db_dependency,user:user_dependency):

    if user is None:
        raise HTTPExcetion(status_code=401,details='Authentication failed')

    rag = RAG(api_key, pinecone_api_key)

    documents = rag.load_document("uploads")

    chunks = rag.chunk_document(documents)

    rag.vector_database(chunks)

    response = rag.response_generation(request.query)

    rag_record = RAGhistory(
        user_id = user.get('id'),
        query=request.query,
        answer=response,
    )

    db.add(rag_record)
    db.commit()
    db.refresh(rag_record)

    return {
        "query": request.query,
        "answer": response
    }

@router.get("/history")
def get_history(db: db_dependency,user: user_dependency):
    if user is None:
        raise HTTPException(
            status_code=401,    
            detail="Authentication Failed"
        )
    response =  db.query(RAGhistory).filter(RAGhistory.user_id == user.get("id")).all()

    return (
        response
    )

@router.delete("/delete_history")
async def delete_history(db:db_dependency,user:user_dependency):
    if user is None:
        raise HTTPException(status_code=401 , details="Authentication Failed")
    db.query(RAGhistory).filter(RAGhistory == user.get('id')).delete()

    db.commit()

    return{
        "message":"Chat history deleted"
    }