# Wispral 000E KT-01 research harness: a deterministic, recording fake NLPService for
# Parlant v3.3.2 (emcie-co/parlant@61bba3b2b3fffd677d345e393e8c942dbd400297). Not product code.
from __future__ import annotations

import enum
import hashlib
import time
import typing
from typing import Any, Mapping, Sequence

from pydantic import BaseModel

from parlant.core.nlp.embedding import Embedder, EmbeddingResult
from parlant.core.nlp.generation import SchematicGenerationResult, SchematicGenerator
from parlant.core.nlp.generation_info import GenerationInfo, UsageInfo
from parlant.core.nlp.moderation import ModerationService, NoModeration
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.tokenization import EstimatingTokenizer

CALLS: list[dict[str, Any]] = []
SCRIPT: dict[str, Any] = {"text": "FAKE_REPLY"}


class _ZeroTokenizer(EstimatingTokenizer):
    async def estimate_token_count(self, prompt: str) -> int:
        return 0


def _usage() -> UsageInfo:
    return UsageInfo(input_tokens=0, output_tokens=0)


def _minimal(tp: Any, depth: int = 0) -> Any:
    origin, args = typing.get_origin(tp), typing.get_args(tp)
    if tp is type(None):
        return None
    if origin is typing.Union or str(origin) == "types.UnionType":
        return None if type(None) in args else _minimal(args[0], depth)
    if origin is typing.Literal:
        return args[0]
    if origin in (list, Sequence, typing.Sequence, set, frozenset, tuple):
        if args and args[0] is str:
            return [f"fake-item-{i}" for i in range(10)]
        return [] if origin is not tuple else ()
    if origin in (dict, Mapping, typing.Mapping):
        return {}
    if isinstance(tp, type):
        if issubclass(tp, bool):
            return False
        if issubclass(tp, enum.Enum):
            return next(iter(tp))
        if issubclass(tp, int):
            return 0
        if issubclass(tp, float):
            return 0.0
        if issubclass(tp, str):
            return SCRIPT["text"]
        if issubclass(tp, BaseModel) and depth < 8:
            return _instance(tp, depth + 1)
    return None


def _instance(model: type[BaseModel], depth: int = 0) -> BaseModel:
    return model.model_validate({n: _minimal(f.annotation, depth) for n, f in model.model_fields.items() if f.is_required()})


class FakeSchematicGenerator(SchematicGenerator[Any]):
    def __init__(self, schema: type[Any]) -> None:
        self._schema = schema

    @property
    def schema(self) -> type[Any]:  # type: ignore[override]
        return self._schema

    async def generate(self, prompt: Any, hints: Mapping[str, Any] = {}) -> SchematicGenerationResult[Any]:
        CALLS.append({"t": time.perf_counter(), "capability": "schematic", "detail": self._schema.__name__})
        info = GenerationInfo(schema_name=self._schema.__name__, model="fake", duration=0.0, usage=_usage())
        return SchematicGenerationResult(content=_instance(self._schema), info=info)

    @property
    def id(self) -> str:
        return "fake/schematic"

    @property
    def max_tokens(self) -> int:
        return 1_000_000

    @property
    def tokenizer(self) -> EstimatingTokenizer:
        return _ZeroTokenizer()


class FakeEmbedder(Embedder):
    DIM = 64

    async def embed(self, texts: list[str], hints: Mapping[str, Any] = {}) -> EmbeddingResult:
        CALLS.append({"t": time.perf_counter(), "capability": "embedding", "detail": str(len(texts))})
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            vecs.append([((h[i % 32] / 255.0) * 2 - 1) for i in range(self.DIM)])
        return EmbeddingResult(vectors=vecs)

    @property
    def id(self) -> str:
        return "fake/embedding"

    @property
    def max_tokens(self) -> int:
        return 1_000_000

    @property
    def tokenizer(self) -> EstimatingTokenizer:
        return _ZeroTokenizer()

    @property
    def dimensions(self) -> int:
        return self.DIM


class FakeNLPService(NLPService):
    @property
    def supports_streaming(self) -> bool:
        return False

    _classes: dict[type, type] = {}

    async def get_schematic_generator(self, t: type[Any], hints: Any = {}) -> SchematicGenerator[Any]:
        # Parlant v3 registers each generator in its container by concrete class, so every
        # schema needs a distinct class (real providers use a generic class per schema).
        cls = self._classes.setdefault(t, type(f"FakeSchematic_{t.__name__}", (FakeSchematicGenerator,), {}))
        return cls(t)

    async def get_streaming_text_generator(self, hints: Any = {}) -> Any:
        raise NotImplementedError("fake provider does not stream")

    async def get_embedder(self, hints: Any = {}) -> Embedder:
        return FakeEmbedder()

    async def get_moderation_service(self) -> ModerationService:
        return NoModeration()


def factory(container: Any) -> NLPService:
    return FakeNLPService()
