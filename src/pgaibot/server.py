from __future__ import annotations

from datetime import UTC, datetime
from html import escape
import sys
import traceback
from urllib.parse import parse_qs, urlencode
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response

from pgaibot.artifacts import build_artifact_id, load_run, save_run, save_transcript
from pgaibot.config import ConfigError, load_settings
from pgaibot.openrouter_client import OpenRouterClient, OpenRouterError
from pgaibot.recordings import RecordingError, download_recording_url_async
from pgaibot.scenarios import ScenarioError, load_scenario


app = FastAPI(title="Pretty Good AI Voice Bot")
SESSIONS: dict[str, dict[str, Any]] = {}
MIN_PATIENT_TURNS = 4
MAX_PATIENT_TURNS = 15


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/voice/start")
async def voice_start(request: Request, scenario: str) -> Response:
    form = await parse_twilio_form(request)
    call_sid = form.get("CallSid", f"local-{timestamp_slug()}")

    try:
        scenario_data = load_scenario(scenario)
    except ScenarioError as exc:
        return twiml_response(say_and_hangup(str(exc)))

    artifact_id = build_artifact_id(scenario)
    session = {
        "artifact_id": artifact_id,
        "call_sid": call_sid,
        "scenario_key": scenario,
        "scenario": scenario_data,
        "events": [],
        "recording": {},
        "started_at": now_iso(),
        "updated_at": now_iso(),
    }
    SESSIONS[call_sid] = session
    persist_session(session)

    return twiml_response(listen_twiml(action_url("/voice/respond", call_sid, scenario)))


@app.post("/voice/respond")
async def voice_respond(request: Request, call_sid: str, scenario: str) -> Response:
    form = await parse_twilio_form(request)
    call_sid = form.get("CallSid", call_sid)
    session = get_or_create_session(call_sid, scenario)

    agent_text = form.get("SpeechResult", "").strip()
    if not agent_text:
        prompt = "Sorry, I did not catch that. Could you say that again?"
        append_event(session, "Patient", prompt)
        persist_session(session)
        return twiml_response(gather_twiml(prompt, action_url("/voice/respond", call_sid, scenario)))

    append_event(session, "Agent", agent_text)

    try:
        settings = load_settings()
        client = OpenRouterClient(settings.openrouter_api_key, settings.openrouter_model)
        patient_turns = count_speaker_turns(session, "Patient")
        patient_reply = await client.next_patient_reply(
            session["scenario"],
            session["events"],
            patient_turns,
        )
    except (ConfigError, OpenRouterError) as exc:
        fallback = "Thanks, I will call back later. Goodbye."
        append_event(session, "Patient", fallback, meta={"error": str(exc)})
        persist_session(session)
        return twiml_response(say_and_hangup(fallback))
    except Exception as exc:
        traceback.print_exc()
        fallback = "Sorry, I had trouble hearing that. I will call back later. Goodbye."
        append_event(session, "Patient", fallback, meta={"error": f"{type(exc).__name__}: {exc}"})
        persist_session(session)
        return twiml_response(say_and_hangup(fallback))

    patient_turns = count_speaker_turns(session, "Patient")
    end_call = patient_reply.end_call and patient_turns >= MIN_PATIENT_TURNS
    if patient_turns >= MAX_PATIENT_TURNS and not end_call:
        end_call = True

    append_event(session, "Patient", patient_reply.reply, meta={"end_call": end_call})
    persist_session(session)

    if end_call:
        return twiml_response(say_and_hangup(patient_reply.reply))
    return twiml_response(gather_twiml(patient_reply.reply, action_url("/voice/respond", call_sid, scenario)))


@app.post("/voice/recording")
async def voice_recording(request: Request, scenario: str) -> dict[str, str]:
    form = await parse_twilio_form(request)
    call_sid = form.get("CallSid", "")
    if call_sid:
        session = get_or_create_session(call_sid, scenario)
        recording_url = form.get("RecordingUrl", "")
        recording_status = form.get("RecordingStatus", "")
        session["recording"] = {
            "recording_sid": form.get("RecordingSid", ""),
            "recording_status": recording_status,
            "recording_duration": form.get("RecordingDuration", ""),
            "updated_at": now_iso(),
        }
        persist_session(session)

        if recording_url and recording_status in ("completed", ""):
            try:
                settings = load_settings()
                path = await download_recording_url_async(settings, session["artifact_id"], recording_url)
                session["recording"]["local_path"] = str(path)
                session["recording"]["downloaded_at"] = now_iso()
                persist_session(session)
                return {"status": "ok", "recording": "downloaded", "path": str(path)}
            except (ConfigError, RecordingError, Exception) as exc:
                traceback.print_exc()
                session["recording"]["download_error"] = str(exc)
                session["recording"]["download_error_at"] = now_iso()
                persist_session(session)
                return {"status": "ok", "recording": "download_failed"}

    return {"status": "ok"}


def get_or_create_session(call_sid: str, scenario_key: str) -> dict[str, Any]:
    if call_sid in SESSIONS:
        return SESSIONS[call_sid]
    try:
        session = load_run(call_sid)
        if "scenario" not in session:
            session["scenario"] = load_scenario(session.get("scenario_key", scenario_key))
    except FileNotFoundError:
        scenario = load_scenario(scenario_key)
        session = {
            "artifact_id": build_artifact_id(scenario_key),
            "call_sid": call_sid,
            "scenario_key": scenario_key,
            "scenario": scenario,
            "events": [],
            "recording": {},
            "started_at": now_iso(),
            "updated_at": now_iso(),
        }
    SESSIONS[call_sid] = session
    return session


def append_event(
    session: dict[str, Any],
    speaker: str,
    text: str,
    meta: dict[str, Any] | None = None,
) -> None:
    event = {
        "timestamp": now_iso(),
        "speaker": speaker,
        "text": text,
    }
    if meta:
        event["meta"] = meta
    session["events"].append(event)
    session["updated_at"] = now_iso()
    log_event(event)


def persist_session(session: dict[str, Any]) -> None:
    save_run(session["artifact_id"], session)
    save_transcript(session["artifact_id"], session["events"])


def count_speaker_turns(session: dict[str, Any], speaker: str) -> int:
    return sum(1 for event in session["events"] if event.get("speaker") == speaker)


async def parse_twilio_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body)
    return {key: values[-1] for key, values in parsed.items() if values}


def gather_twiml(message: str, action: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{escape(action)}" method="POST" speechTimeout="auto" timeout="8">
    <Say>{escape(message)}</Say>
  </Gather>
  <Redirect method="POST">{escape(action)}</Redirect>
</Response>"""


def listen_twiml(action: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{escape(action)}" method="POST" speechTimeout="auto" timeout="15"></Gather>
  <Redirect method="POST">{escape(action)}</Redirect>
</Response>"""


def say_and_hangup(message: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>{escape(message)}</Say>
  <Hangup/>
</Response>"""


def twiml_response(twiml: str) -> Response:
    return Response(content=twiml, media_type="application/xml")


def action_url(path: str, call_sid: str, scenario: str) -> str:
    query = urlencode({"call_sid": call_sid, "scenario": scenario})
    try:
        settings = load_settings()
    except ConfigError:
        return f"{path}?{query}"
    if not settings.public_base_url:
        return f"{path}?{query}"
    return f"{settings.public_base_url}{path}?{query}"


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def log_event(event: dict[str, Any]) -> None:
    timestamp = event.get("timestamp", "")
    speaker = event.get("speaker", "unknown")
    text = event.get("text", "")
    print(f"[{timestamp}] {speaker}: {text}", file=sys.stdout, flush=True)
