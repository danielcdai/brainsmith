from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from cortex.config import settings

Base: DeclarativeMeta = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


# Configure the engine with PostgreSQL connection details
# TODO: Make the Database URL configurable
# TODO: investigate how to enable psycopg2
DATABASE_URL = f"postgresql+psycopg2://postgres:{settings.postgres_password}@{settings.postgre_host}:{settings.postgre_port}/postgres" 
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
# Create a session factory for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Dependency to provide a database session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()