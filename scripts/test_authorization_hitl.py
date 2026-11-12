
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.authorization_supervisor_graph import (
    create_authorization_supervisor_graph
)


def test_authorization_graph_hitl():

    # 1. Mock the agent nodes
    def mock_supervisor(state):
        return {
            "supervisor_summary": "Authorization analyzed",
            "policy_search_query": "Test policy"
        }

    def mock_policy(state):
        return {
            "policy_criteria": [
                {
                    "criterion_id": "CR001",
                    "criterion": "Test criterion"
                }
            ]
        }

    def mock_analysis(state):
        return {
            "eligibility_result": {"status": "ELIGIBLE"},
            "clinical_evidence": [],
            "clinical_missing_information": []
        }

    def mock_criteria(state):
        return {
            "recommendation": "APPROVAL_RECOMMENDED",
            "risk": "LOW",
            "uncertainty": [],
            "missing_information": [],
            "criteria_result": {"recommendation": "APPROVAL_RECOMMENDED"},
            "needs_human_review": True
        }

    # 2. Compile graph with an in-memory checkpointer
    checkpointer = InMemorySaver()

    with (
        patch(
            "app.agents.authorization_supervisor_graph.supervisor_node",
            mock_supervisor
        ),
        patch(
            "app.agents.authorization_supervisor_graph.policy_crag_node",
            mock_policy
        ),
        patch(
            "app.agents.authorization_supervisor_graph.authorization_analysis_node",
            mock_analysis
        ),
        patch(
            "app.agents.authorization_supervisor_graph.criteria_risk_node",
            mock_criteria
        )
    ):

        graph = create_authorization_supervisor_graph(checkpointer)

        config = {
            "configurable": {
                "thread_id": "hitl-test-001"
            }
        }

        initial_state = {
            "authorization_id": 101,
            "organization_id": 1,
            "authorization": {},
            "workflow_status": "RUNNING"
        }

        # 3. Execute graph
        result = graph.invoke(initial_state, config)

        # 4. Verify graph paused for human review
        interrupts = result.get("__interrupt__", [])

        assert interrupts, "Graph did not pause for human review"

        interrupt_value = interrupts[0].value

        assert interrupt_value["authorization_id"] == 101
        assert interrupt_value["recommendation"] == "APPROVAL_RECOMMENDED"

        print("Graph successfully paused for human review.")

        # 5. Resume graph with reviewer decision
        resumed_result = graph.invoke(
            Command(
                resume={
                    "decision": "APPROVE",
                    "notes": "Test reviewer approval"
                }
            ),
            config
        )

        # 6. Verify reviewer decision
        assert resumed_result["human_decision"] == "APPROVE"
        assert resumed_result["reviewer_notes"] == "Test reviewer approval"
        assert resumed_result["workflow_status"] == "REVIEW_COMPLETED"

        print("Graph successfully resumed.")
        print("Human decision:", resumed_result["human_decision"])
        print("Workflow status:", resumed_result["workflow_status"])
