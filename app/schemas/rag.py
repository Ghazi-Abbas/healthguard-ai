from pydantic import BaseModel , Field, field_validator
from typing import Literal
class PolicySearchRequest(BaseModel):
    query:str=Field(min_length=1, max_length=2000)

    method:Literal[
        "semantic",
        "keyword",
        "hybrid",
    ]="hybrid"

    top_k:int=Field(default=5, ge=1,lt=20)

    policy_version_id:int | None= Field(
        default=None,
        gt=0
    )
    @field_validator("query")
    @classmethod
    def clean_query(cls, value:str)->str:
        value=value.strip()

        if not value:
            raise ValueError("Query cannot be Empity")

        return value

class PolicyEvidence(BaseModel):
    text:str
    policy_version_id:int
    document_id:int
    page_number:int
    section:str |None=None
    source:str  |None=None

class PolicySearchResponse(BaseModel):
    query:str
    method:Literal[
        "semantic",
        "keyword",
        "hybrid"
    ]
    results:list[PolicyEvidence]
