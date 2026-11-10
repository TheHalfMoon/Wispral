# Wispral 000E KT-01 research harness: a deterministic, recording fake model provider for
# Parlant v4 (emcie-co/parlant@2a463ccd10eaf0d70d42731705f4f00ef066bee8). Not product code.
#
# The ReAct part adapts `_FakeReactGenerator` from Parlant's tests/core/nlp/test_react.py
# (Copyright 2026 Emcie Co Ltd., Apache License 2.0). Everything else is new.
#
# Every model call is appended to CALLS, so a test can count calls per turn by capability.
from __future__ import annotations

import enum
import hashlib
import os
import time
import typing
import uuid
from typing import Any, AsyncIterator, Mapping, Sequence, cast

from pydantic import BaseModel

from parlant.core.nlp.decision import (
    ChoiceAnswer, Choice, DecisionMaker, DecisionResult, PropositionAnswer, Proposition, Question,
    ScaleAnswer, Scale,
)
from parlant.core.nlp.embedding import Embedder, EmbeddingResult
from parlant.core.nlp.generation import SchematicGenerationResult, SchematicGenerator
from parlant.core.nlp.generation_info import GenerationInfo, UsageInfo
from parlant.core.nlp.model_routing import ModelCapability, ModelImplementationRegistry
from parlant.core.nlp.moderation import NoModeration
from parlant.core.nlp.react import (
    Message, ReactGenerator, Role, StreamEvent, TextDelta, ToolCallStarted, ToolResultPart,
    ToolSpec, TurnBuilder, Usage,
)
from parlant.core.nlp.tokenization import EstimatingTokenizer, ZeroEstimatingTokenizer

PROVIDER = "fake"
CALLS: list[dict[str, Any]] = []
# Script for the ReAct loop: call this tool once (if offered) with these args, then reply.
SCRIPT: dict[str, Any] = {"tool": None, "args": {}, "reply": "FAKE_REPLY", "propositions": 0.0}


def _record(capability: str, detail: str) -> None:
    CALLS.append({"t": time.perf_counter(), "capability": capability, "detail": detail})


def _usage() -> UsageInfo:
    return UsageInfo(input_tokens=0, output_tokens=0, requests=1)


# ---------------------------------------------------------------- schematic (structured output)
def _minimal(tp: Any, depth: int = 0) -> Any:
    """A deterministic minimal valid value for a type annotation."""
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if tp is type(None):
        return None
    if origin is typing.Union or str(origin) == "types.UnionType":
        return None if type(None) in args else _minimal(args[0], depth)
    if origin is typing.Literal:
        return args[0]
    if origin in (list, Sequence, typing.Sequence, set, frozenset, tuple):
        if args and args[0] is str:
            # Deterministic distinct strings: some Parlant pipelines require a fixed count (e.g. 10 rule signals).
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
            # Non-empty: Parlant's indexing rejects empty generated text (e.g. rule titles).
            return "fake-text"
        if issubclass(tp, BaseModel) and depth < 8:
            return _instance(tp, depth + 1)
    return None


def _instance(model: type[BaseModel], depth: int = 0) -> BaseModel:
    values: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        values[name] = _minimal(field.annotation, depth)
    return model.model_validate(values)


class FakeSchematicGenerator(SchematicGenerator[Any]):
    def __init__(self, model: str, schema: type[Any]) -> None:
        self._model = model
        self._schema = schema

    @property
    def schema(self) -> type[Any]:  # type: ignore[override]
        return self._schema

    async def generate(self, prompt: Any, hints: Mapping[str, Any] = {}) -> SchematicGenerationResult[Any]:
        _record("schematic", getattr(self._schema, "__name__", str(self._schema)))
        content = _instance(self._schema)
        info = GenerationInfo(schema_name=self._schema.__name__, model=self._model, duration=0.0, usage=_usage())
        return SchematicGenerationResult(content=content, info=info)

    @property
    def id(self) -> str:
        return f"{PROVIDER}/{self._model}"

    @property
    def max_tokens(self) -> int:
        return 1_000_000

    @property
    def tokenizer(self) -> EstimatingTokenizer:
        return ZeroEstimatingTokenizer()


# ---------------------------------------------------------------- decisions
class FakeDecisionMaker(DecisionMaker):
    def __init__(self, model: str) -> None:
        self._model = model

    async def decide(self, state: Any, questions: Mapping[str, Question], hints: Mapping[str, Any] = {}) -> DecisionResult:
        _record("decision", ",".join(sorted(questions)))
        answers: dict[str, Any] = {}
        for name, q in questions.items():
            if isinstance(q, Proposition):
                answers[name] = PropositionAnswer(probability=float(SCRIPT.get("propositions", 0.0)))
            elif isinstance(q, Choice):
                first = next(iter(q.criteria))
                answers[name] = ChoiceAnswer(option=first, probabilities={first: 1.0}, confidence=1.0)
            elif isinstance(q, Scale):
                mid = len(q.criteria) // 2
                answers[name] = ScaleAnswer(score=float(mid), legend={i: str(c) for i, c in enumerate(q.criteria)})
        info = GenerationInfo(schema_name="decision", model=self._model, duration=0.0, usage=_usage())
        return DecisionResult(answers=answers, info=info)

    @property
    def id(self) -> str:
        return f"{PROVIDER}/{self._model}"

    @property
    def max_tokens(self) -> int:
        return 1_000_000


