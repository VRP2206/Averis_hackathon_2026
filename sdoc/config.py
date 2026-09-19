"""Runtime settings, read from environment variables or a `.env` file.

Every setting has a working default so `sdoc run` works offline with no
API key: the pipeline then uses rules + heuristic extraction only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SDOC_", env_file=".env", extra="ignore")

    # Data
    data_dir: Path = REPO_ROOT / "Provided Information" / "Participant Info"
    ground_truth: Path = REPO_ROOT / "Provided Information" / "Other" / "data_v2" / "ground_truth.json"
    output_dir: Path = REPO_ROOT / "output"

    # LLM. "none" = rules + heuristics only (free, offline).
    llm_provider: Literal["none", "anthropic", "bedrock"] = "none"
    llm_cache_dir: Path = REPO_ROOT / ".cache" / "llm"
    # Cheap model for classification fallback / doc-type checks / extraction.
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    # Stronger model, only used to retry low-confidence extractions.
    llm_strong_model: str = "claude-sonnet-5"
    bedrock_region: str = "us-east-1"
    # Bedrock model ids differ from the Anthropic API ids.
    bedrock_fast_model: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_strong_model: str = "us.anthropic.claude-sonnet-5-v1:0"

    # Behaviour
    use_llm_for_extraction: bool = True   # only matters when llm_provider != none
    extraction_min_confidence: float = 0.6


settings = Settings()
