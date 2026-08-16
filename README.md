# TinyBoard — AgentBox automation fixture work repository

This repository is a deliberately tiny, dependency-free Python project used to test AgentBox autonomous planning, implementation, adversarial review, and acceptance.

It is intentionally incomplete. The required task-domain, persistence, CLI, duplicate-title, archive, and summary behavior is defined by the separate public control repository:

https://github.com/NevynIt/agentbox-automation-fixture-control

## Baseline

Python 3.11 or newer is required. There are no runtime dependencies.

From a source checkout, run the baseline module with the source directory on `PYTHONPATH`:

```bash
PYTHONPATH=src python3 -m tinyboard --version
```

Expected output:

```text
tinyboard 0.1.0
```

Run the baseline tests with:

```bash
python3 -m unittest discover -s tests -v
```

The five ADR features are intentionally **not implemented** in this initial repository. They are the work for the AgentBox ADR-0017 orchestration acceptance fixture.

## Duplicate active titles

`add` rejects a title when its normalized, case-insensitive comparison key
(`normalize_title(title).casefold()`) matches an existing active task. The
command exits unsuccessfully and leaves the database unchanged. Completed or
archived tasks do not block adding the same title again.

## Archive and summary

`archive ID` archives one task, and refuses to archive an incomplete task.
Archived tasks are omitted from `list` and remain archived after reloading the
database. Repeating an archive of an already archived completed task is
idempotent.

`summary` prints one-line JSON. Its `total` count includes all records,
including archived records. `active` counts incomplete, non-archived tasks;
`completed` counts completed, non-archived tasks; and `archived` counts
archived tasks, so these counts sum to `total`.
