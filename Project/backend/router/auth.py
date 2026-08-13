from fastapi import APIRouter , HTTPException , Depends 
from model import User
from datetime import timezone , datetime , timedelta
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt , JWTError
from starlette import status
import os
from dotenv import load_dotenv

load_dotenv()


router = APIRouter(
    prefix='/auth',
    tags=['/auth']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally :
        db.close()

class CreateUser(BaseModel):
    name : str
    email : str 
    password : str  

class Token(BaseModel):
    access_token : str
    token_type:str

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = '/auth/token')

db_dependency = Annotated[Session , Depends(get_db)]

def authenticate_user(username:str , password:str,db):
    user = db.query(User).filter(User.name==username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_token(username:str , user_id :int ,expire_delta:timedelta):
    encode = {'sub':username,'id':user_id}
    expires = datetime.now(timezone.utc)+expire_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm =ALGORITHM)

async def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token , SECRET_KEY , algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id : int =payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = 'COULD NOT VALIDATE USER')

        return {'username':username,'id':user_id}
    except JWTError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail='COULD NOT VALIDATE USER')

@router.post('/create-user')
async def create_user(db:db_dependency,create_user_request:CreateUser):
    existing_user = db.query(User).filter(
        (User.email == create_user_request.email) |
        (User.name == create_user_request.name)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )
    create_user_model = User(
        email = create_user_request.email,
        name = create_user_request.name,
        hashed_password = bcrypt_context.hash(create_user_request.password)
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)

@router.post('/token',response_model=Token)
async def login_success(formData:Annotated[OAuth2PasswordRequestForm,Depends()],db:db_dependency):
    user = authenticate_user(formData.username, formData.password,db)
    if not user :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="COULD'NT VALIDATE")
    token = create_token(user.name,user.id ,timedelta(minutes=30))
    return {'access_token':token , 'token_type':'bearer'}
