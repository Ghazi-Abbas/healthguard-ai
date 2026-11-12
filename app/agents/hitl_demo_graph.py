from typing import Any , Literal, TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph.types import interrupt

ReviewerDecision=Literal[
    "APPROVE",
    "REJECT",
    "REQUEST_INFORMATION",

]

class HITLState(TypedDict, total=False):
    authorization_id:int
    recommendation:str
    reviewer_decision:ReviewerDecision
    reviewer_id:str
    reviewer_notes:str
    review_status:str

def humen_review_node(state:HITLState)->dict[str, Any]:

    review_request={
        "authorization_id":state["authorization_id"],
        "ai_recommendation":state["recommendation"],
        "message":"Please review the authorization recomendation.",
        "allowed_decisions":[
            "APPROVE",
            "REJECT",
            "REQUEST_INFORMATION"
        ]
    }
