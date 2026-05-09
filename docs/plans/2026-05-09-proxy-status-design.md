# Proxy Status Design

## Context

PR #1027 adds proxy detection during startup and shows the result in the GUI.
The current implementation stores a display string on `App`, logs raw proxy URLs,
and reaches into `BottomPanel` internals from `GuiApp` to update a tooltip.

## Goals

- Keep proxy state structured in the app layer.
- Move proxy display logic into a dedicated GUI component.
- Sanitize proxy URLs before they reach logs or tooltips.
- Add focused tests for the utility and widget behavior.

## Approaches

### Option 1: Keep current shape and add helper functions

Add URL sanitization helpers but keep `_proxy_info` on `App` and keep tooltip
updates in `GuiApp`.

Tradeoff: Smallest patch, but the app layer still owns presentation strings and
GUI code still depends on `StatusLine` internals.

### Option 2: Store structured state and add a proxy component

Store a proxy mapping on `App`, move formatting/sanitization into a dedicated
`ProxyStatusButton`, and let `BottomPanel` own the component.

Tradeoff: Slightly broader refactor, but it aligns with the repository's GUI
layering rules and removes the current coupling.

### Option 3: Full proxy status model/service

Add a separate state object plus signals for future interactive proxy control.

Tradeoff: Too much structure for the current requirement.

## Decision

Choose option 2.

`App.initialize()` will only detect and store proxy settings. A new
`ProxyStatusButton` component under `gui/components/` will sanitize proxy URLs
for display, decide the tooltip text, and expose a small update method.
`BottomPanel` will instantiate this component and update it from app state
without exposing `StatusLine` internals.

## Testing

- Add utility tests for sanitizing proxy URLs with embedded credentials.
- Add a GUI test for `ProxyStatusButton` tooltip behavior with and without
  proxies.
- Keep verification focused on the touched utility and GUI test modules.
