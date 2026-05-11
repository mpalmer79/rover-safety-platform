"""Static metadata about local models.

The registry stores the operator's declared capability metadata for
every local model the team has qualified. No metadata is ever
inferred from a model's runtime output; the operator records what
each model is allowed to do. The validator + ranker still dominate
every safety decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ModelCapability:
    model_name: str
    provider: str  # ProviderMode value
    family: str
    parameters_billion: float
    context_tokens: int
    quantization: str = ""
    declared_strengths: tuple[str, ...] = ()
    declared_weaknesses: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    qualified: bool = False
    """``True`` only after a reviewer has signed the local
    qualification checklist (`docs/LOCAL_LLM_MODEL_QUALIFICATION.md`
    when shipped)."""


_DEFAULT_REGISTRY: tuple[ModelCapability, ...] = (
    ModelCapability(
        model_name="llama-3.1-8b-instruct.q4",
        provider="llama_cpp",
        family="llama-3",
        parameters_billion=8.0,
        context_tokens=8192,
        quantization="q4_K_M",
        declared_strengths=(
            "instruction following",
            "structured JSON envelopes",
        ),
        declared_weaknesses=(
            "overconfident on ROS-specific syntax",
            "hallucinates topic names that look plausible",
        ),
        notes=("local-only; download manually; never auto-downloaded by the platform",),
        qualified=False,
    ),
    ModelCapability(
        model_name="qwen2.5-7b-instruct.q4",
        provider="llama_cpp",
        family="qwen-2.5",
        parameters_billion=7.0,
        context_tokens=8192,
        quantization="q4_K_M",
        declared_strengths=(
            "compact instruction following",
            "low memory footprint",
        ),
        declared_weaknesses=(
            "verbose explanations",
            "tends to wrap output in markdown fences",
        ),
        qualified=False,
    ),
    ModelCapability(
        model_name="phi-3.5-mini-instruct.q4",
        provider="ollama",
        family="phi-3.5",
        parameters_billion=3.8,
        context_tokens=4096,
        quantization="q4_0",
        declared_strengths=(
            "very small; runs on laptop",
        ),
        declared_weaknesses=(
            "occasional formatting drift",
            "limited reasoning depth",
        ),
        qualified=False,
    ),
    ModelCapability(
        model_name="canonical-fixture",
        provider="fixture",
        family="fixture",
        parameters_billion=0.0,
        context_tokens=0,
        quantization="",
        declared_strengths=("deterministic; canonical fixture",),
        declared_weaknesses=("returns committed responses only",),
        qualified=True,
        notes=("used by the test-suite + the workbench library",),
    ),
)


def default_capability_registry() -> tuple[ModelCapability, ...]:
    return _DEFAULT_REGISTRY


def find_capability(
    model_name: str,
    registry: tuple[ModelCapability, ...] | None = None,
) -> ModelCapability | None:
    if registry is None:
        registry = _DEFAULT_REGISTRY
    for entry in registry:
        if entry.model_name == model_name:
            return entry
    return None


def capability_to_dict(entry: ModelCapability) -> dict[str, object]:
    return {
        "model_name": entry.model_name,
        "provider": entry.provider,
        "family": entry.family,
        "parameters_billion": entry.parameters_billion,
        "context_tokens": entry.context_tokens,
        "quantization": entry.quantization,
        "declared_strengths": list(entry.declared_strengths),
        "declared_weaknesses": list(entry.declared_weaknesses),
        "notes": list(entry.notes),
        "qualified": entry.qualified,
    }


__all__ = [
    "ModelCapability",
    "capability_to_dict",
    "default_capability_registry",
    "find_capability",
]
