import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_support_saas")

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,
    )
    await client.admin.command("ping")
    db = client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")


async def close_db():
    global client, db
    if client is not None:
        client.close()
    client = None
    db = None
    print("MongoDB connection closed")


async def get_db():
    if db is None:
        raise RuntimeError("Database has not been initialized")
    return db


def get_database():
    if db is None:
        raise RuntimeError("Database has not been initialized")
    return db
