# Bug Report

## Findings

### `scheduling_basic`
The agent misclassifies a new scheduling request as an existing appointment and ends the call before the request is resolved.

Evidence: [`transcripts/scheduling_basic_20260626_232310.txt`](./transcripts/scheduling_basic_20260626_232310.txt)

- The patient clearly asks to schedule a routine appointment for next week.
- The agent says the system already shows an appointment scheduled, which conflicts with the request.
- The agent switches into transfer/cancellation language instead of confirming a new slot.
- The call ends before a Tuesday or Thursday morning time is confirmed.

### `callback_followup_20260627_001037`
The callback flow is not handled cleanly. The agent gives a vague message about checking for messages, then later emits garbled follow-up text instead of answering who called and when the callback will happen.

Evidence: [`transcripts/callback_followup_20260627_001037.txt`](./transcripts/callback_followup_20260627_001037.txt)

- The requested callback details are not answered directly.
- The agent response becomes malformed and drifts into unrelated text.

### `callback_followup_20260627_001557`
The opening turn is garbled, the agent repeatedly forces clarification, and the callback conversation still does not close cleanly.

Evidence: [`transcripts/callback_followup_20260627_001557.txt`](./transcripts/callback_followup_20260627_001557.txt)

- The opening agent speech is truncated.
- Several agent turns are unclear enough to trigger repeated "Could you repeat that?" turns.
- The agent says the team will reach out soon, but the call still does not end cleanly.

### `cancel_appointment`
The cancellation flow is mostly successful, but the agent is noisy and redundant. It interleaves fee handling, cancellation, and follow-up questions in a way that makes the flow feel unstable.

Evidence: [`transcripts/cancel_appointment_20260626_233646.txt`](./transcripts/cancel_appointment_20260626_233646.txt)

- The agent asks for confirmation while also narrating that the appointment is being canceled.
- The fee answer is vague and partially muddled.
- The agent asks for the cancellation reason after the cancellation flow has already started.

### `refill_request`
The refill flow never fully answers the main patient question. The agent redirects to a representative and then ends the interaction without clearly stating whether an appointment is required or how long the refill takes.

Evidence: [`transcripts/refill_request_20260626_234347.txt`](./transcripts/refill_request_20260626_234347.txt)

- The patient asks the key refill questions directly.
- The agent gives a garbled support-team response instead of answering.
- The agent then cuts to a goodbye-style transfer line before the questions are resolved.

### `office_hours`
The office-hours flow contains partial or clipped responses before the final answer lands. The agent also gives a vague "regular business" reply that is not usable on its own.

Evidence: [`transcripts/office_hours_20260626_234915.txt`](./transcripts/office_hours_20260626_234915.txt)

- The early agent responses are garbled.
- The lunch-hour question receives an incomplete answer first.
- The transcript includes a final extra "say that again" style turn after the call is already done.

### `location_info`
The location flow has a clipped agent turn in the middle of the directions exchange.

Evidence: [`transcripts/location_info_20260626_235615.txt`](./transcripts/location_info_20260626_235615.txt)

- The agent gives free parking information correctly.
- The main-entrance answer is interrupted by a broken "And had." turn.
- The directions are only completed after the patient has to ask again.

### `insurance_question`
The insurance flow is not direct enough. The agent gives a broad PPO statement but takes too long to provide a simple answer, and one turn is clipped mid-sentence.

Evidence: [`transcripts/insurance_question_20260627_000112.txt`](./transcripts/insurance_question_20260627_000112.txt)

- The patient asks for a specific PPO answer.
- The agent shifts into a generic insurance-link flow instead of answering directly.
- One agent turn is truncated: "I just sent the".

### `reschedule_appointment`
The reschedule flow contains several garbled agent turns and a broken appointment summary, even though the conversation eventually reaches a usable outcome.

Evidence: [`transcripts/reschedule_appointment_20260626_233130.txt`](./transcripts/reschedule_appointment_20260626_233130.txt)

- The opening agent response is clipped.
- The agent says "You have an upcoming great." instead of a clean status update.
- The provider and appointment confirmation are eventually recovered, but only after repeated clarification.

### `unclear_request`
The agent does not keep the vague request moving cleanly. It starts with a wrong-name prompt, then ends in a transfer/goodbye line before the request is fully resolved.

Evidence: [`transcripts/unclear_request_20260627_002000.txt`](./transcripts/unclear_request_20260627_002000.txt)

- The opening verification turn is garbled.
- The patient has to explain the problem in multiple ways.
- The call ends with a transfer-style goodbye before the vague request is fully closed out.

### `unusual_edge_case`
The mixed refill-plus-appointment scenario is not handled gracefully. The agent keeps drilling into pharmacy details before cleanly addressing the scheduling part of the request.

Evidence: [`transcripts/unusual_edge_case_20260627_002612.txt`](./transcripts/unusual_edge_case_20260627_002612.txt)

- The patient presents two related needs in one call.
- The agent keeps asking for pharmacy specifics and location detail.
- The scheduling request is not prioritized clearly, and the conversation ends with another clarification prompt.
