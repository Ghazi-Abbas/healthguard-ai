from typing import Literal
from pydantic import BaseModel , Field

EvidenceStatus=Literal[
    "FOUND",
    "NOT_FOUND",
    "AMBIGUOUS"
]

class ClinicalEvidenceFinding(BaseModel):
    criterion_id:str
    criterion:str =Field(
        description="The policy criaterion being examined."
    )
    eviedence_status:EvidenceStatus=Field(
        description=(
            "FOUND when supporting clinical evidence is identified."
            "NOT_FOUND when no supporting evidence appears in the supplied"
            "pages ; AMBIGUOUS when the text is unclear or conflicting."
        )
    )
    evodence_summatry:str= Field(
        description=(
            "A concise summary of what the supplied clinal document say."
            "Do not add facts that sre absent from the documents."
        )
    )

    supporting_evidence_ids: list[str]=Field(
        description=(
            "IDs of supplied clinical pages that support this finding. "
            "Only use Ids included in the input."

            )

    )

    missing_information:list[str]=Field(
        description="Evidence still needed to assess the criterion. "
    )


class ClinicalEvidenceResult(BaseModel):
    finding:list[ClinicalEvidenceFinding]

    overall_missing_information:list[str]=Field(
        description="Important information misssing across all criteria."
    )
