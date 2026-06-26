from __future__ import annotations

from pathlib import Path

import httpx

from pgaibot.artifacts import RECORDINGS_DIR, ensure_artifact_dirs, load_run, safe_name
from pgaibot.config import Settings


def download_recording(settings: Settings, identifier: str) -> Path:
    run = load_run(identifier)
    recording = run.get("recording", {})
    recording_url = recording.get("recording_url", "")
    if not recording_url:
        raise RecordingError(
            f"No recording URL found for {identifier}. Wait for Twilio's recording callback or check the Twilio Console."
        )

    artifact_id = str(run.get("artifact_id") or identifier)
    return download_recording_url(settings, artifact_id, recording_url)


async def download_recording_url_async(
    settings: Settings,
    artifact_id: str,
    recording_url: str,
) -> Path:
    url = recording_url if recording_url.endswith(".mp3") else f"{recording_url}.mp3"
    ensure_artifact_dirs()
    output_path = RECORDINGS_DIR / f"{safe_name(artifact_id)}.mp3"

    async with httpx.AsyncClient(
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        follow_redirects=True,
        timeout=60,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    output_path.write_bytes(response.content)
    return output_path


def download_recording_url(settings: Settings, artifact_id: str, recording_url: str) -> Path:
    url = recording_url if recording_url.endswith(".mp3") else f"{recording_url}.mp3"
    ensure_artifact_dirs()
    output_path = RECORDINGS_DIR / f"{safe_name(artifact_id)}.mp3"

    with httpx.Client(
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        follow_redirects=True,
        timeout=60,
    ) as client:
        response = client.get(url)
        response.raise_for_status()

    output_path.write_bytes(response.content)
    return output_path


class RecordingError(RuntimeError):
    pass
