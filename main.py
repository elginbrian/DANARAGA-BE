from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.db import connect_to_mongo, close_mongo_connection

from app.api import auth, users, facilities, expense, microfunding

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Memulai Danaraga API")
    await connect_to_mongo()
    yield
    await close_mongo_connection()
    print("Danaraga API Telah Berhenti")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",         
    redoc_url=f"{settings.API_V1_STR}/redoc",       
    lifespan=lifespan                             
)

print("Mendaftarkan router")
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(expense.router, prefix=f"{settings.API_V1_STR}/expenses", tags=["Expenses"])
app.include_router(facilities.router, prefix=f"{settings.API_V1_STR}/facilities", tags=["Facilities"])
app.include_router(microfunding.router, prefix=f"{settings.API_V1_STR}/microfunding", tags=["Microfunding"])
print("Semua router berhasil didaftarkan.")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit {settings.API_V1_STR}/docs for documentation."}