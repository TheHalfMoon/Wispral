# SPDX-License-Identifier: Apache-2.0
"""Cited Tenant-ACL Hybrid RAG Knowledge Engine.

Combines SQLite FTS5 lexical BM25 search with deterministic character/token n-gram dense-vector
cosine similarity via Reciprocal Rank Fusion (RRF, k=60). Supports 4-level Arabic match-key
normalization, enforces tenant + document ACL tags, emits exact passage citations, and explicitly
distinguishes `SUPPORTED`, `CONFIRMED_NEGATIVE`, and `UNAVAILABLE`.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from klaint.core.arabic import normalize_arabic
from klaint.core.errors import TenantIsolationError
from klaint.core.models import AuthenticatedSession, iso_utc, new_id, validate_tenant_id
from klaint.storage.tenant_db import TenantDatabase

VECTOR_DIM = 256
RRF_K = 60

_NEGATIVE_POLICY_PATTERNS = (
    re.compile(
        r"\b(?:not\s+offered|not\s+supported|not\s+eligible|non-refundable|no\s+refunds?\s+on|"
        r"cannot\s+be\s+refunded|never\s+refunded|excluded\s+from\s+refund|prohibited|unavailable\s+for|"
        r"do\s+not\s+ship|do\s+not\s+accept|do\s+not\s+offer)\b",
        re.IGNORECASE,
    ),
    # Normalized Level-3 Arabic negative policy phrases
    re.compile(
        r"(?:لا\s+يتم\s+استرداد|غير\s+قابل\s+للاسترداد|لا\s+تتوفر|لا\s+ندعم|غير\s+مدعوم|"
        r"لا\s+نقبل|لا\s+يشمل\s+الاسترداد|ممنوع|لا\s+تقدم|غير\s+متاح\s+نهائيا)"
    ),
)

_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "do",
        "does",
        "can",
        "you",
        "we",
        "i",
        "my",
        "for",
        "on",
        "in",
        "to",
        "of",
        "and",
        "or",
        "what",
        "how",
        "about",
        "هل",
        "ما",
        "من",
        "في",
        "على",
        "عن",
        "او",
        "و",
        "لي",
        "هو",
        "هي",
        "تم",
        "كم",
        "ان",
    }
)


class KnowledgeStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONFIRMED_NEGATIVE = "CONFIRMED_NEGATIVE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class Citation:
    doc_id: str
    chunk_id: str
    title: str
    quote: str
    rrf_score: float
    polarity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "title": self.title,
            "quote": self.quote,
            "rrf_score": round(self.rrf_score, 6),
            "polarity": self.polarity,
        }


@dataclass(frozen=True)
class KnowledgeSearchResult:
    status: KnowledgeStatus
    abstain_required: bool
    citations: list[Citation]
    query_normalized: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "abstain_required": self.abstain_required,
            "citations": [c.to_dict() for c in self.citations],
            "query_normalized": self.query_normalized,
        }


def _detect_chunk_polarity(raw_text: str, normalized_text: str, explicit_polarity: str | None = None) -> str:
    if explicit_polarity in ("affirmative", "negative"):
        return explicit_polarity
    if _NEGATIVE_POLICY_PATTERNS[0].search(raw_text) or _NEGATIVE_POLICY_PATTERNS[1].search(normalized_text):
        return "negative"
    return "affirmative"


def _embed_normalized_text(normalized_text: str) -> list[float]:
    """Deterministic L2-normalized feature-hashed dense embedding over word unigrams/bigrams and char 3..4-grams."""
    vec = [0.0] * VECTOR_DIM
    tokens = [tok for tok in normalized_text.split() if tok]
    if not tokens:
        return vec

    features: list[tuple[str, float]] = []
    for tok in tokens:
        weight = 0.25 if tok in _STOPWORDS else 2.0
        features.append((f"w:{tok}", weight))
        if tok not in _STOPWORDS and len(tok) >= 3:
            padded = f"<{tok}>"
            for n in (3, 4):
                for idx in range(max(0, len(padded) - n + 1)):
                    features.append((f"c{n}:{padded[idx:idx + n]}", 0.65))

    for t1, t2 in zip(tokens, tokens[1:]):
        features.append((f"b:{t1}_{t2}", 1.5))

    for feat, weight in features:
        digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        h = int.from_bytes(digest, "little")
        bucket = h % VECTOR_DIM
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[bucket] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0.0:
        vec = [v / norm for v in vec]
    return vec


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _split_into_passages(text: str, max_chars: int = 420) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?؟])\s+", para) if s.strip()]
            buf = ""
            for sent in sentences:
                if not buf:
                    buf = sent
                elif len(buf) + 1 + len(sent) <= max_chars:
                    buf = f"{buf} {sent}"
                else:
                    chunks.append(buf)
                    buf = sent
            if buf:
                chunks.append(buf)
    return chunks or ([text.strip()] if text.strip() else [])


def _content_tokens(normalized_text: str) -> set[str]:
    return {t for t in normalized_text.split() if len(t) >= 2 and t not in _STOPWORDS}


class HybridKnowledgeEngine:
    """Tenant-isolated, ACL-enforced FTS5 + dense cosine RRF (k=60) knowledge retriever."""

    def __init__(self, db: TenantDatabase) -> None:
        self.db = db

    def ingest_document(
        self,
        *,
        title: str,
        content: str,
        language: str = "en",
        acl_tags: list[str] | tuple[str, ...] = ("public", "customer"),
        polarity: str | None = None,
        doc_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_doc_id = doc_id or new_id("doc", 8)
        tags_list = sorted({str(t).strip() for t in acl_tags if str(t).strip()})
        if not tags_list:
            raise ValueError("Document acl_tags must contain at least one tag")

        passages = _split_into_passages(content)
        if not passages:
            raise ValueError("Document content cannot be empty")

        now = iso_utc()
        doc_norm = normalize_arabic(content, level=3)
        doc_polarity = _detect_chunk_polarity(content, doc_norm, polarity)

        chunk_ids: list[str] = []
        with self.db.immediate_transaction() as conn:
            existing = conn.execute(
                "SELECT chunk_id FROM knowledge_chunks WHERE doc_id = ?",
                (resolved_doc_id,),
            ).fetchall()
            for r in existing:
                conn.execute("DELETE FROM knowledge_chunks_fts WHERE chunk_id = ?", (str(r["chunk_id"]),))
            conn.execute("DELETE FROM knowledge_chunks WHERE doc_id = ?", (resolved_doc_id,))
            conn.execute("DELETE FROM knowledge_docs WHERE doc_id = ?", (resolved_doc_id,))

            conn.execute(
                """
                INSERT INTO knowledge_docs (doc_id, tenant_id, title, language, acl_tags_json, polarity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_doc_id,
                    self.db.tenant_id,
                    title,
                    language,
                    json.dumps(tags_list),
                    doc_polarity,
                    now,
                ),
            )

            for idx, passage in enumerate(passages):
                chunk_id = f"{resolved_doc_id}#c{idx + 1}"
                norm_passage = normalize_arabic(passage, level=3)
                chunk_pol = _detect_chunk_polarity(passage, norm_passage, polarity)
                emb = _embed_normalized_text(f"{normalize_arabic(title, level=3)} {norm_passage}")
                conn.execute(
                    """
                    INSERT INTO knowledge_chunks (
                        chunk_id, doc_id, tenant_id, chunk_index, content,
                        normalized_content, polarity, embedding_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        resolved_doc_id,
                        self.db.tenant_id,
                        idx,
                        passage,
                        norm_passage,
                        chunk_pol,
                        json.dumps(emb),
                    ),
                )
                conn.execute(
                    "INSERT INTO knowledge_chunks_fts (chunk_id, doc_id, normalized_content) VALUES (?, ?, ?)",
                    (chunk_id, resolved_doc_id, f"{normalize_arabic(title, level=3)} {norm_passage}"),
                )
                chunk_ids.append(chunk_id)

            self.db.append_audit(
                event_kind="knowledge_ingested",
                actor="knowledge_engine",
                payload={
                    "doc_id": resolved_doc_id,
                    "title": title,
                    "chunk_count": len(chunk_ids),
                    "acl_tags": tags_list,
                },
                conn=conn,
            )

        return {
            "doc_id": resolved_doc_id,
            "tenant_id": self.db.tenant_id,
            "title": title,
            "chunk_ids": chunk_ids,
            "acl_tags": tags_list,
            "polarity": doc_polarity,
        }

    def list_documents(self) -> list[dict[str, Any]]:
        with self.db.read_connection() as conn:
            rows = conn.execute(
                """
                SELECT d.*, COUNT(c.chunk_id) AS chunk_count
                FROM knowledge_docs d
                LEFT JOIN knowledge_chunks c ON c.doc_id = d.doc_id
                WHERE d.tenant_id = ?
                GROUP BY d.doc_id
                ORDER BY d.created_at DESC
                """,
                (self.db.tenant_id,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            item["acl_tags"] = json.loads(str(r["acl_tags_json"]))
            out.append(item)
        return out

    def search(
        self,
        *,
        session: AuthenticatedSession,
        query: str,
        top_k: int = 3,
        min_cosine_floor: float = 0.16,
    ) -> KnowledgeSearchResult:
        """Execute tenant-isolated, ACL-filtered FTS5 + dense cosine RRF (k=60) search."""
        validate_tenant_id(session.tenant_id)
        if session.tenant_id != self.db.tenant_id:
            raise TenantIsolationError(
                f"Cross-tenant RAG access denied: session tenant {session.tenant_id!r} != knowledge DB {self.db.tenant_id!r}"
            )

        norm_query = normalize_arabic(query, level=3)
        query_terms = _content_tokens(norm_query)
        if not norm_query or not query_terms:
            return KnowledgeSearchResult(
                status=KnowledgeStatus.UNAVAILABLE,
                abstain_required=True,
                citations=[],
                query_normalized=norm_query,
            )

        caller_acl = set(session.acl_tags)
        with self.db.read_connection() as conn:
            all_rows = conn.execute(
                """
                SELECT c.chunk_id, c.doc_id, c.tenant_id, c.content, c.normalized_content,
                       c.polarity, c.embedding_json, d.title, d.acl_tags_json
                FROM knowledge_chunks c
                JOIN knowledge_docs d ON d.doc_id = c.doc_id
                WHERE c.tenant_id = ? AND d.tenant_id = ?
                """,
                (self.db.tenant_id, self.db.tenant_id),
            ).fetchall()

            allowed_chunks: dict[str, dict[str, Any]] = {}
            for row in all_rows:
                if str(row["tenant_id"]) != session.tenant_id:
                    raise TenantIsolationError("Tenant mismatch inside knowledge_chunks")
                doc_tags = set(json.loads(str(row["acl_tags_json"])))
                if not (caller_acl & doc_tags):
                    continue
                allowed_chunks[str(row["chunk_id"])] = dict(row)

            if not allowed_chunks:
                return KnowledgeSearchResult(
                    status=KnowledgeStatus.UNAVAILABLE,
                    abstain_required=True,
                    citations=[],
                    query_normalized=norm_query,
                )

            # 1. Lexical ranking via SQLite FTS5 BM25
            fts_terms = [re.sub(r"[^\w\u0600-\u06ff]", "", t) for t in query_terms]
            fts_terms = [t for t in fts_terms if t]
            lexical_ranks: dict[str, int] = {}
            if fts_terms:
                fts_expr = " OR ".join(f'"{t}"' for t in fts_terms)
                fts_rows = conn.execute(
                    """
                    SELECT chunk_id, bm25(knowledge_chunks_fts) AS score
                    FROM knowledge_chunks_fts
                    WHERE knowledge_chunks_fts MATCH ?
                    ORDER BY score ASC
                    LIMIT 50
                    """,
                    (fts_expr,),
                ).fetchall()
                rank_idx = 1
                for f_row in fts_rows:
                    cid = str(f_row["chunk_id"])
                    if cid in allowed_chunks:
                        lexical_ranks[cid] = rank_idx
                        rank_idx += 1

        # 2. Dense n-gram cosine similarity ranking
        query_vec = _embed_normalized_text(norm_query)
        dense_scored: list[tuple[float, str]] = []
        cosine_by_chunk: dict[str, float] = {}
        for cid, row in allowed_chunks.items():
            emb = json.loads(str(row["embedding_json"]))
            cos = _cosine_similarity(query_vec, emb)
            cosine_by_chunk[cid] = cos
            if cos >= min_cosine_floor:
                dense_scored.append((cos, cid))
        dense_scored.sort(key=lambda pair: pair[0], reverse=True)
        dense_ranks: dict[str, int] = {cid: idx + 1 for idx, (_, cid) in enumerate(dense_scored)}

        # 3. Reciprocal Rank Fusion (RRF, k = 60) + topical coverage guard against single-word false matches
        rrf_candidates: list[tuple[float, str]] = []
        for cid, row in allowed_chunks.items():
            in_lex = cid in lexical_ranks
            cos = cosine_by_chunk.get(cid, 0.0)
            chunk_terms = _content_tokens(f"{normalize_arabic(str(row['title']), level=3)} {row['normalized_content']}")

            # Count exact token matches plus >=4-char morphological prefix matches (e.g. return/returned, refund/refunds)
            matched_q = {
                qt
                for qt in query_terms
                if qt in chunk_terms
                or (len(qt) >= 4 and any(ct.startswith(qt[:4]) or qt.startswith(ct[:4]) for ct in chunk_terms if len(ct) >= 4))
            }
            coverage = len(matched_q) / max(1, len(query_terms))

            # Require strong topical coverage (>= 0.5 of query terms, or >= 2 distinct concept terms with cos >= 0.30)
            if coverage < 0.5 and not (len(matched_q) >= 2 and cos >= 0.30):
                continue
            if not in_lex and cid not in dense_ranks:
                continue

            score = 0.0
            if in_lex:
                score += 1.0 / (RRF_K + lexical_ranks[cid])
            if cid in dense_ranks:
                score += 1.0 / (RRF_K + dense_ranks[cid])
            rrf_candidates.append((score, cid))

        if not rrf_candidates:
            return KnowledgeSearchResult(
                status=KnowledgeStatus.UNAVAILABLE,
                abstain_required=True,
                citations=[],
                query_normalized=norm_query,
            )

        rrf_candidates.sort(key=lambda pair: (pair[0], cosine_by_chunk.get(pair[1], 0.0)), reverse=True)
        citations: list[Citation] = []
        for score, cid in rrf_candidates[:top_k]:
            row = allowed_chunks[cid]
            citations.append(
                Citation(
                    doc_id=str(row["doc_id"]),
                    chunk_id=cid,
                    title=str(row["title"]),
                    quote=str(row["content"]),
                    rrf_score=score,
                    polarity=str(row["polarity"]),
                )
            )

        top_polarity = citations[0].polarity
        status = (
            KnowledgeStatus.CONFIRMED_NEGATIVE
            if top_polarity == "negative"
            else KnowledgeStatus.SUPPORTED
        )
        return KnowledgeSearchResult(
            status=status,
            abstain_required=False,
            citations=citations,
            query_normalized=norm_query,
        )
