
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="reshwanth@2006",
    host="127.0.0.1",
    port=3306,
    database="ecommerce_db"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
