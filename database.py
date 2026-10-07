from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

class Base(DeclarativeBase):
    pass

dburl=os.getenv("database_url")
engine=create_async_engine(
    dburl,
    echo=False
   )
   
SessionLocal=async_sessionmaker(
    bind=engine,
    expire_on_commit=False
    )

async def get_db():
   async with SessionLocal() as db:
        yield db