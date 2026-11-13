import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

import os
import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Check LangSmith configuration
logger.info(
    "LangSmith configuration | tracing=%s | project=%s | api_key_present=%s",
    os.getenv("LANGSMITH_TRACING"),
    os.getenv("LANGSMITH_PROJECT"),
    bool(os.getenv("LANGSMITH_API_KEY")),
)


from fastapi import FastAPI
from app.api.routes.authorizations import router as authorization_router
from app.api.routes.auth import router as auth_router

from app.api.routes.admin import router as admin_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.policies import router as policies_router
from app.api.routes.member_coverages import router as member_coverages_router
from app.api.routes.members import router as members
from app.db.base import Base
from app.cache.redis_client import redis_client
from uuid import uuid4
from starlette.requests import Request
from contextlib import asynccontextmanager
from app.models import(
    Authorization,
    Document,DocumentPage,User, Organization
)
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unexpected_exception_handler,
)

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.db.checkpointer import (
    create_checkpointer_pool,
    create_checkpointer
)
from app.agents.authorization_supervisor_graph import (
    create_authorization_supervisor_graph
)
from app.db.session import engine

from app.core.logging_config import setup_logging

setup_logging()
import logging

logger = logging.getLogger(__name__)






@asynccontextmanager
async def lifespan(app: FastAPI):

    pool = create_checkpointer_pool()

    try:
        # Start PostgreSQL connection pool.
        pool.open(wait=True)

        checkpointer = create_checkpointer(pool)

        # Initialize checkpoint tables.
        checkpointer.setup()

        graph = create_authorization_supervisor_graph(
            checkpointer
        )

        app.state.checkpointer_pool = pool
        app.state.checkpointer = checkpointer
        app.state.authorization_graph = graph
        app.state.redis_client = redis_client

        yield

    finally:
        # Close PostgreSQL and Redis connections.
        try:
            pool.close()
        finally:
            redis_client.close()


# uvicorn app.main:app lead the app variable when it start
app=FastAPI(title="HealthGuard AI", lifespan=lifespan)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next
):
    request_id = str(uuid4())
    request.state.request_id = request_id

    try:
        response = await call_next(request)

    except Exception as exc:
        response = await unexpected_exception_handler(
            request,
            exc
        )

    response.headers["X-Request-ID"] = request_id

    return response
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(
    Exception,
    unexpected_exception_handler
)


app.include_router(authorization_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(reviews_router)
app.include_router(policies_router)
app.include_router(member_coverages_router)
app.include_router(members)


@app.get("/")
def root():

    logger.info("HealthGuard AI API root endpoint accessed")

    return {
        "message": "HealthGuard AI API"
    }




#infrastructure can uses health aoi to determine whether the application is alive/healthy.
@app.get("/health")
def health():
    return{
        "status":"healthy"
    }



# alembic revision --autogenerate -m "add phone to users"
# alembic upgrade head
#  ALTER TABLE users ADD COLUMN phone ...
# create_all()
# → creates missing tables only

# Alembic
# → creates + changes schema safely

# DROP TABLE
# → deletes table + its data
