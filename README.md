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
