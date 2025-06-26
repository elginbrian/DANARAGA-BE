from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.models.user import UserCreate, UserUpdate, UserInDB, UserPublic
from app.security import get_password_hash, verify_password

def fix_user_id(user_doc):
    if user_doc and "_id" in user_doc:
        user_doc["id"] = str(user_doc["_id"])
    return user_doc

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> UserInDB | None:
    user_doc = await db["users"].find_one({"email": email.lower()})
    if user_doc:
        return UserInDB(**fix_user_id(user_doc))
    return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserInDB | None:
    if not ObjectId.is_valid(user_id):
        return None
    user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return UserInDB(**fix_user_id(user_doc))
    return None

async def create_user(db: AsyncIOMotorDatabase, user_in: UserCreate) -> UserPublic:
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar.",
        )

    hashed_password = get_password_hash(user_in.password)
    
    user_db_data = user_in.model_dump()
    del user_db_data["password"]
    user_db_data["hashed_password"] = hashed_password
    user_db_data["createdAt"] = datetime.utcnow()
    user_db_data["updatedAt"] = datetime.utcnow()

    new_user_result = await db["users"].insert_one(user_db_data)
    
    created_user_doc = await db["users"].find_one({"_id": new_user_result.inserted_id})
    
    return UserPublic(**fix_user_id(created_user_doc))

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> UserInDB | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: UserUpdate) -> UserPublic | None:
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        current_user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
        return UserPublic(**fix_user_id(current_user_doc))

    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    update_data["updatedAt"] = datetime.utcnow()

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    updated_user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    if updated_user_doc:
        return UserPublic(**fix_user_id(updated_user_doc))
    return None