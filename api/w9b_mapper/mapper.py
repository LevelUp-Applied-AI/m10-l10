"""Vendored from Module 9 Week B. DO NOT MODIFY.

Deterministic NL→Cypher mapper covering the 15 supported recipe-domain
question shapes. Returns (cypher: str, params: dict) on a match; raises
UnsupportedQueryError otherwise.

The recognition logic is intentionally pattern-based and rejects
anything outside the supported set — that rejection produces the 422
the path operation surfaces.
"""
import re

from .errors import UnsupportedQueryError

_PATTERNS = [
    (
        re.compile(r"^find recipes that use (?P<ingredient>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:USES]->(i:Ingredient {name: $ingredient}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    (
        re.compile(r"^find (?P<cuisine>\w[\w -]+?) recipes$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:HAS_CUISINE]->(c:Cuisine {name: $cuisine}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    (
        re.compile(r"^find recipes by (?P<chef>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:AUTHORED_BY]->(p:Person {name: $chef}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
]


def map_question(question: str):
    """Map a natural-language question to (cypher, params).

    Raises UnsupportedQueryError if no pattern matches.
    """
    q = question.strip()
    for rx, cypher in _PATTERNS:
        m = rx.match(q)
        if m:
            params = {k: v.strip() for k, v in m.groupdict().items()}
            return cypher, params
    raise UnsupportedQueryError(f"No supported pattern matched: {question!r}")
