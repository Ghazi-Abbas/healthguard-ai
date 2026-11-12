
from app.agents.supervisor_agent import supervisor_node


def test_supervisor_creates_policy_search_query():
    state = {
        "policy_question": (
            "Determine criteria for procedure XYZ "
            "and diagnosis ABC."
        ),
        "active_policy_version_ids": [1],
        "clinical_pages": [{"page_number": 1}],
    }

    result = supervisor_node(state)

    assert result["policy_search_query"] == state["policy_question"]
    assert result["current_node"] == "supervisor"
    assert result["supervisor_missing_information"] == []


def test_supervisor_reports_missing_policy_question():
    state = {
        "policy_question": "",
        "active_policy_version_ids": [1],
        "clinical_pages": [{"page_number": 1}],
    }

    result = supervisor_node(state)

    assert result["policy_search_query"] == ""
    assert (
        "Original policy question is missing."
        in result["supervisor_missing_information"]
    )


def test_supervisor_reports_missing_active_policy():
    state = {
        "policy_question": "Find applicable policy criteria.",
        "active_policy_version_ids": [],
        "clinical_pages": [{"page_number": 1}],
    }

    result = supervisor_node(state)

    assert (
        "No active policy version is available."
        in result["supervisor_missing_information"]
    )


def test_supervisor_reports_missing_clinical_pages():
    state = {
        "policy_question": "Find applicable policy criteria.",
        "active_policy_version_ids": [1],
        "clinical_pages": [],
    }

    result = supervisor_node(state)

    assert (
        "No extracted clinical pages are available."
        in result["supervisor_missing_information"]
    )


def test_supervisor_does_not_modify_original_policy_question():
    original_question = (
        "Determine criteria for procedure XYZ and diagnosis ABC."
    )

    state = {
        "policy_question": original_question,
        "active_policy_version_ids": [1],
        "clinical_pages": [{"page_number": 1}],
    }

    result = supervisor_node(state)

    assert result["policy_search_query"] == original_question
    assert state["policy_question"] == original_question
