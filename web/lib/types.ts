// TypeScript interfaces — must mirror api/models.py exactly.
//
// Field name drift between these interfaces and the Pydantic shapes is
// silent: the page renders nothing because the destructure fails.
// Use snake_case here for any field that is snake_case in the Pydantic
// model — do not camelCase.

// TODO: declare the Entity interface with the fields used by /extract.
export interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
}

// TODO: declare the ExtractResponse interface returned by /extract.
export interface ExtractResponse {
  entities: Entity[];
}

// TODO: declare the KGResponse interface returned by /kg/query.
export interface KGResponse {
  cypher: string;
  rows: Record<string, any>[];
  count: number;
}

// TODO: declare the Citation interface used inside /rag/answer.
export interface Citation {
  chunk_id: number;
  score: number;
}

// TODO: declare the RAGResponse interface returned by /rag/answer.
export interface RAGResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
}
