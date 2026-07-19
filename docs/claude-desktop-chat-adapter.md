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
   which Anthropic does not document. The library it depends on, and the
   specific database it scans, have been verified against real local data
   (see "How This Was Verified" below) — but whether that database actually
   holds *recoverable* conversation content on a given machine has not been.
   Treat its output as a lead worth checking, not settled evidence.

## Two Modes

### Presence-only (default)

`ClaudeDesktopChatAdapter()` with no arguments only checks whether the local
cache directory exists and reports its last-modified time. No dependency is
required, and no conversation content of any kind is read. This is the mode
used automatically by `workprint discover`.

### Deep parse (opt-in, experimental)

`ClaudeDesktopChatAdapter(deep_parse=True)` scans only the verified
`keyval-store` database (see "How This Was Verified") using the pinned
`ccl_chromium_reader` dependency (`pip install 'workprint[claude-desktop-chat]'`),
then runs a best-effort heuristic scan of each record's deserialized value
for dicts shaped like a chat turn (a role/sender field plus a content/text
field). Deleted/superseded record versions are excluded
(`live_only=True`), so deep parsing should not resurface conversations
already deleted from claude.ai. A record that fails to read — most commonly
because its value was moved to an external "blob" file that IndexedDB's own
metadata still references but which no longer exists on disk — is skipped
rather than aborting the scan.

If the dependency is missing, this raises a clear error rather than silently
falling back. If the dependency is present but nothing readable is found,
this falls back to the presence-only record rather than claiming zero
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
>   claude.ai chat has no concept of a project folder. It skips
>   conversations already deleted from claude.ai, but it may still find
>   nothing readable even when chat history exists, since some entries in
>   this cache have been observed to be unrecoverable.
> - Either way: this stays entirely on your machine. Nothing is uploaded,
>   and the output is visible only to whoever runs this command.

## How This Was Verified

An earlier version of this adapter depended on a PyPI package
("chromium-reader") that turned out to be an unrelated project from the one
actually researched, with a real bug in its own metadata parsing. See
`docs/foundation/DECISION_LOG.md`, "Claude Desktop Chat's Optional
Dependency Is Pinned, Not Name-Matched," for the full story and the general
principle it produced. What follows describes what was verified once that
was corrected and the real dependency (`cclgroupltd/ccl_chromium_reader`,
pinned to a specific commit) was actually run against real local data.

Confirmed against a real local installation:

- The pinned library correctly opens the store and enumerates its real
  databases. This origin has exactly four: `keyval-store`,
  `claude-notifications`, `claude-device-binding`, and
  `omelette-fs-access`. Only `keyval-store` is scanned — the other three
  are not conversation-shaped, and `claude-device-binding` in particular
  plausibly holds authentication or device-identity material that should
  never be treated as scannable evidence.
- `keyval-store` has a single object store, `keyval`, consistent with the
  `idb-keyval` JavaScript library's default naming — evidence that Claude's
  web client most likely uses that library for local persistence here,
  though that is an inference, not a documented fact.
- Individual unreadable records (missing externally serialized blob files)
  are real and must be skipped without aborting the scan; this was not a
  hypothetical concern; it happened on the first real record encountered
  during verification.
- The heuristic turn-scanning logic (`_as_candidate_turn`,
  `_walk_candidate_turns`) correctly finds and classifies turn-shaped
  records once a readable value is available. This was confirmed not
  against hand-crafted bytes, but against a database written by an actual
  Chrome browser through the real `indexedDB.open()`/`put()` APIs — so the
  on-disk encoding is genuinely Chromium's, not a guess at what it might
  look like. That fixture is committed at
  `fixtures/claude-desktop-chat/synthetic-keyval-store.indexeddb.leveldb`
  (containing only synthetic text written for this test, not real user
  data) and exercised by
  `test_deep_parse_against_genuine_chromium_encoded_fixture` whenever the
  optional dependency is installed.

Not yet confirmed:

- Whether claude.ai's own real `keyval-store` value, on a given machine at
  a given time, is actually readable and actually contains the
  conversation-shaped structure the heuristic looks for. What's confirmed
  above is that the *code* correctly finds and classifies that shape when
  it is present and readable — not that claude.ai's web client reliably
  produces a readable value of that shape in practice. Across several
  dogfood runs against the live real cache (Claude Desktop actively
  running throughout, not a copy), one run's full `workprint discover`
  pipeline did report finding one candidate turn; three immediately
  following runs found nothing readable, consistent with reading a
  database the running app is actively writing to.
- Windows and Linux default paths, which follow the platform's usual
  Electron app-data convention but were not independently checked.

## Evidence Collected

In deep-parse mode, each recovered turn is recorded with a turn ID, role
(`human` or `assistant`), and — when parseable — a timestamp. Content is
structural by default (a fixed label, not the actual text); raw excerpts
require `include_content_excerpts=True`, not currently exposed through the
CLI. Every record's metadata includes `project_specific: false`,
`experimental_deep_parse: true`, and `may_include_deleted_records: false`
(reflecting the `live_only=True` filtering above, recorded explicitly so
the mitigation stays visible and auditable rather than merely assumed).

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
- Deep-parse mode can surface real prompt and response text. It excludes
  already-deleted conversations by construction (`live_only=True`), and it
  only ever opens the `keyval-store` database — `claude-device-binding` and
  the other two databases in this origin are never opened, let alone read.
- Nothing this adapter reads is ever sent anywhere; all processing is local.
- The `title` and `initialMessage`-equivalent risk that applies to Cowork
  metadata does not apply here in the same way, but the same principle
  does: raw content stays out of the default output, and opting into
  excerpts is a separate, explicit choice from opting into deep parsing at
  all.
