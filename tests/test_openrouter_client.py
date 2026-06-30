from __future__ import annotations

import unittest

from pgaibot.openrouter_client import SAFE_FALLBACK_UTTERANCE, parse_patient_reply


class ParsePatientReplyTest(unittest.TestCase):
    def test_valid_json_response_returns_patient_reply(self) -> None:
        reply = parse_patient_reply(
            '{"reply": "I need to reschedule my appointment.", "end_call": true}'
        )

        self.assertEqual(reply.reply, "I need to reschedule my appointment.")
        self.assertTrue(reply.end_call)

    def test_invalid_json_response_uses_safe_fallback(self) -> None:
        malformed_content = '{"reply": "I need to reschedule my appointment.", "end_call": false'

        reply = parse_patient_reply(malformed_content)

        self.assertEqual(reply.reply, SAFE_FALLBACK_UTTERANCE)
        self.assertFalse(reply.end_call)
        self.assertNotEqual(reply.reply, malformed_content)


if __name__ == "__main__":
    unittest.main()
