"""FastAPI application — recipe service.

This module wires the path operations, lifespan, and CORS middleware.

Discipline gates the autograder enforces:
- Neo4j driver, Weaviate client, spaCy pipeline, and the flan-t5-base
  generator are constructed exactly once per process inside `lifespan`.
- `CORSMiddleware` is registered with `allow_origins=[WEB_ORIGIN]`.
- `/extract`, `/kg/query`, `/rag/answer` use Pydantic shapes from
  `models.py` (no anonymous dicts; use Pydantic v2 idioms (model_dump, not the deprecated v1 serialization shortcut)).
- `/kg/query` converts `UnsupportedQueryError` to 422 with structured
  detail (`{"reason": "unsupported_question", "supported_patterns": [...]}`).
- `/readyz` probes Neo4j (`RETURN 1`) AND Weaviate (`client.is_ready()`)
  within 2 seconds; failure → 503.
- `/healthz` does NOT touch Neo4j or Weaviate.
"""
import os
import asyncio
from contextlib import asynccontextmanager

import spacy
import weaviate
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .m8_rag.generator import load_generator
from .nlp import extract_entities
from .kg import wrap_kg_query
from .rag import compose_rag
from .w9b_mapper.errors import UnsupportedQueryError
from .w9b_mapper.shapes import SUPPORTED_PATTERNS
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
from .auth import LoginRequest, TokenResponse, get_current_user, verify_admin_scope, create_access_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Process-scoped resource setup and teardown.

    On startup: open the Neo4j Bolt driver, construct the Weaviate
    client, load the spaCy `en_core_web_sm` pipeline, and load the
    flan-t5-base generator. Stash each on `app.state` so `Depends()`
    helpers can resolve them.
    """
    # TODO: construct the five resources once and stash each on
    #       `app.state` (see deps.py for the attribute names the
    #       autograder pins):
    #         - Neo4j Bolt driver — read the URI + credentials from
    #           os.environ.
    #         - Weaviate client — read WEAVIATE_URL from os.environ.
    #         - spaCy pipeline — the `en_core_web_sm` model installed by
    #           the Lab Dockerfile.
    #         - flan-t5-base generator — load via the vendored helper in
    #           `.m8_rag` (do NOT modify the m8_rag package).
    #         - sentence-transformers embedder — load the same model
    #           the seed used (`sentence-transformers/all-MiniLM-L6-v2`).
    #           Required for the query-side embedding `/rag/answer`
    #           needs to do, since the Weaviate class is
    #           `vectorizer=none`.
    # Then `yield` (so request handling can proceed), and on shutdown
    # close the Neo4j driver.
    
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    app.state.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    weaviate_url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
    app.state.weaviate_client = weaviate.Client(url=weaviate_url)
    
    app.state.nlp = spacy.load("en_core_web_sm")
    app.state.generator = load_generator()
    app.state.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    yield
    app.state.neo4j_driver.close()


app = FastAPI(title="M10 Recipe Service", lifespan=lifespan)

# TODO: register CORSMiddleware so the Next.js frontend can call the
#       API from the browser. Allow the origin set by the WEB_ORIGIN
#       env var (with a sensible localhost default for `npm run dev`).
#       See the Reading's CORS section for the middleware arguments.
web_origin = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest, nlp=Depends(get_nlp), user=Depends(get_current_user)):
    """Run spaCy NER on the input text; return entities ordered by `start`.

    Returns ExtractResponse with entities sorted by `start` ascending.
    """
    # TODO: type-annotate the request body, wire response_model on the
    #       decorator, run NER via the helper in nlp.py, and return the
    #       typed response.
    entities = extract_entities(req.text, nlp)
    return ExtractResponse(entities=entities)


@app.post("/kg/query", response_model=KGResponse)
def kg_query(req: KGRequest, session=Depends(get_session)):
    """Run the W9B mapper and execute the resulting Cypher.

    Returns KGResponse(cypher=..., rows=[r.data() for r in session.run(...)], count=len(rows)).
    UnsupportedQueryError → HTTPException(422, detail=UnsupportedQueryDetail(...).model_dump()).
    """
    # TODO: type-annotate the request body, wire response_model on the
    #       decorator, run the W9B mapper via the helper in kg.py,
    #       execute the cypher in a Neo4j session, materialize the rows,
    #       and return the typed response. Convert UnsupportedQueryError
    #       to a structured 422.
    try:
        cypher, params = wrap_kg_query(req.question)
    except UnsupportedQueryError as e:
        detail = UnsupportedQueryDetail(
            reason="unsupported_question",
            supported_patterns=list(SUPPORTED_PATTERNS)
        )
        raise HTTPException(status_code=422, detail=detail.model_dump())
    
    result = session.run(cypher, **params)
    rows = [r.data() for r in result]
    return KGResponse(cypher=cypher, rows=rows, count=len(rows))


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(req: RAGRequest, weaviate_client=Depends(get_weaviate), generator=Depends(get_generator), embedder=Depends(get_embedder)):
    """Retrieve → assemble → generate → cite → grounding check.

    Returns RAGResponse with citations populated when a grounded answer
    is available, or the SENTINEL with empty citations when retrieval
    or citation extraction fails.
    """
    # TODO: type-annotate the request body, wire response_model on the
    #       decorator, run the RAG composition via the helper in rag.py
    #       (passing the injected weaviate client and generator), and
    #       return the typed response.
    res = compose_rag(req.question, embedder, weaviate_client, generator, req.k)
    return RAGResponse(answer=res["answer"], citations=res["citations"], confidence=res["confidence"])


@app.get("/healthz", response_model=HealthResponse)
def healthz():
    """Liveness probe. Must NOT touch Neo4j or Weaviate."""
    # TODO: wire response_model on the decorator and return the typed
    #       liveness response.
    return HealthResponse(status="ok")


@app.get("/readyz")
async def readyz(session=Depends(get_session), weaviate_client=Depends(get_weaviate)):
    """Readiness probe.

    Returns 200 only if `RETURN 1` against Neo4j AND `client.is_ready()`
    against Weaviate both succeed within 2 seconds. Otherwise 503 with
    structured detail naming which backend failed.
    """
    # TODO: probe both backends within the 2-second budget, populate
    #       the readiness detail, and raise an HTTP error with the
    #       readiness detail if either probe fails.
    neo4j_status = "down"
    weaviate_status = "down"
    
    async def check_neo4j():
        try:
            res = await asyncio.to_thread(session.run, "RETURN 1")
            if res.single():
                return "ok"
        except Exception:
            pass
        return "down"
        
    async def check_weaviate():
        try:
            if await asyncio.to_thread(weaviate_client.is_ready):
                return "ok"
        except Exception:
            pass
        return "down"

    try:
        neo4j_status, weaviate_status = await asyncio.wait_for(
            asyncio.gather(check_neo4j(), check_weaviate()),
            timeout=2.0
        )
    except asyncio.TimeoutError:
        pass
        
    if neo4j_status == "ok" and weaviate_status == "ok":
        return {"neo4j": "ok", "weaviate": "ok"}
        
    detail = {"neo4j": neo4j_status, "weaviate": weaviate_status}
    raise HTTPException(status_code=503, detail=detail)

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    valid_users = {
        "admin": "admin",
        "demo": "demo",
        "stretch": "stretch"
    }
    if req.username in valid_users and valid_users[req.username] == req.password:
        token = create_access_token(sub=req.username)
        return TokenResponse(access_token=token, token_type="bearer")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/admin/echo")
def admin_echo(payload: dict = Depends(verify_admin_scope)):
    return payload
