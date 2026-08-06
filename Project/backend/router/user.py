from fastapi import APIRouter, APIRouter , HTTPException , Depends
from database import SessionLocal
from typing import Annotated
from model import User
from .auth import bcrypt_context, get_current_user
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from pydantic import BaseModel,Field


router = APIRouter(
    prefix='/User',
    tags=['/User']
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()
db_dependency = Annotated[Session , Depends(get_db)]
user_dependency = Annotated[dict , Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

class user_authorization(BaseModel):
    password:str
    hasshed_pasword : str = Field(min_length=6)

@router.get("/",status_code = status.HTTP_200_OK)
async def get_users(user:user_dependency , db:db_dependency):
    if user is None:
        raise HTTPException(status_code=401,detail='AUTHENTICATION FAILED')
    return db.query(User).filter(User.id == user.get('id')).first()

@router.put('/update_password',status_code = status.HTTP_204_NO_CONTENT)
async def update_password(user:user_dependency , db:db_dependency , user_verification:user_authorization):
    if user is None:
        raise HTTPException(status_code = 401 , detail='Authentication failed')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verification.password,user_verification.hashed_password):
        raise HTTPException(status_code = 401 , detail='Incorrect Password')
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
    