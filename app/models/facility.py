from pydantic import BaseModel
from typing import List, Optional
from app.models.common import IDModelMixin

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]

class FacilityBase(BaseModel):
    name: str
    type: str
    address: str
    location: GeoJSONPoint
    tariff_min: Optional[int] = 0
    tariff_max: Optional[int] = 0
    overall_rating: Optional[float] = 0.0
    phone: Optional[str] = None
    services_offered: Optional[List[str]] = []
    image_url: Optional[str] = None

class FacilityPublic(IDModelMixin, FacilityBase):
     class Config:
        from_attributes = True