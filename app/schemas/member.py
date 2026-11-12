from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MemberCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    date_of_birth: date

    external_member_id: str = Field(
        min_length=1,
        max_length=100,
    )



class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    date_of_birth: date
    created_at: datetime
    updated_at: datetime
