
from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql

from app.repositories.autharization_repository import AuthorizationRepository


def test_review_queue():

    # Mock database session
    db = MagicMock()

    # Mock query result
    expected_authorizations = [
        MagicMock(id=101),
        MagicMock(id=102)
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = (
        expected_authorizations
    )

    db.execute.return_value = mock_result

    # Create repository
    repository = AuthorizationRepository(db)

    # Execute review queue query
    result = repository.get_review_queue(
        organization_id=10
    )

    # Verify returned results
    assert result == expected_authorizations

    # Verify database query was executed
    db.execute.assert_called_once()

    # Inspect generated SQL
    statement = db.execute.call_args.args[0]

    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True}
        )
    )

    # Verify required query conditions
    assert "authorization_workflows" in sql
    assert "users.organization_id = 10" in sql
    assert "authorization_workflows.organization_id = 10" in sql
    assert "authorization_workflows.workflow_status = 'WAITING_FOR_REVIEW'" in sql
    assert "authorizations.status IN ('SUBMITTED', 'IN_REVIEW')" in sql

    print("Organization isolation verified.")
    print("Workflow status filter verified.")
    print("Authorization status filter verified.")
    print("Review queue repository test passed!")


if __name__ == "__main__":
    test_review_queue()
