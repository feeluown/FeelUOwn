# AGETNS.md (Draft)

This file is a working draft for contributors/agents. It summarizes project
structure, core docs, and practical workflows for changes in FeelUOwn.

## 1) Project Overview

- Project: FeelUOwn (desktop music player, Python + Qt)
- Main package: `feeluown/`
- Entrypoint CLI: `feeluown` / `fuo`
- App modes: GUI-first, with protocol and server capabilities

Key references:
- `README.md`
- `README.en.md`
- `docs/source/index.rst`

## 2) Repository Map (high signal)

- `feeluown/`: application source
  - `app/`: app bootstrap, config, lifecycle
  - `entry_points/`: CLI entry logic (`run.py`)
  - `gui/`: Qt UI (pages, widgets, sidebars, provider UI)
  - `library/`: provider abstraction and protocols
  - `player/`: playback, playlist, FM/radio, media handling
  - `server/`, `webserver/`: protocol/server side logic
  - `models/`, `serializers/`, `utils/`: common infra
- `tests/`: unit tests
- `integration-tests/`: integration test runner
- `docs/source/`: user + developer docs
- `Makefile`: lint/test/build tasks
- `pyproject.toml` and `uv.lock`: dependency/runtime config

## 3) Development Workflow (uv-first)

Use `uv` as the default project/dependency runner. Prefer `uv` commands over
direct `pip` usage for daily development.

Suggested setup:
1. Prepare a Python >= 3.10 environment
2. Sync dependencies with `uv`
3. Run checks via `uv run`

Useful commands:
- `uv sync --group dev --extra qt --extra jsonrpc`
- `uv run make pytest`
- `uv run make test`
- `uv run make integration_test`
- `uv run make lint`

Notes:
- GUI tests are partially excluded in default pytest addopts.
- Integration tests run with `QT_QPA_PLATFORM=offscreen`.

## 4) Coding and Contribution Style

Primary docs:
- `docs/source/dev_quickstart.rst`
- `docs/source/coding_style.rst`
- `docs/source/contributing.rst`
- `docs/source/arch.rst`

Practical conventions:
- Prefer small, focused changes.
- Add/adjust tests for behavior changes under `feeluown/`.
- Keep comments/docstrings in English.
- For Qt widgets, prefer a `setup_ui` style split when code grows.
- Handle provider/network exceptions defensively in GUI flows.

## 5) Workflow

Keep a lightweight todo list for the current task:
- Update it before/after each meaningful step.
- Mark items done as soon as they are completed.
- Save it under `.tasks/` (for example, `.tasks/todo.md`).

Keep a short proposal note for design changes:
- Capture the intended approach, tradeoffs, and assumptions.
- Use it to confirm alignment before coding.
- Save it under `.tasks/` (for example, `.tasks/proposal.md`).

Minimal templates:

Todo:
- [ ] Step 1
- [ ] Step 2

Proposal:
- Approach: ...
- Tradeoffs: ...
- Assumptions: ...
