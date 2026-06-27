# Pretty Good AI Voice Bot

Python voice bot for the Pretty Good AI engineering challenge.

The bot places outbound calls to the challenge test number, runs a scenario-driven patient conversation, records the call, stores transcripts locally, and downloads the completed audio recording after hangup.

## Quick Start

After setup, the normal run path is:

```bash
uv run pgaibot call --scenario scheduling_basic
```

That command starts the outbound call using the scenario you choose. The webhook server and tunnel still need to be running in separate terminals for a real conversation.

## What It Uses

- Twilio Programmable Voice for outbound calls, speech gathering, and call recording
- OpenRouter chat completions for patient responses
- FastAPI for the webhook server
- Cloudflare Quick Tunnel or another public HTTPS tunnel for Twilio webhooks

## Current Design

The call flow is intentionally simple:

1. Twilio calls the challenge number.
2. Twilio requests `/voice/start` from this app.
3. The app listens first, then starts the conversation with `<Gather input="speech">`.
4. Twilio sends speech results to `/voice/respond`.
5. The app sends the recognized speech to OpenRouter.
6. OpenRouter returns the next patient reply.
7. The loop continues until the scenario is complete.
8. After hangup, Twilio sends the recording callback and the app downloads the `.mp3` into `recordings/`.

## Requirements

- Python 3.11+
- `uv`
- A Twilio account with one phone number
- An OpenRouter API key
- A public HTTPS tunnel for Twilio webhooks

## Environment Variables

Create a `.env` file from `.env.example` and fill in:

```bash
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
PG_TEST_NUMBER=+18054398008
PUBLIC_BASE_URL=https://your-public-url
```

`PUBLIC_BASE_URL` must point to your public tunnel URL when running a real scenario call.

## Setup

Install dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

## Twilio Setup

1. Create or sign in to your Twilio account.
2. Buy one Twilio phone number with voice capability.
3. Copy your Account SID and Auth Token into `.env`.
4. Set `TWILIO_FROM_NUMBER` to that Twilio number in E.164 format.
5. Keep using the same Twilio number for all challenge calls.
6. If your account is in trial mode, upgrade it if Twilio blocks calls to the challenge test number.

## Public Webhook URL

Twilio cannot reach `localhost`, so the webhook server must be exposed publicly.

One free option is Cloudflare Quick Tunnels:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the generated `https://...trycloudflare.com` URL into `PUBLIC_BASE_URL`.

Keep the tunnel running while calls are active.

## Running the Server

Start the webhook server:

```bash
uv run uvicorn pgaibot.server:app --host 0.0.0.0 --port 8000 --reload
```

## Running a Scenario Call

Dry run:

```bash
uv run pgaibot call --scenario scheduling_basic --dry-run
```

Real call:

```bash
uv run pgaibot call --scenario scheduling_basic
```

Available scenarios live in `scenarios.yaml`, for example:

- `scheduling_basic`
- `reschedule_appointment`
- `cancel_appointment`
- `refill_request`
- `office_hours`
- `location_info`
- `insurance_question`
- `callback_followup`
- `unclear_request`
- `unusual_edge_case`

## Artifacts

Each call writes local artifacts as it progresses:

```text
runs/<scenario>_<timestamp>.json
transcripts/<scenario>_<timestamp>.txt
recordings/<scenario>_<timestamp>.mp3
```

The transcript contains both the patient bot and the agent speech turns. The recording is downloaded automatically after Twilio sends the completed recording callback.

## Logging

The server prints each turn to the terminal while the call runs, so you can watch the conversation live.

## Project Commands

```bash
uv run pgaibot call --scenario scheduling_basic --dry-run
uv run pgaibot call --scenario scheduling_basic
uv run pgaibot download-recording <scenario>_<timestamp>
```

## Notes

- The bot is designed to avoid over-engineering.
- The patient listens first, then answers.
- The patient does not greet the agent with a generic hello; it begins with the actual request or response.
- The implementation is focused on producing the required 10 recorded conversations and supporting artifacts.
