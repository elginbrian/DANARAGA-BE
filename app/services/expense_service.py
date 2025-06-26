from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
import math

from app.models.expense import ExpenseRecordCreate, ExpenseRecordPublic, ReceiptCreate, ReceiptPublic
from app.models.enums import ExpenseCategory

async def create_expenses_from_receipt(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    receipt_data: Dict[str, Any]
) -> List[ExpenseRecordPublic]:
    created_expenses = []
    
    receipt_doc = {
        "user_id": user_id,
        "upload_date": datetime.utcnow(),
        "image_url": receipt_data.get("image_url", ""),
        "status": "PROCESSED",
        "ocr_raw_text": receipt_data.get("raw_text", "")
    }
    
    receipt_result = await db.receipts.insert_one(receipt_doc)
    receipt_id = str(receipt_result.inserted_id)
    
    items = receipt_data.get("items", [])
    facility_name = receipt_data.get("facility_name", "")
    transaction_date = receipt_data.get("transaction_date")
    
    for item in items:
        expense_data = {
            "user_id": user_id,
            "medicine_name": item.get("name", ""),
            "facility_name": facility_name,
            "category": item.get("category", ExpenseCategory.OTHER),
            "transaction_date": datetime.fromisoformat(transaction_date) if transaction_date else datetime.utcnow(),
            "total_price": float(item.get("price", 0)),
            "receipt_id": receipt_id,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        result = await db.expense_records.insert_one(expense_data)
        expense_data["_id"] = str(result.inserted_id)
        created_expenses.append(ExpenseRecordPublic(**expense_data))
    
    return created_expenses

async def get_all(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    params: Dict[str, Any]
) -> Dict[str, Any]:
    page = params.get("page", 1)
    limit = params.get("limit", 10)