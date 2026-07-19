# Claude Cowork Adapter

The Claude Cowork adapter imports evidence from local Claude Cowork session
transcripts using the canonical source ID `claude-cowork` and reader-facing
label `Claude Cowork`.

The adapter is local-only. It reads session data already written to disk by
the Claude desktop app; it does not call any network service.

## How Cowork Sessions Are Stored

Each Cowork session runs in its own sandboxed environment with its own
Claude Code home directory. That sandbox writes a transcript in the same
JSONL shape the [Claude Code adapter](claude-code-adapter.md) reads
(`type: "user" | "assistant"`, `message.content` as text or structured
blocks). This adapter reads that same shape independently — it does not
share code with the Claude Code adapter, matching this codebase's existing
pattern of self-contained adapters.

Because a Cowork transcript's own `cwd` points at an internal sandbox output
path rather than the user's real project directory, sessions are matched
using the `userSelectedFolders` list recorded in the session's metadata file
(`local_<uuid>.json`, found alongside the transcript directory). A project
directory that is not exactly present in any session's `userSelectedFolders`
is not matched — this is a deliberate fail-closed choice, the same one the
Claude Code adapter makes for its own matching.

## Supported Inputs

Supported in v1:

- Claude Cowork session transcripts stored under the Claude desktop app's
  local session-data directory (by default
  `~/Library/Application Support/Claude/local-agent-mode-sessions` on
  macOS), matched to the selected project directory via
  `userSelectedFolders`.

The default location is verified against a real macOS installation. The
Windows (`%APPDATA%\Claude\local-agent-mode-sessions`) and Linux
(`$XDG_CONFIG_HOME/Claude/local-agent-mode-sessions` or
`~/.config/Claude/local-agent-mode-sessions`) defaults follow the platform's
usual Electron app-data convention but are not independently verified. Set
`WORKPRINT_COWORK_HOME` to override if they are wrong.

Unsupported in v1:

- Claude Desktop's own chat history (as opposed to Cowork sessions), which
  is cached in an undocumented internal LevelDB format and is tracked
  separately.
- The session metadata file's `title` and `initialMessage` fields, which can
  contain real prompt text. Only the nested transcript's structural turns
  are read; the sibling metadata file's `userSelectedFolders` is used only
  for matching.
- Cowork's own `audit.jsonl` action log inside each sandbox, which records
  tool permissions and actions separately from the Claude Code-shaped
  transcript. Not read in v1.

## Evidence Collected

Each Cowork session turn is recorded as a normalized message with:

- a turn ID, session ID, timestamp, and role (`human` or `assistant`);
- whether the turn was part of a subagent ("sidechain") run;
- the Cowork session ID, model, session type (for example `scheduled`), and
  archived status, taken from the session's metadata file.

Message content is structural by default, matching the Claude Code adapter:

- Human turns record only that a message was sent and its character length.
- Assistant turns record how many text responses were present and a count
  of tool names used, not tool arguments, file contents, or command output.

Raw text excerpts (bounded to roughly 600 characters) are only included when
the adapter is constructed with `include_content_excerpts=True`. This is not
currently exposed through the CLI.

## Evidence Semantics

Claude Cowork evidence is mapped conservatively, using the same rules as the
Claude Code adapter: a turn supports that a message was exchanged and, for
assistant turns, that certain tools were used a certain number of times.
Tool-use counts describe recorded invocations, not effort, ownership, value,
authorship, or contribution.

## Privacy

Cowork sandboxes can contain anything a person asked Cowork to do, including
work on personal or proprietary files. Because discovery can run
automatically rather than only after a manual export, this adapter's default
behavior never includes raw prompt or response text, the session title, or
the initial message — only structural signal. Raw text excerpts from the
transcript require explicit opt-in at the adapter level.

The adapter does not send session data to external services, and it does
not read any file in a Cowork sandbox outside `.claude/projects` and the
sibling metadata file's `userSelectedFolders` field.
