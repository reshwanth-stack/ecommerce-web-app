
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing.")

DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+pg8000://",
    1
)

url = make_url(DATABASE_URL)

# Remove parameters unsupported by pg8000
url = url.difference_update_query(["sslmode", "channel_binding"])

engine = create_engine(
    url,
    connect_args={"ssl_context": True},
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
