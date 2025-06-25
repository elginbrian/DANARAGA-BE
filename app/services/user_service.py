from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserCreate, UserInDB, UserPublic
from app.security import get_password_hash, verify_password

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> UserInDB | None:
    user_row = await db["users"].find_one({"email": email.lower()})
    if user_row:
        return UserInDB(**user_row)
    return None

async def create_user(db: AsyncIOMotorDatabase, user_in: UserCreate) -> UserPublic:
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    hashed_password = get_password_hash(user_in.password)
    
    user_db_data = user_in.model_dump(exclude={"password"})
    user_db_data["hashed_password"] = hashed_password
    
    new_user = await db["users"].insert_one(user_db_data)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    
    return UserPublic(**created_user)

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> UserInDB | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
        
    if not verify_password(password, user.hashed_password):
        return None
        
    return user