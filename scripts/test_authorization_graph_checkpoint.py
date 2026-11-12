import uuid

from app.db.checkpointer import (
    create_checkpointer_pool,
    create_checkpointer
)

from app.agents.authorization_supervisor_graph import (
    create_authorization_supervisor_graph
)


def test_authorization_graph_checkpoint():

    pool = create_checkpointer_pool()

    try:
        pool.open(wait=True)

        checkpointer = create_checkpointer(pool)
        checkpointer.setup()

        graph = create_authorization_supervisor_graph(
            checkpointer
        )

        thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state = graph.get_state(config)

        print("Graph compiled successfully")
        print("Thread ID:", thread_id)
        print("Initial checkpoint:", state.values)

    finally:
        pool.close()


if __name__ == "__main__":
    test_authorization_graph_checkpoint()
