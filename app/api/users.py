from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any

from app.core.db import get_database
from app.models.user import UserPublic, UserUpdate
from app.security import get_current_active_user
from app.services import user_service

router = APIRouter()

@router.get("/profile", summary="Get current user profile")
async def read_current_user_profile(
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, UserPublic]:
    return {"user": current_user}

@router.patch("/profile", summary="Update current user profile")
async def update_current_user_profile(
    user_update: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, UserPublic]:
    updated_user = await user_service.update_user(db, user_id=current_user.id, user_update=user_update)
    return {"user": updated_user}