"""TF-IDF cosine similarity ranker for repository files."""

from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def rank_files(files: list[dict[str, Any]], query: str, max_files: int) -> list[dict[str, Any]]:
    """Rank files by TF-IDF cosine similarity to query; return top max_files with scores."""
    if not files:
        return []

    corpus = [query] + [f["content"] for f in files]
    vectorizer = TfidfVectorizer(sublinear_tf=True)
    matrix = vectorizer.fit_transform(corpus)

    query_vec = matrix[0]
    file_vecs = matrix[1:]
    similarities = cosine_similarity(query_vec, file_vecs).flatten()

    ranked = []
    for file, score in zip(files, similarities):
        ranked.append({**file, "score": round(float(score), 3)})

    ranked.sort(key=lambda f: f["score"], reverse=True)
    return ranked[:max_files]
