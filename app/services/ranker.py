import math
import re
from collections import Counter

from langchain_core.embeddings import Embeddings
from sqlmodel import Session, select

from app.models import Program, ProgramDoc


class HashEmbeddings(Embeddings):
    """Lightweight deterministic embeddings for offline demos."""

    def __init__(self, dims: int = 256) -> None:
        self.dims = dims

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        counts = Counter(words)
        for token, count in counts.items():
            vec[hash(token) % self.dims] += float(count)

        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            return vec
        return [x / norm for x in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _snippet(text: str, max_chars: int = 120) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip() + "..."


class ProgramRanker:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.embedder = HashEmbeddings()

    def _load_docs(self, discipline_filter: str | None = None) -> list[tuple[Program, ProgramDoc]]:
        stmt = select(Program, ProgramDoc).join(ProgramDoc, Program.id == ProgramDoc.id)
        rows = self.session.exec(stmt).all()
        if not discipline_filter:
            return rows

        needle = discipline_filter.lower()
        return [(p, d) for p, d in rows if needle in p.discipline_name.lower()]

    def rank(self, query: str, top_k: int = 10, discipline: str | None = None) -> list[dict]:
        rows = self._load_docs(discipline_filter=discipline)
        if not rows:
            return []

        texts = [doc.page_content for _, doc in rows]
        query_vec = self.embedder.embed_query(query)
        doc_vecs = self.embedder.embed_documents(texts)

        query_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))

        scored = []
        for (program, doc), vec in zip(rows, doc_vecs):
            semantic = _cosine(query_vec, vec)
            keyword_bonus = 0.0
            joined = f"{program.program_name} {program.program_stream_name}".lower()
            if any(term in joined for term in query_terms):
                keyword_bonus = 0.1
            discipline_bonus = 0.2 if discipline and discipline.lower() in program.discipline_name.lower() else 0.0
            score = (0.7 * semantic) + discipline_bonus + keyword_bonus
            scored.append((score, program, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        return [
            {
                "program_id": p.id,
                "program_name": p.program_name,
                "school_name": p.school_name,
                "discipline_name": p.discipline_name,
                "score": round(float(score), 4),
                "description_snippet": _snippet(d.page_content),
            }
            for score, p, d in top
        ]
