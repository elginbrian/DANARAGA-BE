from fastapi import APIRouter, Depends, Body, HTTPException, status
from typing import List, Dict, Any

from app.models.facility import FacilityPublic, FacilityResponse
from app.models.user import UserPublic
from app.security import get_current_active_user
from app.services import gemini_service, facility_service
from app.core.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/recommendations", response_model=FacilityResponse, summary="Get AI-based facility recommendations")
async def get_ai_recommendations(
    payload: Dict[str, Any] = Body(...),
    current_user: UserPublic = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    preferences = payload.get("preferences", {})
    user_profile_for_ai = current_user.model_dump()
    user_profile_for_ai['preferences'] = preferences
    
    mongo_filter = await gemini_service.generate_facility_filter(user_profile_for_ai)
    facilities = await facility_service.get_facilities_by_filter(db, filter=mongo_filter)
    
    return FacilityResponse(
        data=facilities,
        source="AI_RECOMMENDATIONS"
    )

@router.post("/nearby", response_model=FacilityResponse, summary="Get nearby facilities")
async def get_nearby(
    payload: Dict[str, Any] = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    preferences = payload.get("preferences", {})
    facilities = await facility_service.get_nearby_facilities(db, preferences)
    
    return FacilityResponse(
        data=facilities,
        source="NEARBY_SEARCH"
    )

@router.post("/search", response_model=FacilityResponse, summary="Search facilities with Gemini")
async def search_facilities(
    payload: Dict[str, Any] = Body(...),
):
    query = payload.get("query")
    user_location = payload.get("user_location")
    if not query or not user_location:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "query dan user_location diperlukan.")
    
    facilities = await gemini_service.search_facilities_with_gemini(query, user_location)
    
    return FacilityResponse(
        data=facilities,
        source="GEMINI_SEARCH"
    )

@router.get("/{facility_id}", summary="Get facility by ID")
async def get_facility_by_id(
    facility_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    facility = await facility_service.get_facility_by_id(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    return {"facility": facility}