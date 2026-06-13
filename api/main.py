"""FastAPI application — recipe service.

This module wires the path operations, lifespan, and CORS middleware.

Discipline gates the autograder enforces:
- Neo4j driver, Weaviate client, spaCy pipeline, and the flan-t5-base
  generator are constructed exactly once per process inside `lifespan`.
- `CORSMiddleware` is registered with `allow_origins=[WEB_ORIGIN]`.
- `/extract`, `/kg/query`, `/rag/answer` use Pydantic shapes from
  `models.py` (no anonymous dicts; no `.dict()` v1 idioms).
- `/kg/query` converts `UnsupportedQueryError` to 422 with structured
  detail (`{"reason": "unsupported_question", "supported_patterns": [...]}`).
- `/readyz` probes Neo4j (`RETURN 1`) AND Weaviate (`client.is_ready()`)
  within 2 seconds; failure → 503.
- `/healthz` does NOT touch Neo4j or Weaviate.
"""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .deps import get_generator, get_nlp, get_session, get_weaviate
from .models import (
    Entity,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    UnsupportedQueryDetail,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Process-scoped resource setup and teardown.

    On startup: open the Neo4j Bolt driver, construct the Weaviate
    client, load the spaCy `en_core_web_sm` pipeline, and load the
    flan-t5-base generator. Stash each on `app.state` so `Depends()`
    helpers can resolve them.
    """
    # TODO:
    # 1. app.state.neo4j_driver = GraphDatabase.driver(
    #        os.environ["NEO4J_URI"],
    #        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    #    )
    # 2. app.state.weaviate_client = weaviate.Client(os.environ["WEAVIATE_URL"])
    # 3. app.state.nlp = spacy.load("en_core_web_sm")
    # 4. app.state.generator = load_generator()  # from .m8_rag
    # 5. yield
    # 6. Close the Neo4j driver on shutdown.
    yield


app = FastAPI(title="M10 Recipe Service", lifespan=lifespan)

# TODO: register CORSMiddleware with allow_origins reading from the
#       WEB_ORIGIN env var (default http://localhost:3000), and
#       allow_methods=["*"], allow_headers=["*"].


@app.post("/extract")
def extract(req, nlp=Depends(get_nlp)):
    """Run spaCy NER on the input text; return entities ordered by `start`.

    Returns ExtractResponse with entities sorted by `start` ascending.
    """
    # TODO: annotate `req: ExtractRequest`, set
    #       response_model=ExtractResponse, call extract_entities, return
    #       ExtractResponse(entities=...).
    raise NotImplementedError


@app.post("/kg/query")
def kg_query(req, session=Depends(get_session)):
    """Run the W9B mapper and execute the resulting Cypher.

    Returns KGResponse(cypher=..., rows=[r.data() for r in session.run(...)], count=len(rows)).
    UnsupportedQueryError → HTTPException(422, detail=UnsupportedQueryDetail(...).model_dump()).
    """
    # TODO: annotate `req: KGRequest`, set response_model=KGResponse,
    #       call wrap_kg_query, catch UnsupportedQueryError → raise 422,
    #       run the cypher, materialize rows via `.data()`, return KGResponse.
    raise NotImplementedError


@app.post("/rag/answer")
def rag_answer(req, weaviate_client=Depends(get_weaviate), generator=Depends(get_generator)):
    """Retrieve → assemble → generate → cite → grounding check.

    Returns RAGResponse with citations populated when a grounded answer
    is available, or the SENTINEL with empty citations when retrieval
    or citation extraction fails.
    """
    # TODO: annotate `req: RAGRequest`, set response_model=RAGResponse,
    #       call compose_rag(req.question, weaviate_client, generator, k=req.k),
    #       return RAGResponse(**result).
    raise NotImplementedError


@app.get("/healthz")
def healthz():
    """Liveness probe. Must NOT touch Neo4j or Weaviate."""
    # TODO: annotate response_model=HealthResponse and return
    #       HealthResponse(status="ok").
    raise NotImplementedError


@app.get("/readyz")
def readyz(session=Depends(get_session), weaviate_client=Depends(get_weaviate)):
    """Readiness probe.

    Returns 200 only if `RETURN 1` against Neo4j AND `client.is_ready()`
    against Weaviate both succeed within 2 seconds. Otherwise 503 with
    structured detail naming which backend failed.
    """
    # TODO: probe both backends; populate ReadyDetail; raise HTTPException(503)
    #       if either probe fails; return ReadyDetail on success.
    raise NotImplementedError
