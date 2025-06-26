from fastapi import APIRouter, Depends, Body, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.security import get_current_active_user
from app.models.user import UserPublic
from app.models.pool import (
    PoolCreate, PoolUpdate, PoolPublic, 
    JoinRequestPublic, PoolMemberPublic,
    CreateDisbursementRequest, ContributionPublic,
    DisbursementPublic
)
from app.models.enums import JoinRequestStatus, VoteOption, DisbursementStatus, ContributionStatus
from app.services import microfunding_service

router = APIRouter()

class ApiResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Dict[str, Any]

@router.get("/pools/my-pools")
async def get_user_pools(
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    pools = await microfunding_service.get_user_pools(db, user_id=current_user.id)
    return ApiResponse(data={"pools": pools})

@router.post("/pools", status_code=201)
async def create_new_pool(
    pool_data: PoolCreate, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    pool = await microfunding_service.create_pool(db, user_id=current_user.id, pool_data=pool_data)
    return ApiResponse(data={"pool": pool}, message="Pool created successfully")

@router.get("/pools/{pool_id}")
async def get_pool_details(
    pool_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    pool = await microfunding_service.get_pool_by_id(db, pool_id=pool_id)
    return ApiResponse(data={"pool": pool})

@router.patch("/pools/{pool_id}")
async def update_pool_details(
    pool_id: str, 
    update_data: PoolUpdate, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    pool = await microfunding_service.update_pool(db, user_id=current_user.id, pool_id=pool_id, update_data=update_data)
    return ApiResponse(data={"pool": pool}, message="Pool updated successfully")

@router.get("/pools/{pool_id}/members")
async def get_all_pool_members(
    pool_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    members = await microfunding_service.get_pool_members(db, pool_id=pool_id)
    return ApiResponse(data={"members": members})

@router.get("/pools/{pool_id}/members/me")
async def get_my_membership_status(
    pool_id: str, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    member = await microfunding_service.get_user_membership(db, pool_id=pool_id, user_id=current_user.id)
    return ApiResponse(data={"member": member})

@router.post("/join-requests", status_code=201)
async def send_join_request(
    payload: Dict[str, str] = Body(...), 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    pool_code = payload.get("pool_code")
    if not pool_code:
        raise HTTPException(status_code=400, detail="pool_code is required")
    
    result = await microfunding_service.request_to_join(db, user_id=current_user.id, pool_code=pool_code)
    return ApiResponse(data={"joinRequest": result["joinRequest"]}, message=result["message"])

@router.get("/pools/{pool_id}/join-requests")
async def get_pool_join_requests(
    pool_id: str, 
    status: JoinRequestStatus, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    requests = await microfunding_service.get_join_requests(db, user_id=current_user.id, pool_id=pool_id, status=status)
    return ApiResponse(data={"requests": requests})

@router.patch("/join-requests/{request_id}")
async def process_join_request(
    request_id: str, 
    payload: Dict[str, str] = Body(...), 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    new_status = payload.get("status")
    if not new_status or new_status not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="status must be APPROVED or REJECTED")
    
    result = await microfunding_service.update_join_request(db, user_id=current_user.id, request_id=request_id, new_status=new_status)
    return ApiResponse(data={"updatedRequest": result["updatedRequest"]}, message=result["message"])

@router.post("/pools/{pool_id}/contributions")
async def initiate_contribution(
    pool_id: str, 
    payload: Dict[str, float] = Body(...), 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    amount = payload.get("amount")
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be greater than 0")
    
    result = await microfunding_service.create_contribution(db, user_id=current_user.id, pool_id=pool_id, amount=amount)
    
    return ApiResponse(data={
        "contributionId": result.get("contributionId") or result.get("contribution_id"),
        "paymentToken": result.get("paymentToken") or result.get("payment_token")
    })

@router.get("/pools/{pool_id}/contributions/me")
async def get_my_pool_contributions(
    pool_id: str, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    contributions = await microfunding_service.get_my_contributions(db, user_id=current_user.id, pool_id=pool_id)
    return ApiResponse(data={"contributions": contributions})

@router.get("/contributions/{contribution_id}/check-status")
async def check_payment_status(
    contribution_id: str, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    result = await microfunding_service.check_contribution_status(db, user_id=current_user.id, contribution_id=contribution_id)
    return ApiResponse(data=result)

@router.get("/pools/{pool_id}/disbursements")
async def get_pool_disbursements(
    pool_id: str, 
    status: Optional[DisbursementStatus] = None, 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    disbursements = await microfunding_service.get_disbursements(db, pool_id=pool_id, status=status)
    return ApiResponse(data={"disbursements": disbursements})

@router.post("/pools/{pool_id}/disbursements", status_code=201)
async def create_new_disbursement(
    pool_id: str, 
    data: CreateDisbursementRequest, 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    disbursement = await microfunding_service.create_disbursement(db, user_id=current_user.id, pool_id=pool_id, data=data)
    return ApiResponse(data={"disbursement": disbursement}, message="Disbursement request created successfully")

@router.post("/disbursements/{disbursement_id}/vote")
async def vote_on_a_disbursement(
    disbursement_id: str, 
    payload: Dict[str, Any] = Body(...), 
    current_user: UserPublic = Depends(get_current_active_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ApiResponse:
    vote = payload.get("vote")
    comment = payload.get("comment")
    
    if not vote or vote not in ["FOR", "AGAINST"]:
        raise HTTPException(status_code=400, detail="vote must be FOR or AGAINST")
    
    result = await microfunding_service.vote_on_disbursement(
        db, 
        user_id=current_user.id, 
        disbursement_id=disbursement_id, 
        vote=vote, 
        comment=comment
    )
    return ApiResponse(data={"disbursement": result["disbursement"]}, message=result["message"])