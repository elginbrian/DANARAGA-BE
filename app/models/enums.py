from enum import Enum

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class FacilityType(str, Enum):
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    PUSKESMAS = "PUSKESMAS"
    LABORATORY = "LABORATORY"

class ExpenseCategory(str, Enum):
    MEDICATION = "MEDICATION"
    CONSULTATION = "CONSULTATION"
    LAB_FEE = "LAB_FEE"
    OTHER = "OTHER"

class PoolStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class PoolMemberRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

class ContributionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    
class ContributionPeriod(str, Enum):
    MONTHLY = "BULANAN"
    WEEKLY = "MINGGUAN"
    ANNUALLY = "TAHUNAN"

class DisbursementStatus(str, Enum):
    PENDING_VOTE = "PENDING_VOTE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"
    CANCELLED = "CANCELLED"

class VoteOption(str, Enum):
    FOR = "FOR"
    AGAINST = "AGAINST"

class JoinRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ClaimApprovalSystem(str, Enum):
    VOTING_50_PERCENT = "VOTING_50_PERCENT"