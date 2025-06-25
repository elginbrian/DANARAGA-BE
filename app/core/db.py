from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = Database()

async def connect_to_mongo():
    print("Menghubungkan ke MongoDB...")
    db_manager.client = AsyncIOMotorClient(settings.MONGO_URI)
    db_manager.db = db_manager.client[settings.MONGO_DB_NAME]
    print(f"Terhubung ke database: {settings.MONGO_DB_NAME}")

async def close_mongo_connection():
    print("Menutup koneksi MongoDB...")
    if db_manager.client:
        db_manager.client.close()
    print("Koneksi ditutup.")

def get_database() -> AsyncIOMotorDatabase:
    if db_manager.db is None:
        raise Exception("Database tidak terhubung. Panggil 'connect_to_mongo' terlebih dahulu.")
    return db_manager.db