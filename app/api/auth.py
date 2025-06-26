from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta
from pydantic import BaseModel

from app.core.db import get_database
from app.models.user import UserCreate, UserPublic
from app.models.token import Token
from app.services import user_service
from app.security import create_access_token
from app.core.config import settings

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: UserPublic

@router.post(
    "/register", 
    response_model=UserPublic, 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register_user(
    user_in: UserCreate, 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await user_service.create_user(db=db, user_in=user_in)
    return user

@router.post("/login", response_model=AuthResponse, summary="User login")
async def login(
    login_data: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    user = await user_service.authenticate_user(
        db=db, email=login_data.email, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        token=access_token,
        user=user
    )

@router.post("/token", response_model=Token, summary="OAuth2 compatible login")
async def login_oauth2(
    db: AsyncIOMotorDatabase = Depends(get_database),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await user_service.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}