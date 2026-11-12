from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings



# DATABASE_URL = (
#     "postgresql+psycopg://"
#     "healthguard:healthguard@127.0.0.1:5433/healthguard"
# )

# 1. Engine → database connection/communication
engine=create_engine(
    settings.DATABASE_URL,
    # Show me the SQL queries you are executing."
    echo=False,

    hide_parameters=True,
    pool_pre_ping=True
)
# Session → "Perform DB operations."
# "Execute this INSERT/UPDATE/DELETE/query."
sessionlocal=sessionmaker(
    bind=engine,
    # send the pending operation to the database flush()
    autoflush=False,
    # commit the transaction permanently
    # after commiting by default the attribute is expire but after FALSE teh attribute will not expire
    expire_on_commit=False
)
