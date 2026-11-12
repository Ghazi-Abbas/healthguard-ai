
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from app.core.config import settings


def create_checkpointer_pool():

    pool = ConnectionPool(
        conninfo=settings.LANGGRAPH_CHECKPOINTER_URL,
        min_size=1,
        max_size=5,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        },
        open=False
    )

    return pool


def create_checkpointer(pool):

    return PostgresSaver(pool)
