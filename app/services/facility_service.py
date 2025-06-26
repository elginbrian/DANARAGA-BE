from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any, Optional

from app.models.facility import FacilityPublic

def fix_facility_id(facility_doc):
    if facility_doc and "_id" in facility_doc:
        facility_doc["id"] = str(facility_doc["_id"])
    return facility_doc

async def get_facilities_by_filter(db: AsyncIOMotorDatabase, filter: Dict[str, Any]) -> List[FacilityPublic]:
    facilities = []
    cursor = db["facilities"].find(filter).limit(10)
    async for doc in cursor:
        facilities.append(FacilityPublic(**fix_facility_id(doc)))
    return facilities

async def get_nearby_facilities(db: AsyncIOMotorDatabase, preferences: Dict[str, Any]) -> List[FacilityPublic]:
    user_location = preferences.get("userLocation", {})
    latitude = user_location.get("latitude")
    longitude = user_location.get("longitude")
    max_distance_km = preferences.get("maxDistanceKm", 20)

    if not latitude or not longitude:
        return []

    geo_filter = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "$maxDistance": max_distance_km * 1000
            }
        }
    }
    
    return await get_facilities_by_filter(db, filter=geo_filter)


async def get_facility_by_id(db: AsyncIOMotorDatabase, facility_id: str) -> Optional[FacilityPublic]:
    if not ObjectId.is_valid(facility_id):
        return None
        
    facility_doc = await db["facilities"].find_one({"_id": ObjectId(facility_id)})
    if facility_doc:
        return FacilityPublic(**fix_facility_id(facility_doc))
    return None