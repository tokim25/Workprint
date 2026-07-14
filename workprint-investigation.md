# Workprint Investigation — Workprint

**Scope:** Initial product and repository creation

## Evidence coverage

| Dimension | Coverage |
|---|---:|
| Timestamp | 6/6 (100.0%) |
| Actor | 6/6 (100.0%) |
| Source locator | 6/6 (100.0%) |
| High-reliability evidence | 5/6 (83.3%) |

> Coverage describes supplied records only; it does not measure how complete the project history is.

## Timeline

| Event | Time | Actor | Activity | Observation | Evidence |
|---|---|---|---|---|---|
| EV-001 | 2026-07-14T12:00:00-07:00 | Tony Kim | question | Asked whether Claude could determine human time versus AI time on a project. | Initial user question |
| EV-002 | 2026-07-14T12:12:00-07:00 | ChatGPT | suggestion | Suggested replacing unsupported human-versus-AI percentages with evidence-based project attribution. | Evidence-based attribution discussion |
| EV-003 | 2026-07-14T12:15:00-07:00 | Tony Kim | adoption | Adopted the evidence-based project attribution direction. | User approval |
| EV-004 | 2026-07-14T13:20:00-07:00 | Tony Kim | decision | Selected Workprint as the working product name. | Naming decision |
| EV-005 | 2026-07-14T14:05:00-07:00 | ChatGPT | drafting | Generated the initial repository documentation and Claude skill package. | README.md |
| EV-006 | 2026-07-14T14:30:00-07:00 | Tony Kim | implementation | Uploaded the initial Workprint repository to GitHub. | Repository upload |

## Decisions

| Decision | Date | Actor | Outcome | Statement | Confidence |
|---|---|---|---|---|---|
| D-001 | 2026-07-14T12:15:00-07:00 | Tony Kim | adoption | Adopted the evidence-based project attribution direction. | High |
| D-002 | 2026-07-14T13:20:00-07:00 | Tony Kim | decision | Selected Workprint as the working product name. | High |

## Findings

### F-001

**Finding:** ChatGPT is recorded performing: drafting, suggestion.

**Classification:** Qualitative

**Confidence:** High

**Evidence:** EV-002, EV-005

**Reasoning:** The listed activities are directly present in normalized evidence records.

**Alternative explanations:**
- The evidence may omit unrecorded contributors or activities.

### F-002

**Finding:** Tony Kim is recorded performing: adoption, decision, implementation, question.

**Classification:** Qualitative

**Confidence:** Medium

**Evidence:** EV-001, EV-003, EV-004, EV-006

**Reasoning:** The listed activities are directly present in normalized evidence records.

**Alternative explanations:**
- The evidence may omit unrecorded contributors or activities.

### F-003

**Finding:** The evidence contains 2 explicit decision event(s).

**Classification:** Measured

**Confidence:** High

**Evidence:** EV-003, EV-004

**Reasoning:** Events classified as decision, adoption, or rejection are treated as explicit decision records.

### F-004

**Finding:** Timestamped evidence contains 40 minute(s) of observed multi-event session span.

**Classification:** Estimated

**Confidence:** Medium

**Evidence:** EV-001, EV-002, EV-003, EV-005, EV-006

**Reasoning:** Events no more than 30 minutes apart were grouped into sessions. This is an observed span, not total active time.

**Alternative explanations:**
- The contributor may have been idle during gaps.
- Work may have occurred before, after, or between recorded events.

## Unknowns

- Exact thinking, reading, and offline planning time cannot be determined from event records alone.
- The engine cannot determine whether every AI-generated artifact was reviewed, used, or discarded unless evidence records that outcome.

## Limitations

- The engine analyzes normalized evidence and does not verify source authenticity.
- A recorded AI response does not prove that its contents were adopted.
- Activity timestamps do not measure unrecorded or offline work.
