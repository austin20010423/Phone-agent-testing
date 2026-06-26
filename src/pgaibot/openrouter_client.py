from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class PatientReply:
    reply: str
    end_call: bool = False


class OpenRouterClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def next_patient_reply(
        self,
        scenario: dict[str, Any],
        events: list[dict[str, Any]],
        patient_turns: int,
    ) -> PatientReply:
        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is required for conversation calls")

        messages = [
            {"role": "system", "content": build_system_prompt(scenario, patient_turns)},
            *build_conversation_messages(events),
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 180,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Pretty Good AI Challenge Bot",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:
            raise OpenRouterError(f"OpenRouter request failed: {response.status_code} {response.text}")

        content = response.json()["choices"][0]["message"]["content"]
        return parse_patient_reply(content)


def build_system_prompt(scenario: dict[str, Any], patient_turns: int) -> str:
    details = "\n".join(f"- {item}" for item in scenario.get("details", []))
    return f"""
You are simulating a realistic patient on a phone call with a medical office AI agent.

Scenario name: {scenario.get("name", "unknown")}
Patient name: {scenario.get("patient_name", "Patient")}
Goal: {scenario.get("goal", "")}
Details:
{details}

Rules:
- Stay in character as the patient.
- Answer directly. Do not start with hello, hi, or other greeting words.
- Speak naturally and briefly, usually 1-2 sentences.
- Do not mention testing, prompts, OpenRouter, Twilio, or that you are an AI.
- Keep the conversation multi-turn. Do not end too early.
- Let the agent finish speaking before replying. Do not interrupt, talk over them, or answer in the middle of their sentence.
- Ask follow-up questions or provide missing details when needed.
- Steer toward the scenario goal.
- Only set end_call to true when the goal is handled or blocked and there have been at least 4 patient turns.

Patient turns so far: {patient_turns}

Return only JSON in this exact shape:
{{"reply": "patient words to say aloud", "end_call": false}}
""".strip()


def build_conversation_messages(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for event in events:
        speaker = event.get("speaker")
        text = event.get("text", "")
        if not text:
            continue
        if speaker == "Patient":
            messages.append({"role": "assistant", "content": text})
        elif speaker == "Agent":
            messages.append({"role": "user", "content": text})
    return messages


def parse_patient_reply(content: str) -> PatientReply:
    try:
        payload = json.loads(content)
        reply = str(payload.get("reply", "")).strip()
        end_call = bool(payload.get("end_call", False))
    except json.JSONDecodeError:
        reply = content.strip()
        end_call = False

    if not reply:
        reply = "Could you help me with that?"
    return PatientReply(reply=reply, end_call=end_call)


class OpenRouterError(RuntimeError):
    pass
