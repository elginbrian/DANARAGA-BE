from pydantic import BaseModel
from typing import List, Optional
from app.models.common import IDModelMixin
from app.models.enums import FacilityType

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  

class FacilityBase(BaseModel):
    name: str
    type: FacilityType
    address: str
    location: Optional[GeoJSONPoint] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tariff_min: Optional[int] = None
    tariff_max: Optional[int] = None
    overall_rating: Optional[float] = None
    phone: Optional[str] = None
    services_offered: Optional[List[str]] = []
    image_url: Optional[str] = None
    distanceKm: Optional[float] = None
    distanceText: Optional[str] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[FacilityType] = None
    address: Optional[str] = None
    location: Optional[GeoJSONPoint] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tariff_min: Optional[int] = None
    tariff_max: Optional[int] = None
    overall_rating: Optional[float] = None
    phone: Optional[str] = None
    services_offered: Optional[List[str]] = None
    image_url: Optional[str] = None

class FacilityPublic(IDModelMixin, FacilityBase):
    class Config:
        from_attributes = True

class FacilityResponse(BaseModel):
    data: List[FacilityPublic]
    source: str