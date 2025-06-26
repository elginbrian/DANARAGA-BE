from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.models.common import IDModelMixin
from app.models.user import UserPublic
from app.models.enums import (
    PoolStatus, ContributionPeriod, PoolMemberRole,
    DisbursementStatus, VoteOption, JoinRequestStatus,
    ClaimApprovalSystem, PaymentMethod, ContributionStatus
)

class JoinRequestCreate(BaseModel):
    pool_code: str

class JoinRequestPublic(IDModelMixin, BaseModel):
    pool_id: str
    user_id: str
    user_details: Optional[UserPublic] = None
    status: JoinRequestStatus
    requested_at: datetime

    class Config:
        from_attributes = True

class PoolMemberPublic(IDModelMixin, BaseModel):
    pool_id: str
    user_id: str
    user_details: Optional[UserPublic] = None
    role: PoolMemberRole
    joined_date: datetime

    class Config:
        from_attributes = True

class ContributionPublic(IDModelMixin, BaseModel):
    pool_id: str
    member_id: str
    amount: float
    contribution_date: datetime
    payment_method: PaymentMethod
    status: ContributionStatus

    class Config:
        from_attributes = True

class VotePublic(BaseModel):
    user_id: str
    vote: VoteOption
    voted_at: datetime
    comment: Optional[str] = None

    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    vote: VoteOption
    comment: Optional[str] = Field(None, max_length=280)

class CreateDisbursementRequest(BaseModel):
    recipient_user_id: str
    amount: float = Field(gt=0, description="Jumlah dana yang diajukan")
    purpose: str = Field(..., max_length=500, description="Tujuan penggunaan dana")
    proof_url: Optional[str] = None

class DisbursementPublic(IDModelMixin, BaseModel):
    pool_id: str
    recipient_user_id: str
    requested_by_user_id: Optional[str] = None
    recipient_details: Optional[UserPublic] = None
    amount: float
    purpose: str
    proof_url: Optional[str] = None
    status: DisbursementStatus
    request_date: datetime
    voting_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    votes_for: int
    votes_against: int
    voters: List[VotePublic] = []

    class Config:
        from_attributes = True

class PoolBase(BaseModel):
    title: str
    description: str
    type_of_community: str
    max_members: int = Field(gt=0)
    contribution_period: ContributionPeriod
    contribution_amount_per_member: int = Field(ge=0)
    benefit_coverage: Optional[List[str]] = []
    claim_approval_system: ClaimApprovalSystem = ClaimApprovalSystem.VOTING_50_PERCENT
    claim_voting_duration: str = "24_HOURS"

class PoolCreate(PoolBase):
    pass

class PoolUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_members: Optional[int] = Field(None, gt=0)

class PoolPublic(IDModelMixin, PoolBase):
    creator_user_id: str
    pool_code: str
    current_amount: float
    status: PoolStatus
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True