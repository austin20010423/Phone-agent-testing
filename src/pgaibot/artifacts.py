from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RECORDINGS_DIR = ROOT / "recordings"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"


def ensure_artifact_dirs() -> None:
    RECORDINGS_DIR.mkdir(exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    RUNS_DIR.mkdir(exist_ok=True)


def build_artifact_id(scenario_key: str) -> str:
    slug = safe_name(scenario_key)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{slug}_{stamp}"


def save_run(artifact_id: str, payload: dict[str, Any]) -> None:
    ensure_artifact_dirs()
    path = RUNS_DIR / f"{safe_name(artifact_id)}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_run(identifier: str) -> dict[str, Any]:
    path = RUNS_DIR / f"{safe_name(identifier)}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    for candidate in RUNS_DIR.glob("*.json"):
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if payload.get("call_sid") == identifier or payload.get("artifact_id") == identifier:
            return payload

    raise FileNotFoundError(f"No run file found for {identifier}: {path}")


def save_transcript(artifact_id: str, events: list[dict[str, Any]]) -> None:
    ensure_artifact_dirs()
    lines = []
    for event in events:
        speaker = event.get("speaker", "unknown")
        text = event.get("text", "")
        timestamp = event.get("timestamp", "")
        lines.append(f"[{timestamp}] {speaker}: {text}")
    path = TRANSCRIPTS_DIR / f"{safe_name(artifact_id)}.txt"
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)
