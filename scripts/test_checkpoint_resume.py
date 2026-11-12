
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.db.checkpointer import (
    create_checkpointer_pool,
    create_checkpointer
)

from app.services.review_service import ReviewService


# ============================================================
# TEST GRAPH STATE
# ============================================================

class TestState(TypedDict):
    message: str
    decision: object


# ============================================================
# GRAPH NODES
# ============================================================

def first_node(state: TestState):
    return {
        "message": "Workflow started"
    }


def human_review_node(state: TestState):

    decision = interrupt({
        "message": "Human review required"
    })

    return {
        "decision": decision
    }


def final_node(state: TestState):
    return {
        "message": "Workflow completed"
    }


# ============================================================
# CREATE TEST GRAPH
# ============================================================

def create_test_graph(checkpointer):

    builder = StateGraph(TestState)

    builder.add_node("first", first_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("final", final_node)

    builder.add_edge(START, "first")
    builder.add_edge("first", "human_review")
    builder.add_edge("human_review", "final")
    builder.add_edge("final", END)

    return builder.compile(checkpointer=checkpointer)


# ============================================================
# TEST REVIEW SERVICE WITH REAL POSTGRES CHECKPOINTING
# ============================================================

def test_review_service_postgres_resume():

    pool = create_checkpointer_pool()

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:

        # ----------------------------------------------------
        # 1. Open PostgreSQL connection pool
        # ----------------------------------------------------

        pool.open(wait=True)

        checkpointer = create_checkpointer(pool)
        checkpointer.setup()

        graph = create_test_graph(checkpointer)

        print("PostgreSQL connection pool opened.")

        # ----------------------------------------------------
        # 2. Start workflow
        # ----------------------------------------------------

        result = graph.invoke(
            {
                "message": "Start",
                "decision": ""
            },
            config=config
        )

        assert result.get("__interrupt__")

        print("Workflow paused for human review.")

        # ----------------------------------------------------
        # 3. Verify checkpoint
        # ----------------------------------------------------

        state = graph.get_state(config)

        assert state.next == ("human_review",)

        print("PostgreSQL checkpoint saved.")

        # ----------------------------------------------------
        # 4. Close original connection pool
        # ----------------------------------------------------

        pool.close()

        print("Original PostgreSQL pool closed.")

        # ----------------------------------------------------
        # 5. Create a new pool and graph
        # ----------------------------------------------------

        pool = create_checkpointer_pool()
        pool.open(wait=True)

        checkpointer = create_checkpointer(pool)

        graph = create_test_graph(checkpointer)

        print("New PostgreSQL pool created.")

        # ----------------------------------------------------
        # 6. Create mocked repositories and database
        # ----------------------------------------------------

        auth_repo = MagicMock()
        review_repo = MagicMock()
        workflow_repo = MagicMock()
        db = MagicMock()

        authorization = SimpleNamespace(
            id=101,
            status="SUBMITTED"
        )

        workflow = SimpleNamespace(
            id=1,
            thread_id=thread_id,
            workflow_status="WAITING_FOR_REVIEW"
        )

        auth_repo.get_by_id_for_organization_for_update.return_value = (
            authorization
        )

        workflow_repo.get_by_authorization_for_update.return_value = (
            workflow
        )

        workflow_repo.get_by_authorization.return_value = workflow

        # ----------------------------------------------------
        # 7. Create actual ReviewService
        # ----------------------------------------------------

        review_service = ReviewService(
            auth_repo=auth_repo,
            review_repo=review_repo,
            workflow_repo=workflow_repo,
            graph=graph,
            db=db
        )

        # ----------------------------------------------------
        # 8. Submit human decision through ReviewService
        # ----------------------------------------------------

        result = review_service.approve(
            authorization_id=101,
            organization_id=10,
            reviewer_id=5,
            comments="Evidence verified"
        )

        # ----------------------------------------------------
        # 9. Verify application-level results
        # ----------------------------------------------------

        assert result.status == "APPROVED"

        assert workflow.workflow_status == "REVIEW_COMPLETED"

        review_repo.create.assert_called_once()

        assert db.commit.call_count == 2

        print("Review record saved.")
        print("Authorization status updated.")

        # ----------------------------------------------------
        # 10. Verify actual PostgreSQL-backed graph state
        # ----------------------------------------------------

        final_state = graph.get_state(config)

        assert final_state.next == ()

        assert final_state.values["decision"] == {
            "decision": "APPROVE",
            "notes": "Evidence verified"
        }

        assert final_state.values["message"] == "Workflow completed"

        print("Existing PostgreSQL checkpoint resumed.")
        print("Human decision:", final_state.values["decision"])
        print("Final message:", final_state.values["message"])

        print("\nReviewService PostgreSQL resume test passed!")

    finally:

        pool.close()


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":
    test_review_service_postgres_resume()
