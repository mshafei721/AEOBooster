from __future__ import annotations

"""Utility functions for loading prompt templates and generating prompts."""

from pathlib import Path
import json
from typing import Iterable, List

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "templates.json"


def load_prompt_templates() -> List[str]:
    """Load prompt templates from the JSON template file."""
    with TEMPLATE_PATH.open() as f:
        return json.load(f)


def generate_prompts(entities: Iterable[str]) -> List[str]:
    """Generate prompts by injecting entity names into templates.

    Args:
        entities: An iterable of entity names.
    Returns:
        A list of prompts with each template formatted for every entity.
    """
    templates = load_prompt_templates()
    prompts: List[str] = []
    for template in templates:
        for entity in entities:
            prompts.append(template.format(entity=entity))
    return prompts
