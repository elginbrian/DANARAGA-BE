from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from . import gemini_service
from ..models.enums import ExpenseCategory

def fix_expense_id(expense_doc):
    if expense_doc and "_id" in expense_doc:
        expense_doc["id"] = str(expense_doc["_id"])
    return expense_doc

async def create_expenses_from_receipt(db: AsyncIOMotorDatabase, user_id: str, receipt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    created_expenses = []
    items_to_insert = []
    
    transaction_date = datetime.fromisoformat(receipt_data.get("transaction_date")) if receipt_data.get("transaction_date") else datetime.utcnow()
    facility_name = receipt_data.get("store_name")

    for item in receipt_data.get("items", []):
        expense_record = {
            "user_id": ObjectId(user_id),
            "medicine_name": item.get("name"),
            "facility_name": facility_name,
            "category": item.get("category", ExpenseCategory.OTHER),
            "transaction_date": transaction_date,
            "total_price": item.get("total_price", 0),
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        items_to_insert.append(expense_record)

    if not items_to_insert:
        return []

    result = await db["expenses"].insert_many(items_to_insert)
    
    cursor = db["expenses"].find({"_id": {"$in": result.inserted_ids}})
    async for doc in cursor:
        created_expenses.append(fix_expense_id(doc))
        
    return created_expenses

async def get_summary(db: AsyncIOMotorDatabase, user_id: str, period: str) -> Dict[str, Any]:
    now = datetime.utcnow()
    start_date = now - timedelta(days=30) 
    end_date = now

    pipeline = [
        {"$match": {
            "user_id": ObjectId(user_id),
            "transaction_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": None,
            "totalSpending": {"$sum": "$total_price"}
        }}
    ]
    result = await db["expenses"].aggregate(pipeline).to_list(1)
    total_spending = result[0]['totalSpending'] if result else 0
    return {"totalSpending": total_spending, "periodLabel": period}

async def get_all(db: AsyncIOMotorDatabase, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    cursor = db["expenses"].find({"user_id": ObjectId(user_id)}).sort("transaction_date", -1).limit(10)
    expenses = [fix_expense_id(doc) async for doc in cursor]
    return {"data": expenses}

async def get_recommendations(db: AsyncIOMotorDatabase, user_id: str) -> List[str]:
    cursor = db["expenses"].find({"user_id": ObjectId(user_id)}).sort("transaction_date", -1).limit(20)
    expenses = [doc async for doc in cursor]
    
    recommendations = await gemini_service.generate_spending_recommendations(expenses)
    return recommendations