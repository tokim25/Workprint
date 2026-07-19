# Claude Code Adapter

The Claude Code adapter imports evidence from local Claude Code session
transcripts using the canonical source ID `claude-code` and reader-facing
label `Claude Code`.

The adapter is local-only. It reads session transcripts already written to
disk by Claude Code; it does not call any network service and does not
require Claude Code to be running.

## Supported Inputs

Supported in v1:

- Claude Code session transcripts stored under `~/.claude/projects` (or the
  directory named by the `WORKPRINT_CLAUDE_HOME` environment variable),
  matched to the selected project directory.

Unsupported in v1:

- Claude Desktop chat history and Claude Cowork session history. Both are
  only reachable through undocumented internal application-cache formats
  and are tracked separately as a follow-on milestone.
- Session transcripts stored outside the default Claude Code home directory
  unless `WORKPRINT_CLAUDE_HOME` points at them.
- Raw prompt or response text by default. See Evidence Collected below.

## Matching Sessions to a Project

Claude Code writes each session transcript under a directory named for the
project path, but that naming convention is an internal implementation
detail of Claude Code, not a published contract. Rather than reproduce it,
the adapter opens each candidate session transcript and reads the `cwd`
value recorded on its early entries, then matches only sessions whose
recorded working directory resolves exactly to the selected project
directory.

If no session's recorded `cwd` matches, the adapter finds nothing rather
than guessing. This is a deliberate fail-closed choice: an incorrect match
would attribute a conversation to the wrong project.

Matching scans up to the 20 most recently modified matching sessions per
project. Within each session, at most 5,000 transcript lines are read.

## Evidence Collected

Each Claude Code session turn is recorded as a normalized message with:

- a turn ID, session ID, timestamp, and role (`human` or `assistant`);
- whether the turn was part of a subagent ("sidechain") run;
- the recorded working directory and Git branch for that turn.

Message content is structural by default, not raw transcript text:

- Human turns record only that a message was sent and its character length.
- Assistant turns record how many text responses were present and a count
  of tool names used (for example `Edit (2), Bash (1)`), not the tool
  arguments, file contents, or command output.

Raw text excerpts (bounded to roughly 600 characters, matching the excerpt
limit used elsewhere in Workprint) are only included when the adapter is
constructed with `include_content_excerpts=True`. This is not currently
exposed through the CLI; it exists for callers that explicitly opt in.

## Evidence Semantics

Claude Code evidence is mapped conservatively:

- A session turn supports that a message was exchanged between a person and
  Claude Code at a given time, and, for assistant turns, that certain tools
  were used a certain number of times.
- Tool-use counts describe recorded tool invocations, not effort, ownership,
  value, authorship, or contribution.
- Sidechain (subagent) turns are recorded with `is_sidechain: true` in
  metadata so they remain distinguishable from the primary conversation
  rather than silently merged into it.

## Privacy

Claude Code session transcripts can contain anything typed or pasted into a
prompt, including credentials, personal text, or proprietary code. Because
this adapter can run automatically during project discovery, rather than
only after someone manually exports and hands over a file, its default
behavior never includes raw prompt or response text — only structural
signal. Raw text excerpts require explicit opt-in at the adapter level.

The adapter does not send session data to external services.
