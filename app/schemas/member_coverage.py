from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MemberCoverageCreate(BaseModel):
    member_id: int = Field(gt=0)
    plan_id: str = Field(
        min_length=1,
        max_length=100,
    )
    member_number: str = Field(
        min_length=1,
        max_length=100,
    )

    effective_date: date
    termination_date: date | None = None

    @model_validator(mode="after")
    def validate_coverage_dates(self):
        if (
            self.termination_date is not None
            and self.termination_date < self.effective_date
        ):
            raise ValueError(
                "Termination date cannot be earlier than effective date."
            )

        return self


class MemberCoverageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    plan_id: str = Field(
    min_length=1,
    max_length=100,
)
    member_number: str
    coverage_status: str
    effective_date: date
    termination_date: date | None
    created_at: datetime
    updated_at: datetime
