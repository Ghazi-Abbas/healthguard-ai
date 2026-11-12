from pydantic import BaseModel ,Field ,field_validator,ConfigDict
from datetime import date, datetime
from enum import Enum
from datetime import date

class AuthorizationStatus(str,Enum):
    DRAFT="DRAFT"
    SUBMITTED="SUBMITTED"
    IN_REVIE="IN_REVIE"
    APPROVED="APPROVED"
    REJECTED="REJECTED"
    REQUEST_INFORMSTION="REQUEST_INFORMSTION"

class AuthorizationCreate(BaseModel):
    member_id: str
    plan_id: str
    service_date: date
    procedure_code: str
    diagnosis_code: str
    clinical_summary: str = Field(min_length=20)

    @field_validator("member_id", "procedure_code", "diagnosis_code")
    @classmethod
    def validate_not_blank(cls, value: str):
        if not value.strip():
            raise ValueError("Field can't be blank")
        return value

    @field_validator("clinical_summary")
    @classmethod
    def validate_clinical_summary(cls, value: str):
        if len(value.strip()) < 20:
            raise ValueError(
                "Clinical summary must contain at least 20 characters"
            )
        return value


class AuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: str
    member_coverage_id: int
    service_date: date
    procedure_code: str
    diagnosis_code: str
    clinical_summary: str
    status: AuthorizationStatus
    user_id: int
    created_at: datetime

class AuthorizationUpdate(BaseModel):
    procedure_code:str
    dignosis_code:str
    cllinical_summary:str

class AuthorisationPatch(BaseModel):
    procedure_code: str | None = Field(default=None, min_length=1)
    diagnosis_code: str | None = Field(default=None, min_length=1)
    clinical_summary: str | None = Field(default=None, min_length=20)

    @field_validator(
        "procedure_code",
        "diagnosis_code",
        "clinical_summary"
    )
    @classmethod
    def validate_not_blank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Field cannot be blank")
        return value

    def validate_patch_data(self):
        update_data = self.model_dump(exclude_unset=True)

        if not update_data:
            raise ValueError("At least one field must be provided")

        if any(value is None for value in update_data.values()):
            raise ValueError("Fields cannot be null")

        return update_data

class AuthorizationListResponse(BaseModel):
    items:list[AuthorizationResponse]
    page:int
    page_size:int
    total:int
    total_pages:int

    # Health Insurance Portability and Accountability Act HIPAA

    # Information that identifies a person and relates to their health can be Protected Health Information (PHI) under HIPAA.

    # BAA stands for Business Associate Agreement.
