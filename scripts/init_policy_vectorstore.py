from langchain_postgres import Column, PGEngine

from app.db.session import DATABASE_URL

from app.rag.constants import EMBIDDING_DIMENSION , POLICY_VECTOR_TABLE

def initialize_policy_vectorstore()->None:
    engine=PGEngine.from_connection_string(
        url=DATABASE_URL
    )

    engine.init_vectorstore_table(
        table_name=POLICY_VECTOR_TABLE,
        vector_size=EMBIDDING_DIMENSION,
        content_column="content",
        embedding_column="embedding",
        id_column=Column("langchain_id", "VARCHAR"),
        metadata_columns=[
            Column("organization_id", "INTEGER"),
            Column("policy_version_id", "INTEGER"),
            Column("document_id", "INTEGER"),
            Column("page_number", "INTEGER"),
            Column("chunk_index", "INTEGER"),
            Column("section", "TEXT"),
            Column("source", "TEXT"),
        ],
    )

    print("Policy vector-store table initialized.")

if __name__ == "__main__":
    import asyncio

    asyncio.set_event_loop_policy(
        asyncio._WindowsSelectorEventLoopPolicy()
    )

    initialize_policy_vectorstore()
