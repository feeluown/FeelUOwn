# Proxy Status Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor proxy detection so app state stays structured and GUI proxy presentation is encapsulated in a dedicated component.

**Architecture:** Keep proxy detection in the app layer, move proxy formatting and tooltip presentation into a `ProxyStatusButton`, and validate the behavior with focused utility and GUI tests. The utility layer will provide sanitization helpers so logs and tooltips never expose proxy credentials.

**Tech Stack:** Python, PyQt6, pytest, pytest-qt

---

### Task 1: Red tests for proxy sanitization

**Files:**
- Modify: `tests/test_utils.py`
- Modify: `feeluown/utils/utils.py`

**Step 1: Write the failing test**

Add tests that expect a helper to remove `username:password@` from proxy URLs
and format a sanitized proxy mapping for display.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_utils.py -k proxy -v`
Expected: FAIL because the helper does not exist yet.

**Step 3: Write minimal implementation**

Add small helpers in `feeluown/utils/utils.py` to sanitize one proxy URL and
produce a sanitized mapping for presentation/logging.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_utils.py -k proxy -v`
Expected: PASS

### Task 2: Red tests for proxy status button behavior

**Files:**
- Create: `tests/gui/components/test_proxy_status.py`
- Create: `feeluown/gui/components/proxy_status.py`
- Modify: `feeluown/gui/components/__init__.py`

**Step 1: Write the failing test**

Add a GUI test that constructs a `ProxyStatusButton`, updates it with proxies,
and expects the tooltip to show a sanitized description; also verify the
no-proxy tooltip path.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/gui/components/test_proxy_status.py -v`
Expected: FAIL because the component does not exist yet.

**Step 3: Write minimal implementation**

Add `ProxyStatusButton` under `gui/components/` with an update method that
accepts the structured proxy mapping and sets the tooltip accordingly.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/gui/components/test_proxy_status.py -v`
Expected: PASS

### Task 3: Integrate structured proxy state into app and bottom panel

**Files:**
- Modify: `feeluown/app/app.py`
- Modify: `feeluown/app/gui_app.py`
- Modify: `feeluown/gui/uimain/toolbar.py`

**Step 1: Write the failing integration expectation**

Extend `tests/app/test_gui_app.py` so initialization expects the app to keep
structured proxy state and the bottom panel proxy button to receive sanitized
tooltip content.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/app/test_gui_app.py -k proxy -v`
Expected: FAIL because initialization still uses `_proxy_info` plumbing.

**Step 3: Write minimal implementation**

Store `self.proxies` on `App`, log a sanitized string, and update the bottom
panel through a simple method instead of reaching into the `StatusLine` from
`GuiApp`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/app/test_gui_app.py -k proxy -v`
Expected: PASS

### Task 4: Final verification

**Files:**
- Verify touched files only

**Step 1: Run focused verification**

Run: `uv run pytest tests/test_utils.py tests/gui/components/test_proxy_status.py tests/app/test_gui_app.py -v`
Expected: PASS

**Step 2: Review diff**

Run: `git diff -- feeluown/app/app.py feeluown/app/gui_app.py feeluown/gui/components feeluown/gui/uimain/toolbar.py feeluown/utils/utils.py tests`
Expected: Only proxy-related refactor and tests.
