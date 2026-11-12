from pydantic import BaseModel, Field

class RequestINformationRequest(BaseModel):
    message:str=Field(
        ..., min_length=5,
        max_length=2000
    )
