from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta

from app.core.db import get_database
from app.models.user import UserCreate, UserPublic
from app.models.token import Token
from app.services import user_service
from app.security import create_access_token
from app.core.config import settings

router = APIRouter()

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
    user = await user_service.create_user(db=db, user_in=user_in)
    return user


@router.post("/login", response_model=Token, summary="User login")
async def login(
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
    
    # Frontend mengharapkan { token: "...", user: {...} }, tapi standar OAuth2 hanya mengembalikan token.
    # Untuk mencocokkan, kita bisa saja mengembalikan user, tapi kita akan tetap pada standar.
    # Frontend perlu menyesuaikan untuk memanggil /users/profile setelah login.
    # Di sini, kita akan tetap pada standar OAuth2.
    return {"access_token": access_token, "token_type": "bearer"}