# Workprint MCP Server

Workprint can run as a local [Model Context Protocol](https://modelcontextprotocol.io)
server, so its evidence-discovery and investigation capabilities are
callable directly from inside Claude Desktop or Claude Code, instead of
only from the CLI or the web app.

## Installing

The `mcp` optional dependency (the official
[`modelcontextprotocol/python-sdk`](https://github.com/modelcontextprotocol/python-sdk),
published on PyPI as `mcp`) is required and not installed by default:

```bash
pip install -e '.[mcp]'
```

This installs a `workprint-mcp` command that runs the server over stdio,
the standard local transport both Claude Desktop and Claude Code expect.

## Configuring Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS; Settings → Developer → Edit Config from within the app also opens
it) and add an entry under `mcpServers`:

```json
{
  "mcpServers": {
    "workprint": {
      "command": "workprint-mcp"
    }
  }
}
```

If `workprint-mcp` is not on the PATH Claude Desktop uses (for example,
inside a virtual environment), point directly at the interpreter instead:

```json
{
  "mcpServers": {
    "workprint": {
      "command": "/absolute/path/to/venv/bin/python3",
      "args": ["-m", "workprint.mcp_server"]
    }
  }
}
```

Restart Claude Desktop after editing the config.

## Configuring Claude Code

Either run:

```bash
claude mcp add workprint --scope user -- workprint-mcp
```

or add it directly to a project's `.mcp.json` (use `--scope project` above
instead, if the config should be committed and shared with a team):

```json
{
  "mcpServers": {
    "workprint": {
      "command": "workprint-mcp"
    }
  }
}
```

## Tools

All three tools are read-only (`readOnlyHint: true`, `destructiveHint:
false`, `openWorldHint: false`) and only ever access the local
`project_path` given as an argument.

### `list_supported_sources`

Returns the evidence source IDs Workprint knows how to read (`git`,
`claude-code`, `claude-cowork`, `claude-desktop-chat`, `chatgpt`, `claude`,
`google-docs`, `figma`). No arguments.

### `discover_project`

`discover_project(project_path)` mirrors `workprint discover`: a bounded
preview of what evidence exists for a project directory, without reading
full content. Safe to call speculatively.

### `investigate_project`

`investigate_project(project_path, include=None, project_name=None,
include_desktop_chat_deep_parse=False, include_full_report=False,
include_observations=False, include_timeline=False)` runs a full
investigation and returns a structured report.

`include` uses the same selection syntax as the `workprint guide` CLI
wizard (`"all"`, `"1,3"`, `"git,claude-code"`, `"-google-docs"`, and so on).

**The default response is deliberately bounded, not the full report.** A
real investigation's complete JSON — raw observations, full timeline,
every finding's complete evidence-ID list — was measured at several
megabytes on this project's own history, far too large for a
conversational tool result. By default:

- findings carry only the first 10 evidence IDs plus a total count
  (`evidence_id_count`);
- the executive brief is included, but the rest of the executive report is
  not;
- observations and timeline are represented only as counts
  (`observation_count`, `timeline_event_count`).

Set `include_full_report`, `include_observations`, and/or
`include_timeline` to `true` for the complete data.

`include_desktop_chat_deep_parse` opts into Claude Desktop Chat's
experimental, account-wide deep-parse mode (see
[docs/claude-desktop-chat-adapter.md](claude-desktop-chat-adapter.md)). It
defaults to `false`, matching every other Workprint surface, because that
evidence cannot be confirmed to relate to the specific project being
investigated.

## Evidence Boundaries

The MCP server does not change what Workprint is allowed to claim. Every
guardrail that applies to the CLI and web app applies here: no authorship,
ownership, effort, or contribution-percentage inference; structural
evidence by default for session-based sources; explicit unknowns and
limitations included in every response.

## What This Does Not Do

- No write tools. The server cannot modify files, evidence, or Workprint's
  own configuration.
- No network access beyond what the underlying adapters already use (none
  of them make network calls; Git, Claude Code, Cowork, and Desktop Chat
  are all local-only).
- No project selection or ambient context: every tool call requires an
  explicit `project_path` argument. The server does not infer which
  project is "current."
