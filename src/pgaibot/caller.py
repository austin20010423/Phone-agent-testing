from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from pgaibot.config import DEFAULT_TEST_NUMBER, Settings


@dataclass(frozen=True)
class CallRequest:
    scenario: str
    to_number: str = DEFAULT_TEST_NUMBER
    dry_run: bool = False


@dataclass(frozen=True)
class CallResult:
    sid: str
    from_number: str
    to_number: str
    call_instructions: str
    status: str
    dry_run: bool


def start_call(settings: Settings, request: CallRequest) -> CallResult:
    assert_allowed_destination(settings, request.to_number)
    webhook_url = build_webhook_url(settings.public_base_url, request.scenario)
    call_instructions = webhook_url or "inline TwiML"

    if request.dry_run:
        return CallResult(
            sid="dry-run",
            from_number=settings.twilio_from_number,
            to_number=request.to_number,
            call_instructions=call_instructions,
            status="not-created",
            dry_run=True,
        )

    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call_kwargs = {
        "from_": settings.twilio_from_number,
        "to": request.to_number,
        "record": True,
        "recording_channels": "dual",
    }

    if webhook_url:
        call_kwargs["url"] = webhook_url
        call_kwargs["method"] = "POST"
        call_kwargs["recording_status_callback"] = build_recording_callback_url(
            settings.public_base_url,
            request.scenario,
        )
        call_kwargs["recording_status_callback_method"] = "POST"
        call_kwargs["recording_status_callback_event"] = ["completed"]
    else:
        call_kwargs["twiml"] = build_inline_twiml(request.scenario)

    call = client.calls.create(**call_kwargs)

    return CallResult(
        sid=call.sid,
        from_number=settings.twilio_from_number,
        to_number=request.to_number,
        call_instructions=call_instructions,
        status=call.status,
        dry_run=False,
    )


def assert_allowed_destination(settings: Settings, to_number: str) -> None:
    if normalize_number(to_number) != normalize_number(settings.pg_test_number):
        raise UnsafeDestinationError(
            f"Refusing to call {to_number}. This app may only call {settings.pg_test_number}."
        )


def build_webhook_url(public_base_url: str, scenario: str) -> str:
    if not public_base_url:
        return ""
    query = urlencode({"scenario": scenario})
    return f"{public_base_url}/voice/start?{query}"


def build_recording_callback_url(public_base_url: str, scenario: str) -> str:
    query = urlencode({"scenario": scenario})
    return f"{public_base_url}/voice/recording?{query}"


def build_inline_twiml(scenario: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Caller smoke test for scenario {scenario}. This confirms Twilio can place the call.</Say>
  <Hangup/>
</Response>"""


def normalize_number(number: str) -> str:
    return number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


class UnsafeDestinationError(RuntimeError):
    pass