# ---------------------------------------------------------------- ReAct (adapted from Parlant's test fake)
class FakeReactGenerator(ReactGenerator):
    def __init__(self, model: str) -> None:
        super().__init__(model=model)

    @property
    def provider_name(self) -> str:
        return PROVIDER

    def _encode(self, history: Sequence[Message], tools: Sequence[ToolSpec], tool_choice: Any, *, reasoning: Any = None, hints: Any = None) -> Any:
        return {"history": list(history), "tools": [t.name for t in tools]}

    async def _raw_stream(self, request: Any) -> AsyncIterator[Any]:
        _record("react", "tools=" + ",".join(request["tools"]))
        called = any(isinstance(p, ToolResultPart) for m in request["history"] for p in m.parts)
        tool = SCRIPT.get("tool")
        if tool and tool in request["tools"] and not called:
            yield ("tool", tool, dict(SCRIPT.get("args") or {}))
        else:
            yield ("text", str(SCRIPT.get("reply", "FAKE_REPLY")))

    def _decode(self, raw_event: Any, builder: TurnBuilder) -> Sequence[StreamEvent]:
        builder.usage = Usage(input_tokens=0, output_tokens=0, model_name=self.model)
        if raw_event[0] == "tool":
            call_id = uuid.uuid4().hex
            builder.tool_call(call_id, name=raw_event[1], args=raw_event[2])
            return [ToolCallStarted(id=call_id, name=raw_event[1])]
        builder.text_delta(raw_event[1])
        return [TextDelta(text=raw_event[1])]


# ---------------------------------------------------------------- embeddings
class FakeEmbedder(Embedder):
    DIM = 64

    def __init__(self, model: str) -> None:
        self._model = model

    async def embed(self, texts: list[str], hints: Mapping[str, Any] = {}) -> EmbeddingResult:
        _record("embedding", str(len(texts)))
        vectors = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            vectors.append([((h[i % 32] / 255.0) * 2 - 1) for i in range(self.DIM)])
        return EmbeddingResult(vectors=vectors, usage=_usage())

    @property
    def id(self) -> str:
        return f"{PROVIDER}/{self._model}"

    @property
    def max_tokens(self) -> int:
        return 1_000_000

    @property
    def tokenizer(self) -> EstimatingTokenizer:
        return ZeroEstimatingTokenizer()

    @property
    def dimensions(self) -> int:
        return self.DIM


# ---------------------------------------------------------------- registration
def load_fake_models(registry: ModelImplementationRegistry) -> None:
    async def schematic(model: str, schema: type[Any], raw_args: Mapping[str, Any]) -> FakeSchematicGenerator:
        return FakeSchematicGenerator(model, schema)

    async def decision(model: str, raw_args: Mapping[str, Any]) -> FakeDecisionMaker:
        return FakeDecisionMaker(model)

    async def react(model: str, raw_args: Mapping[str, Any]) -> FakeReactGenerator:
        return FakeReactGenerator(model)

    async def embedding(model: str, raw_args: Mapping[str, Any]) -> FakeEmbedder:
        return FakeEmbedder(model)

    async def moderation(model: str, raw_args: Mapping[str, Any]) -> NoModeration:
        return NoModeration()

    async def tokenizer(model: str, raw_args: Mapping[str, Any]) -> EstimatingTokenizer:
        return ZeroEstimatingTokenizer()

    registry.register_schematic(PROVIDER, schematic, default="fake-schematic")
    registry.register(PROVIDER, ModelCapability.DECISION, decision, default="fake-decision")
    registry.register(PROVIDER, ModelCapability.REACT, react, default="fake-react")
    registry.register(PROVIDER, ModelCapability.EMBEDDING, embedding, default="fake-embedding")
    registry.register(PROVIDER, ModelCapability.MODERATION, moderation, default="fake-moderation")
    registry.register(PROVIDER, ModelCapability.TOKENIZER, tokenizer, default="fake-tokenizer")


def install() -> None:
    """Make every Parlant server in this process also know the `fake` provider."""
    import parlant.bin.server as server

    original = server.register_model_implementation_loaders

    def patched(registry: ModelImplementationRegistry, container: Any) -> None:
        original(registry, container)
        registry.register_provider_loader(PROVIDER, lambda: load_fake_models(registry))

    server.register_model_implementation_loaders = patched
