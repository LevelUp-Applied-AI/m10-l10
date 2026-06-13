"""FastAPI dependency-injection helpers.

These functions resolve process-scoped resources (Neo4j driver, Weaviate
client, spaCy pipeline, flan-t5-base generator) that were constructed
once in `main.lifespan` and stored on `app.state`. Path operations
declare these via `Depends()` so the resource is fetched per request
without being re-constructed.
"""
from fastapi import Request


async def get_session(request: Request):
    """Yield a short-lived Neo4j session from the process-scoped driver.

    Yields one session per request; closes it on exit.
    """
    # TODO: access request.app.state.neo4j_driver, open a session via
    #       `with driver.session() as session: yield session`.
    raise NotImplementedError


def get_weaviate(request: Request):
    """Return the process-scoped Weaviate client."""
    # TODO: return request.app.state.weaviate_client.
    raise NotImplementedError


def get_generator(request: Request):
    """Return the process-scoped flan-t5-base generator."""
    # TODO: return request.app.state.generator.
    raise NotImplementedError


def get_nlp(request: Request):
    """Return the process-scoped spaCy pipeline."""
    # TODO: return request.app.state.nlp.
    raise NotImplementedError
