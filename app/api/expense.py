from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List, Any, Dict

from app.security import get_current_active_user
from app.models.user import UserPublic
from app.models.expense import ExpenseRecordPublic
from app.services import gemini_service, expense_service
from app.core.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload a receipt for OCR processing")
async def upload_receipt(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user),
    receiptImage: UploadFile = File(...)
) -> Dict[str, Any]:
    if not receiptImage.content_type or not receiptImage.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="File harus berupa gambar.")
        
    image_bytes = await receiptImage.read()
    extracted_data = await gemini_service.process_receipt_with_gemini(image_bytes, receiptImage.content_type)
    
    if not extracted_data or not extracted_data.get("items"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Gagal mengekstrak data dari struk.")
        
    created_expenses = await expense_service.create_expenses_from_receipt(db, user_id=current_user.id, receipt_data=extracted_data)
    return {"success": True, "expenses": created_expenses}

@router.get("/", summary="Get list of expenses")
async def get_all_expenses(
    page: int = 1,
    limit: int = 10,
    sortBy: str = "transaction_date",
    sortOrder: str = "desc",
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, Any]:
    params = {"page": page, "limit": limit, "sortBy": sortBy, "sortOrder": sortOrder}
    result = await expense_service.get_all(db, user_id=current_user.id, params=params)
    return result

@router.get("/summary", summary="Get expense summary")
async def get_summary_of_expenses(
    period: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, Any]:
    summary = await expense_service.get_summary(db, user_id=current_user.id, period=period)
    return {"success": True, "summary": summary}

@router.get("/recommendations", summary="Get AI-based spending recommendations")
async def get_spending_recommendations(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, Any]:
    recommendations = await expense_service.get_recommendations(db, user_id=current_user.id)
    return {"success": True, "recommendations": recommendations}