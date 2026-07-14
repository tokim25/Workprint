# Evidence Model

## Default reliability order

1. Original machine-generated records with stable timestamps
2. Native revision or version history
3. Original AI conversation logs
4. Original project-management and communication records
5. Exported copies of original records
6. Contemporaneous human notes
7. Later recollections
8. Model inference without direct support

Reliability and completeness are separate.

## Record example

```yaml
id: EV-0001
source_type: git_commit
source_name: repository-name
source_locator: commit SHA
event_time: 2026-07-13T16:12:03-07:00
actor: Tony Kim
activity: implementation
artifact: src/example.py
observation: Added the initial parser.
reliability: high
completeness: partial
notes: Commit time does not establish when all included work occurred.
```

## Source cautions

- Git proves recorded changes, not continuous active time.
- AI chats prove generation, not adoption into the final artifact.
- File timestamps may reflect syncing or export.
- Calendar duration proves scheduled time, not attendance or exclusive effort.
- Revision history is strong only when account identity and export completeness are reliable.
- Messages support decisions and chronology but rarely prove implementation effort alone.
- Time trackers are strongest for duration but may include idle time or missing sessions.

Two records are not independent when one was derived from the other.
