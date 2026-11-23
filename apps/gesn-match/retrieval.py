"""Hybrid candidate retrieval: FTS (russian) + pg_trgm + pgvector.

Fusion is reciprocal rank fusion (RRF, k=60): scale-free, no weight
calibration needed. Raw branch scores are kept for diagnostics.
"""
from __future__ import annotations

RRF_K = 60

CANDIDATE_SQL = """
WITH q AS (
  SELECT plainto_tsquery('russian', %(text)s) AS tsq,
         %(text)s AS raw,
         %(embedding)s::vector AS emb
),
fts AS (
  SELECT n.code,
         ts_rank(n.search_tsv, q.tsq) AS fts_score,
         ROW_NUMBER() OVER (ORDER BY ts_rank(n.search_tsv, q.tsq) DESC) AS rnk
  FROM norms n, q
  WHERE n.collection = %(collection)s AND n.edition_id = %(edition_id)s
    AND n.search_tsv @@ q.tsq
),
trgm AS (
  SELECT n.code,
         GREATEST(word_similarity(q.raw, n.code), word_similarity(q.raw, n.title)) AS trgm_score,
         ROW_NUMBER() OVER (ORDER BY GREATEST(word_similarity(q.raw, n.code), word_similarity(q.raw, n.title)) DESC) AS rnk
  FROM norms n, q
  WHERE n.collection = %(collection)s AND n.edition_id = %(edition_id)s
    AND (n.code %%> q.raw OR n.title %%> q.raw)
),
vec AS (
  SELECT n.code,
         1 - (e.embedding <=> q.emb) AS vec_score,
         ROW_NUMBER() OVER (ORDER BY e.embedding <=> q.emb) AS rnk
  FROM norms n
  JOIN norm_embeddings e ON e.norm_code = n.code
    AND e.collection = n.collection AND e.edition_id = n.edition_id, q
  WHERE n.collection = %(collection)s AND n.edition_id = %(edition_id)s
  ORDER BY e.embedding <=> q.emb
  LIMIT %(vec_prefetch)s
)
SELECT n.code, n.title, n.unit, n.work_composition, n.table_code,
       n.source_ref, n.needs_review,
       COALESCE(f.fts_score, 0) AS fts_score,
       COALESCE(t.trgm_score, 0) AS trgm_score,
       COALESCE(v.vec_score, 0) AS vec_score,
       (COALESCE(1.0 / (%(rrf_k)s + f.rnk), 0)
        + COALESCE(1.0 / (%(rrf_k)s + t.rnk), 0)
        + COALESCE(1.0 / (%(rrf_k)s + v.rnk), 0)) AS score
FROM norms n
LEFT JOIN fts f ON f.code = n.code
LEFT JOIN trgm t ON t.code = n.code
LEFT JOIN vec v ON v.code = n.code, q
WHERE n.collection = %(collection)s AND n.edition_id = %(edition_id)s
  AND (f.code IS NOT NULL OR t.code IS NOT NULL OR v.code IS NOT NULL)
ORDER BY score DESC
LIMIT %(limit)s
"""


def search_candidates(con, vor_text: str, embedding: list[float],
                      collection: str, edition_id: str,
                      limit: int = 30) -> list[dict]:
    """Return up to `limit` candidates; [] when nothing matches (not an error)."""
    text = (vor_text or "").strip()
    if not text:
        return []

    cur = con.execute(
        CANDIDATE_SQL,
        {
            "text": text,
            "embedding": embedding,
            "collection": collection,
            "edition_id": edition_id,
            "limit": limit,
            "vec_prefetch": max(limit * 4, 100),
            "rrf_k": RRF_K,
        },
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
