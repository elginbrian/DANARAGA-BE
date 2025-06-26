from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.common import IDModelMixin
from app.models.enums import ExpenseCategory, ReceiptStatus

class ReceiptBase(BaseModel):
    user_id: str
    upload_date: datetime
    image_url: str
    status: ReceiptStatus
    ocr_raw_text: Optional[str] = None
    processing_error: Optional[str] = None

class ReceiptCreate(BaseModel):
    image_url: str
    ocr_raw_text: Optional[str] = None

class ReceiptPublic(IDModelMixin, ReceiptBase):
    class Config:
        from_attributes = True

class ExpenseRecordBase(BaseModel):
    user_id: str
    medicine_name: Optional[str] = None
    facility_name: Optional[str] = None
    category: ExpenseCategory
    transaction_date: Optional[datetime] = None
    total_price: float = Field(ge=0)
    receipt_id: Optional[str] = None

class ExpenseRecordCreate(BaseModel):
    medicine_name: Optional[str] = None
    facility_name: Optional[str] = None
    category: ExpenseCategory
    transaction_date: Optional[datetime] = None
    total_price: float = Field(ge=0)
    receipt_id: Optional[str] = None

class ExpenseRecordUpdate(BaseModel):
    medicine_name: Optional[str] = None
    facility_name: Optional[str] = None
    category: Optional[ExpenseCategory] = None
    transaction_date: Optional[datetime] = None
    total_price: Optional[float] = Field(None, ge=0)

class ExpenseRecordPublic(IDModelMixin, ExpenseRecordBase):
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True