import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Use env var if present, otherwise default to sqlite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pytalk.db")

# For sqlite we need connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = MetaData()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
