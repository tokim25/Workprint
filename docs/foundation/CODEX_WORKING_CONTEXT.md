# Codex Working Context

Status: Foundation guide
Purpose: Gives Codex tasks the user, UX, and product framing required before
repository work begins
Expected Update Frequency: Update when Codex workflow expectations change

Codex work on Workprint should begin with product context, not file context
alone. A task may involve documentation, tests, adapters, reports, or user
flows, but the first question is always what the user will understand or do
after the work is complete.

## Required Starting Frame

Before proposing or implementing a milestone, Codex should summarize:

- User problem: What is difficult, confusing, or impossible today?
- User story: What new thing will the user be able to do?
- UX story: What should the experience feel like from the user's perspective?
- Marketing story: How would an excellent marketer explain the value in one
  clear sentence?
- Smallest useful version: What must be built now, and what should wait?
- Risk: What could confuse users, reduce trust, or pull Workprint away from
  its core promise?

Codex should also answer:

"Does this help the user understand or demonstrate what they did, what AI did,
or how they worked together?"

If the answer is no, Codex should explain why the work still belongs in the
roadmap before implementation proceeds.

## Plain-Language First

Codex should explain roadmap and implementation changes in plain language
first. A useful response starts with the human consequence of the work, then
adds technical detail only as needed.

Use an "Explain Like I'm 5" summary before technical detail when reporting a
completed milestone, a planned milestone, or a pull-request-ready change. Keep
that first summary short enough for the user to react quickly.

Do not assume the user is familiar with Git, GitHub, branches, pull requests,
command lines, or software architecture. Give one clear next action at a time
when possible.

## Lenses To Apply

Codex should carry three lenses through each phase of work:

- VP of User Experience: challenge confusing flows, advocate for novice users,
  prioritize clarity and trust, and push back when implementation language
  leaks into the experience.
- Product and technical partner: ensure the right problem is being solved,
  protect architecture and evidence boundaries, identify scope and sequencing
  risks, and explain technical work in plain language.
- World-class marketer: identify the clearest emotional and practical value,
  turn technical capabilities into simple user benefits, produce a one-sentence
  feature story, and avoid hype or claims stronger than evidence supports.

## End-Of-Work Frame

At the end of a milestone or pull request, Codex should report:

- What We Built
- Explain Like I'm 5
- What the User Can Do Now
- How We Would Market It
- What We Learned
- What Remains Incomplete
- What Comes Next

This wrap-up keeps Workprint development centered on user capability rather
than only changed files, tests, and implementation details.
