# Claude Desktop Chat Adapter (Experimental)

The Claude Desktop Chat adapter reports on the Claude desktop app's local
cache of claude.ai web chat, using the canonical source ID
`claude-desktop-chat` and reader-facing label `Claude Desktop Chat`.

This adapter is materially different from every other adapter in this
package, in two ways that matter before using it:

1. **It cannot be scoped to a project.** Claude Code and Claude Cowork
   sessions record which folder they ran in; a claude.ai chat conversation
   does not. So even at its most capable, this adapter can only report that
   claude.ai chat activity exists on the machine — never that a specific
   conversation relates to the project currently being investigated. Every
   record this adapter produces carries `project_specific: false`.
2. **Its deep-parse mode is experimental**, in the literal sense: the
   on-disk format is Chromium's internal IndexedDB-over-LevelDB storage,
   which Anthropic does not document and this adapter's author did not
   independently verify against a running parser (see "How This Was Built"
   below). Treat its output as a lead worth checking, not settled evidence.

## Two Modes

### Presence-only (default)

`ClaudeDesktopChatAdapter()` with no arguments only checks whether the local
cache directory exists and reports its last-modified time. No dependency is
required, and no conversation content of any kind is read. This is the mode
used automatically by `workprint discover`.

### Deep parse (opt-in, experimental)

`ClaudeDesktopChatAdapter(deep_parse=True)` attempts to extract real
conversation turns using the optional `ccl_chromium_reader` dependency
(`pip install 'workprint[claude-desktop-chat]'`) plus a best-effort
heuristic scan for dict-shaped values that look like a chat turn (a
role/sender field plus a content/text field). If the dependency is missing,
this raises a clear error rather than silently falling back. If the
dependency is present but the heuristic scan finds nothing that looks like a
turn, this falls back to the presence-only record rather than claiming zero
conversations exist.

The `workprint guide` terminal wizard offers this as an explicit choice
when it detects the cache, with the same trade-off language reproduced
below, rather than turning it on automatically. It is never enabled by
non-interactive or scripted runs (`workprint guide --include ...` or
`--yes`) — only the fully interactive prompt can turn it on, and only for
that run.

## The Trade-off, in Plain Language

This is the exact text shown by `workprint discover` and `workprint guide`
when the cache is detected:

> Workprint can optionally read this cache in more detail using an
> experimental, opt-in parser (not on by default).
>
> - Without it: Workprint only notes that the cache exists and when it last
>   changed. No conversation content is read.
> - With it: Workprint attempts to extract real chat turns, but this
>   evidence is account-wide, not specific to this project, because
>   claude.ai chat has no concept of a project folder. It may also surface
>   conversations you deleted from claude.ai, since the local cache does
>   not always remove them right away.
> - Either way: this stays entirely on your machine. Nothing is uploaded,
>   and the output is visible only to whoever runs this command.

## How This Was Built

The presence-only path was verified against a real local installation. The
deep-parse path was written against `ccl_chromium_reader`'s documented API
and empirically observed object-store name fragments (`keyval-store`,
`val-store`) found by scanning a real local cache file for readable
strings — which also turned up plausible message-shaped field names
(`uuid`, `created_at`, message-role-adjacent text), suggesting real
conversation data likely is recoverable. It was not run end-to-end against
real data in the environment this adapter was built in, because that
environment had no Python 3.10+ interpreter available (the dependency
requires it) and could not install the package to verify. Anyone enabling
deep parsing is the first real test of this path against their own data;
if it produces nothing, it falls back to the presence-only record rather
than failing the whole command.

## Evidence Collected

In deep-parse mode, each recovered turn is recorded with a turn ID, role
(`human` or `assistant`), and — when parseable — a timestamp. Content is
structural by default (a fixed label, not the actual text); raw excerpts
require `include_content_excerpts=True`, not currently exposed through the
CLI. Every record's metadata includes `project_specific: false` and
`experimental_deep_parse: true`, and `may_include_deleted_records: true` as
a standing reminder of the IndexedDB retention risk described above.

## Evidence Semantics

Because this source cannot be tied to the project under investigation and
its extraction is heuristic, Workprint does not treat deep-parsed turns from
this adapter as equivalent in reliability to Claude Code or Cowork evidence.
A turn supports only that some claude.ai chat activity occurred at
approximately that time — not that it relates to this project, and not that
the extraction is complete or accurate.

## Privacy

- Presence-only mode reads nothing but a directory's existence and
  modification time.
- Deep-parse mode can surface real prompt and response text, including
  conversations already deleted from claude.ai's own interface, because
  local caches do not always garbage-collect deleted records promptly.
- Nothing this adapter reads is ever sent anywhere; all processing is local.
- The `title` and `initialMessage`-equivalent risk that applies to Cowork
  metadata does not apply here in the same way, but the same principle
  does: raw content stays out of the default output, and opting into
  excerpts is a separate, explicit choice from opting into deep parsing at
  all.
