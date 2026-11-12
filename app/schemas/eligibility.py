from datetime import date
from typing import Literal

from pydantic import BaseModel

EligibilityStatus=Literal[
    "ELIGIBLE_FOR_REVIEW",
    "NOT_ELIGIBLE",
    "UNKNOWN"
]

class EligibilityResult(BaseModel):
    member_id:str
    status:EligibilityStatus
    plan_id:str |None=None
    service_date:date |None=None
    reason:str
    source:str="authoritative_member_coverage"
    effective_date: date | None = None
    termination_date: date | None = None
    coverage_status: str | None = None
