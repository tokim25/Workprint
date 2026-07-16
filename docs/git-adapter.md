# Git Adapter

The Git adapter imports evidence from a local Git repository using the
canonical source ID `git` and reader-facing label `Git`.

The adapter is local-only. It does not call the GitHub API, does not require a
remote, and does not use network access.

## Supported Inputs

Supported in v1:

- a local non-bare Git repository root;
- a path inside a local non-bare Git worktree when `git rev-parse
  --show-toplevel` can resolve the repository root;
- an empty repository, represented by repository metadata and zero commit
  records;
- a shallow repository, with a disclosed limitation.

Unsupported in v1:

- bare repositories;
- remote-only repositories;
- automatic traversal of unrelated nested repositories;
- file-content inspection;
- identity resolution across names or email addresses.

When discovery runs on a selected project directory, Workprint checks that
directory's Git context. It does not recursively search for unrelated nested
repositories.

## Collection Mechanism

Workprint invokes the installed `git` command through a small deterministic
adapter boundary. Commands use explicit argument arrays, UTF-8 handling, and
`core.quotePath=false` so Unicode paths are preserved as text.

The adapter uses read-only commands such as:

- `git rev-parse --show-toplevel`
- `git rev-parse --is-bare-repository`
- `git rev-parse --is-shallow-repository`
- `git branch --show-current`
- `git log --reverse`
- `git show -s`
- `git diff-tree`
- `git tag --points-at`

The adapter does not run checkout, reset, fetch, pull, push, merge, rebase, or
branch-changing commands.

## Evidence Collected

Repository records preserve:

- repository root;
- current branch when available;
- bare repository status;
- shallow repository status.

Commit records preserve Git-recorded values for:

- full commit SHA;
- abbreviated SHA;
- commit timestamp;
- author name and email;
- committer name and email;
- subject;
- body;
- parent SHAs;
- merge status;
- changed file paths;
- per-file change type when available;
- additions and deletions when available;
- tags pointing at the commit.

Every observation retains evidence references tied to the repository, commit
SHA, and relevant file path when file-specific.

## Evidence Semantics

Git evidence is mapped conservatively:

- A commit may support implementation chronology.
- A merge commit may support a branch-integration milestone.
- A commit message may support a decision only when the text itself explicitly
  states a decision.
- File changes support that repository artifacts changed, not why they changed
  unless the evidence says so.
- Additions and deletions describe repository changes, not human effort,
  ownership, value, productivity, authorship, or contribution.

Git author and committer fields are preserved exactly as recorded by Git. They
do not prove who personally wrote every changed line, and Workprint does not
resolve identities across different names or email addresses.

Git author and committer fields preserve identities recorded in repository
history. They do not prove who personally wrote every changed line, establish
ownership, or measure contribution.

## Executive Report Effects

When Git evidence is supplied, the Executive Report can use it to support
implementation chronology, repository milestones, merge milestones, completed
output evidence, and Git-history coverage.

Git evidence does not automatically raise confidence merely because it exists.
Confidence improves only under the existing deterministic rules, such as when
Git evidence supports the same executive claim as another evidence reference.

If the repository reports shallow history, Workprint records that limitation.
Shallow history may omit earlier commits, tags, branch history, or context
needed to reconstruct chronology.

## Privacy

Git history may contain personal or sensitive data, including:

- names;
- email addresses;
- commit messages;
- branch context;
- file paths.

Workprint preserves those values by default because they are part of the
evidence. The Git adapter does not send Git data to external services. It does
not redact values unless a future Workprint redaction feature explicitly
supports that behavior.
