"""Pydantic request/response models for the recipe service.

These are the typed-boundary contracts. They must mirror the TypeScript
interfaces in `web/lib/types.ts` exactly — `chunk_id` not `chunkId`,
`start` not `start_char`. Drift produces silent render failures in the
Next.js frontend.

Constraints below are the source of truth for the autograder's 422 gates.
"""
from typing import List, Literal

from pydantic import BaseModel, Field


# --- /extract --------------------------------------------------------

class ExtractRequest(BaseModel):
    """Request body for POST /extract.

    `text` must be non-empty and at most 5000 characters.
    """
    # TODO: declare `text: str` with Field(..., min_length=1, max_length=5000).
    pass


class Entity(BaseModel):
    """A single named-entity span.

    Field names must match `web/lib/types.ts` exactly.
    """
    # TODO: declare text (str), label (str), start (int), end (int).
    pass


class ExtractResponse(BaseModel):
    """Response body for POST /extract.

    Per the Evaluation Methodology, `entities` is ordered by `start`
    ascending.
    """
    # TODO: declare `entities: List[Entity]`.
    pass


# --- /kg/query -------------------------------------------------------

class KGRequest(BaseModel):
    """Request body for POST /kg/query."""
    # TODO: declare `question: str` with min_length=1, max_length=500.
    pass


class KGResponse(BaseModel):
    """Response body for POST /kg/query."""
    # TODO: declare cypher (str), rows (List[dict]), count (int).
    pass


class UnsupportedQueryDetail(BaseModel):
    """Structured detail returned on 422 from /kg/query."""
    reason: Literal["unsupported_question"]
    supported_patterns: List[str]


# --- /rag/answer -----------------------------------------------------

class RAGRequest(BaseModel):
    """Request body for POST /rag/answer."""
    # TODO: declare question (str, min_length=1, max_length=500) and
    #       k (int, ge=1, le=10, default=4).
    pass


class Citation(BaseModel):
    """One citation: chunk id and retrieval score."""
    # TODO: declare chunk_id (int), score (float).
    pass


class RAGResponse(BaseModel):
    """Response body for POST /rag/answer.

    Grounding contract: when `answer` is not the empty-retrieval
    sentinel, `len(citations) > 0` is required.
    """
    # TODO: declare answer (str), citations (List[Citation]),
    #       confidence (float).
    pass


# --- Health / readiness ---------------------------------------------

class HealthResponse(BaseModel):
    """Liveness response."""
    # TODO: declare status (str).
    pass


class ReadyDetail(BaseModel):
    """Readiness detail naming each backend's status."""
    neo4j: str
    weaviate: str
