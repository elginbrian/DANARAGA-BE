from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from passlib.context import CryptContext

from app.models.user import UserCreate, UserUpdate, UserInDB, UserPublic

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[UserInDB]:
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[UserInDB]:
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None

async def create_user(db: AsyncIOMotorDatabase, user_in: UserCreate) -> UserPublic:
    user_data = user_in.model_dump()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    user_data["createdAt"] = datetime.utcnow()
    user_data["updatedAt"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)
    
    user_data.pop("hashed_password", None)
    return UserPublic(**user_data)

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[UserPublic]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    user_data = user.model_dump()
    user_data.pop("hashed_password", None)
    return UserPublic(**user_data)

async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: UserUpdate) -> UserPublic:
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updatedAt"] = datetime.utcnow()
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": update_data}
    )
    
    updated_user = await get_user_by_id(db, user_id)
    if updated_user:
        user_data = updated_user.model_dump()
        user_data.pop("hashed_password", None)
        return UserPublic(**user_data)
    
    raise Exception("User not found after update")