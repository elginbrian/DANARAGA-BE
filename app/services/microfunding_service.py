import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.enums import (DisbursementStatus, JoinRequestStatus,
                              PoolMemberRole, PoolStatus, ContributionStatus, VoteOption)
from app.models.pool import (CreateDisbursementRequest, PoolCreate,
                             PoolUpdate, VoteCreate)
from app.models.user import UserPublic
from app.services import payment_service


def _fix_document_id(doc: Dict) -> Dict:
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
    return doc

async def _check_is_pool_admin(db: AsyncIOMotorDatabase, pool_id: str, user_id: str) -> bool:
    admin_membership = await db["pool_members"].find_one({
        "pool_id": ObjectId(pool_id),
        "user_id": ObjectId(user_id),
        "role": PoolMemberRole.ADMIN
    })
    return admin_membership is not None

def _generate_pool_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def create_pool(db: AsyncIOMotorDatabase, user_id: str, pool_data: PoolCreate) -> Dict:
    pool_code = _generate_pool_code()
    while await db["pools"].find_one({"pool_code": pool_code}):
        pool_code = _generate_pool_code()
        
    new_pool_doc = pool_data.model_dump()
    new_pool_doc.update({
        "creator_user_id": ObjectId(user_id),
        "pool_code": pool_code,
        "current_amount": 0,
        "status": PoolStatus.OPEN,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    })
    
    result = await db["pools"].insert_one(new_pool_doc)
    pool_id = result.inserted_id

    admin_member_doc = {
        "pool_id": pool_id, "user_id": ObjectId(user_id),
        "role": PoolMemberRole.ADMIN, "joined_date": datetime.utcnow(),
    }
    await db["pool_members"].insert_one(admin_member_doc)
    
    created_pool = await db["pools"].find_one({"_id": pool_id})
    return _fix_document_id(created_pool)

async def get_user_pools(db: AsyncIOMotorDatabase, user_id: str) -> List[Dict]:
    member_of_docs = await db["pool_members"].find({"user_id": ObjectId(user_id)}).to_list(length=None)
    pool_ids = [doc["pool_id"] for doc in member_of_docs]

    cursor = db["pools"].find({"_id": {"$in": pool_ids}}).sort("createdAt", -1)
    return [_fix_document_id(doc) async for doc in cursor]

async def get_pool_by_id(db: AsyncIOMotorDatabase, pool_id: str) -> Dict:
    if not ObjectId.is_valid(pool_id):
        raise HTTPException(status_code=404, detail="Pool not found")
    pool = await db["pools"].find_one({"_id": ObjectId(pool_id)})
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return _fix_document_id(pool)

async def update_pool(db: AsyncIOMotorDatabase, user_id: str, pool_id: str, update_data: PoolUpdate) -> Dict:
    if not await _check_is_pool_admin(db, pool_id, user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this pool")

    update_doc = update_data.model_dump(exclude_unset=True)
    if not update_doc:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_doc["updatedAt"] = datetime.utcnow()
    
    await db["pools"].update_one(
        {"_id": ObjectId(pool_id)},
        {"$set": update_doc}
    )
    return await get_pool_by_id(db, pool_id)

async def get_pool_members(db: AsyncIOMotorDatabase, pool_id: str) -> List[Dict]:
    pipeline = [
        {"$match": {"pool_id": ObjectId(pool_id)}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user_details"
        }},
        {"$unwind": "$user_details"},
        {"$project": {
            "id": "$_id", "pool_id": 1, "user_id": 1, "role": 1, "joined_date": 1,
            "user_details.name": 1, "user_details.email": 1
        }}
    ]
    members = await db["pool_members"].aggregate(pipeline).to_list(length=None)
    return members

async def get_user_membership(db: AsyncIOMotorDatabase, pool_id: str, user_id: str) -> Dict:
    membership = await db["pool_members"].find_one({"pool_id": ObjectId(pool_id), "user_id": ObjectId(user_id)})
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this pool")
    return _fix_document_id(membership)

async def request_to_join(db: AsyncIOMotorDatabase, user_id: str, pool_code: str) -> Dict:
    pool = await db["pools"].find_one({"pool_code": pool_code.upper()})
    if not pool:
        raise HTTPException(status_code=404, detail="Pool with this code not found")
    
    new_request = {
        "pool_id": pool["_id"], "user_id": ObjectId(user_id),
        "status": JoinRequestStatus.PENDING, "requested_at": datetime.utcnow()
    }
    result = await db["join_requests"].insert_one(new_request)
    created_request = await db["join_requests"].find_one({"_id": result.inserted_id})
    return _fix_document_id(created_request)

async def update_join_request(db: AsyncIOMotorDatabase, user_id: str, request_id: str, new_status: str) -> Dict:
    request_doc = await db["join_requests"].find_one({"_id": ObjectId(request_id)})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Join request not found")

    if not await _check_is_pool_admin(db, str(request_doc["pool_id"]), user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if new_status == JoinRequestStatus.APPROVED:
        await db["pool_members"].insert_one({
            "pool_id": request_doc["pool_id"], "user_id": request_doc["user_id"],
            "role": PoolMemberRole.MEMBER, "joined_date": datetime.utcnow()
        })
    
    await db["join_requests"].update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": new_status, "resolved_at": datetime.utcnow()}}
    )
    return {"message": f"Request has been {new_status.lower()}"}

async def create_contribution(db: AsyncIOMotorDatabase, user: UserPublic, pool_id: str, amount: float) -> Dict:
    new_contrib = {
        "pool_id": ObjectId(pool_id), "member_id": ObjectId(user.id), "amount": amount,
        "contribution_date": datetime.utcnow(), "status": ContributionStatus.PENDING
    }
    result = await db["contributions"].insert_one(new_contrib)
    contrib_id = str(result.inserted_id)

    midtrans_data = await payment_service.create_midtrans_snap_transaction(contrib_id, amount, user)
    
    await db["contributions"].update_one(
        {"_id": result.inserted_id},
        {"$set": {"payment_gateway_reference_id": midtrans_data["token"]}}
    )
    
    return {"contributionId": contrib_id, "paymentToken": midtrans_data["token"]}

async def get_my_contributions(db: AsyncIOMotorDatabase, user_id: str, pool_id: str) -> List[Dict]:
    cursor = db["contributions"].find({"member_id": ObjectId(user_id), "pool_id": ObjectId(pool_id)}).sort("contribution_date", -1)
    return [_fix_document_id(doc) async for doc in cursor]

async def create_disbursement(db: AsyncIOMotorDatabase, requested_by_user_id: str, pool_id: str, data: CreateDisbursementRequest) -> Dict:
    
    new_disbursement_doc = data.model_dump()
    new_disbursement_doc.update({
        "pool_id": ObjectId(pool_id),
        "requested_by_user_id": ObjectId(requested_by_user_id),
        "recipient_user_id": ObjectId(data.recipient_user_id),
        "status": DisbursementStatus.PENDING_VOTE,
        "request_date": datetime.utcnow(),
        "votes_for": 0, "votes_against": 0, "voters": []
    })
    
    result = await db["disbursements"].insert_one(new_disbursement_doc)
    created_doc = await db["disbursements"].find_one({"_id": result.inserted_id})
    return _fix_document_id(created_doc)