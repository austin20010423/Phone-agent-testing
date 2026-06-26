from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = ROOT / "scenarios.yaml"


def load_scenario(key: str) -> dict[str, Any]:
    data = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", {})
    if key not in scenarios:
        available = ", ".join(sorted(scenarios))
        raise ScenarioError(f"Unknown scenario '{key}'. Available: {available}")
    return scenarios[key]


class ScenarioError(RuntimeError):
    pass
