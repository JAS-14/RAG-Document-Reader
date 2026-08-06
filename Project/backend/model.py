from sqlalchemy import Column , Text , Integer , ForeignKey
from database import Base

class RAGhistory(Base):
    __tablename__ = "rag"

    session_id = Column(Integer , primary_key = True)
    query = Column(Text)
    answer = Column(Text)
    user_id = Column(Integer, ForeignKey('user.id'))

class User(Base):
    __tablename__ = "user"
    id = Column(Integer , primary_key = True)
    name = Column(Text)
    email = Column(Text)
    hashed_password = Column(Text)