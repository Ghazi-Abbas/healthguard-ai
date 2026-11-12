
from pydantic import BaseModel, Field


class QueryRewrites(BaseModel):
    search_query: str = Field(
        min_length=2,
        max_length=1000,
        description="A self-contained search query containing relevant policy terms."
    )

    reason: str = Field(
        description="A brief explanation of why the query was changed."
    )

    missing_context: list[str] = Field(
        default_factory=list,
        description="Important details that are still missing and must not be guessed."
    )


class RetrievalAssessment(BaseModel):
    relevant_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence IDs that are genuinely relevant to answering the question."
    )

    sufficient: bool = Field(
        description=(
            "True only if the supplied evidence is sufficient to answer "
            "the main question without inventing facts."
        )
    )

    missing_information: list[str] = Field(
        default_factory=list,
        description="Information not established by the retrieved evidence."
    )

    correction_hints: list[str] = Field(
        default_factory=list,
        description="Suggestions for improving the next search query."
    )
