# AGENTS.md

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
- `uv sync --group dev --extra qt --extra jsonrpc --extra battery`
- `uv run make pytest`
- `uv run make test`
- `uv run make integration_test`
- `uv run make lint`

Notes:
- GUI tests are partially excluded in default pytest addopts.
- Integration tests run with `QT_QPA_PLATFORM=offscreen`.
- Before commit/push for PR updates, run full `uv run make test` and record
  result summary in the PR thread.

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

## 5) GUI Architecture Rules

Layering rules for GUI code:
- `gui/widgets/`: app-independent reusable widgets.
- `gui/components/`: reusable UI units that depend on `app` or app managers.
- `gui/pages/`: route-level orchestration and page composition only.

Placement rule for shared UI:
- If a shared UI piece needs `app` (e.g. browser navigation, provider UI manager),
  place it under `gui/components/`, not `gui/widgets/` or a specific page module.

Page rendering rule:
- For pages rendered as custom widget bodies, use shared page-level helpers
  (for example, `render_scroll_area_view`) to keep route rendering behavior
  consistent and avoid duplicated setup code.

Provider-scoped vs multi-provider presentation:
- Multi-provider pages should keep source-identifying affordances.
- Provider-scoped pages should prefer cleaner headers and avoid redundant
  source decorations.

Responsive layout rule:
- Let a page own its responsive reflow logic based on its own available width.
- Avoid parent-coupled resize orchestration unless there is a proven structural
  need.

## 6) Workflow

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

## 7) Recent Engineering Notes

- Prefer semantic API names over scenario-specific ones:
  - Good: `show_cover_from_metadata(artwork, source, uid)`
  - Avoid: names that encode one caller context (for example `show_current_song_*`)
- For cover/image loading, keep a clear boundary:
  - Data/adapter layer should convert `(url, source)` into `Media`.
  - Widget layer should consume `Media` directly (`show_cover_media`) whenever possible.
- Avoid broad fallback branches that hide failures. If input contract is wrong,
  fail early with explicit type/shape checks.
