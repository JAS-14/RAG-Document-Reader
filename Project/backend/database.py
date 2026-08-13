from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pymysql
from dotenv import load_dotenv
load_dotenv()
import os

DATABASE_URL = os.getenv("DATABASE_URL")
pymysql.install_as_MySQLdb()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()