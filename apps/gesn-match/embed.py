"""Embeddings backfill (e5-small) + cross-encoder reranker (lazy).

e5-small query/passage prefixes are required by the model.
"""
from __future__ import annotations

RERANKER_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

_st_model = None
_reranker = None


def get_st_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer(MODEL_NAME)
    return _st_model


def embed_passages(texts: list[str]) -> list[list[float]]:
    model = get_st_model()
    return model.encode(
        [f"passage: {t}" for t in texts],
        batch_size=256,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()


def embed_query(text: str) -> list[float]:
    model = get_st_model()
    return model.encode(
        f"query: {text}",
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()


def norm_text(row: dict) -> str:
    parts = [row.get("title", "")]
    parts.extend(row.get("work_composition") or [])
    return " ".join(p for p in parts if p)[:4000]


def backfill_embeddings(con, edition_id: str, batch: int = 256) -> int:
    """Encode norms missing from norm_embeddings. Idempotent; returns count."""
    done = 0
    while True:
        rows = con.execute(
            """SELECT code, title, work_composition FROM norms
               WHERE edition_id = %s AND code NOT IN (SELECT norm_code FROM norm_embeddings)
               ORDER BY code LIMIT %s""",
            (edition_id, batch),
        ).fetchall()
        if not rows:
            break
        texts = [norm_text({"title": t, "work_composition": w}) for _, t, w in rows]
        vectors = embed_passages(texts)
        for (code, _, _), vec in zip(rows, vectors):
            con.execute(
                """INSERT INTO norm_embeddings(norm_code, embedding)
                   VALUES (%s, %s) ON CONFLICT (norm_code) DO NOTHING""",
                (code, vec),
            )
        con.commit()
        done += len(rows)
        print(f"  ... {done} embedded", flush=True)
    return done


def rerank(vor_text: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Cross-encoder rerank 30 -> top_k. Score kept as rerank_score (sort only)."""
    global _reranker
    if not candidates:
        return []
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(RERANKER_NAME, max_length=512)
    pairs = [
        (vor_text, f"{c.get('title', '')} {' '.join(c.get('work_composition') or [])}"[:2000])
        for c in candidates
    ]
    scores = _reranker.predict(pairs, batch_size=32, show_progress_bar=False)
    ranked = sorted(zip(candidates, scores), key=lambda p: p[1], reverse=True)
    out = []
    for cand, score in ranked[:top_k]:
        cand = dict(cand)
        cand["rerank_score"] = float(score)
        out.append(cand)
    return out
