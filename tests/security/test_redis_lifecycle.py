
from unittest.mock import MagicMock, patch

from app.main import lifespan


def test_lifespan_closes_postgres_and_redis():
    app = MagicMock()

    mock_pool = MagicMock()
    mock_checkpointer = MagicMock()
    mock_graph = MagicMock()

    with (
        patch(
            "app.main.create_checkpointer_pool",
            return_value=mock_pool
        ),
        patch(
            "app.main.create_checkpointer",
            return_value=mock_checkpointer
        ),
        patch(
            "app.main.create_authorization_supervisor_graph",
            return_value=mock_graph
        ),
        patch("app.main.redis_client") as mock_redis
    ):
        async def run_test():
            async with lifespan(app):
                assert app.state.checkpointer is mock_checkpointer
                assert app.state.authorization_graph is mock_graph

        import asyncio
        asyncio.run(run_test())

    mock_pool.open.assert_called_once_with(wait=True)
    mock_checkpointer.setup.assert_called_once()
    mock_pool.close.assert_called_once()
    mock_redis.close.assert_called_once()
