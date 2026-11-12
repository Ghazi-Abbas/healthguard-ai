from typing import Literal
from pydantic import BaseModel , Field

class SupervisionPlan(BaseModel):
    case_summary:str =Field(
        description=(
            "A concise summery based on the supplied procedure, diagonsis,"
            "and request, Do not invent patient information"
        )
    )

    policy_search_query:str =Field(
        description=(
            "A focused query to find the application policy and its criteria. "

        )
    )

    missing_information: list[str]=Field(
        description=(
            "Required context that is missing from the supplied input."
        )
    )

class HumenReviewInput(BaseModel):
        decsion: Literal[
            "APPROVE",
            "REJECT",
            "REQUEST_INFORMATION",
        ]

        note:str | None= Field(
            default=None,
            max_length=2000
        )
