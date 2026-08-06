from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pymysql

pymysql.install_as_MySQLdb()

DATABASE_URL = "mysql+pymysql://root:Jaspreet1420047@localhost/RAG"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()