# app/api/users.py

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_database
from app.models.user import UserPublic, UserUpdate
from app.security import get_current_active_user
from app.services import user_service

router = APIRouter()

@router.get("/profile", response_model=UserPublic, summary="Get current user profile")
async def read_current_user_profile(
    current_user: UserPublic = Depends(get_current_active_user)
):
    return current_user

@router.patch("/profile", response_model=UserPublic, summary="Update current user profile")
async def update_current_user_profile(
    user_update: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user)
):
    updated_user = await user_service.update_user(db, user_id=current_user.id, user_update=user_update)
    return updated_user