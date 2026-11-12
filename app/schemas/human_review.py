from typing import Literal
from pydantic import BaseModel , Field

class HumanReviewInput(BaseModel):
    decision:Literal[
        "APPROVE",
        "REJECT",
        "REQUEST_INFORMATION"
    ]

    notes:str | None=Field(
        default=None,
        max_length=2000
    )

class ClinicalPageForResume(BaseModel):
    evidence_id:str
    document_id:int
    filename:str
    page_number: int= Field(ge=1)
    text:str

class ProviderUploadEvent(BaseModel):
    authorization_id:int
    document_ids:list[int]=Field(min_length=1)
    clinical_pages:list[ClinicalPageForResume] =Field(min_length=1)
