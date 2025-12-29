# MustWebUI Implementation Plan (small-first, TDD-first)

This document translates the specs in `docs/` into a **small-first** (minimal working vertical slices) implementation plan, explicitly assuming **test-driven development (TDD)**.

Premise: MustWebUI is best thought of as a **compiler/generator** that integrates FastAPI + Pydantic + Alpine.js. For each page it generates SSR HTML, embeds initial state safely, emits Alpine bindings, compiles event handlers (including typed RPC), and provides “battery-included” Tailwind-based defaults.

Specification sources:
- Architecture: docs/spec-architecture.md
- State Proxy: docs/spec-state-proxy.md
- Typed RPC / Actions: docs/spec-rpc-actions.md
- DSL (ml.*): docs/spec-dsl.md
- Component Catalog: docs/component-catalog.md
- Security / Ops: docs/spec-security-ops.md

---

## Principles

### Small-first

- Every milestone must produce something observable: a working route, a generated HTML diff, or a clear compile-time error.
- Implement only the **minimum normative surface** first; defer phase-2 items (x-for, links, structured try/catch DSL sugar).
- Prefer “fail safe and early”:
  - Referencing a missing state field is a **compile-time error**.
  - Proxy truthiness (e.g. `if state.loading:`) is an **immediate exception**.
  - Callable → URL resolution ambiguity is a **hard error**.

### TDD-first (assumed workflow for every milestone)

For each milestone:
1. Write tests that specify the new behavior.
2. Implement the minimum code to pass.
3. Refactor only if needed, without changing behavior.

Suggested test categories:
- Unit tests: expression compilation, attribute rendering, action compilation.
- Integration tests: FastAPI `TestClient` SSR responses, route registration, RPC endpoint resolution.
- “Golden” HTML tests (snapshot-ish): compare generated HTML strings for key pages.

---

## Milestone 0: Repository foundation (minimum)

**Goal**: Make the project runnable and testable so we can iterate quickly.

**TDD tasks**
- Add a test runner setup (recommended: `pytest`).
- Add a minimal package surface so `import mustwebui` works.
- Decide whether a CLI is real scope; if not, adjust/remove `project.scripts` in `pyproject.toml`.

**Acceptance**
- Tests run (even if only a smoke test).
- `python -c "import mustwebui"` succeeds.

---

## Milestone 1: SSR “Hello” (no state, no DSL required yet)

**Goal**: The smallest end-to-end vertical slice: register a page and return HTML.

**Spec coverage**
- Page registration + SSR flow: docs/spec-architecture.md

**TDD tasks**
- Integration test: create a FastAPI app, register `@ui.page("/")`, and assert `GET /` returns 200 + expected HTML body.
- Implement `MustWebUI(app)` and `@ui.page(path, state=...)` skeleton.

**Acceptance**
- `GET /` returns HTML from the page handler.

---

## Milestone 2: XSS-safe initial state embedding

**Goal**: Embed initial state as JSON safely in SSR output.

**Spec coverage**
- State embedding requirements: docs/spec-security-ops.md
- Artifact contract: docs/spec-architecture.md

**TDD tasks**
- Unit test: state JSON is embedded in `<script type="application/json" id="__mustwebui_state">...</script>`.
- Security test: state containing `"</script>"`, `<`, `>`, `&`, and U+2028/U+2029 does not break HTML.
- Implement initial state creation from Pydantic defaults.

**Acceptance**
- SSR output includes a safe state script tag; the HTML remains valid with adversarial strings.

---

## Milestone 3: State Proxy (Expr) minimum

**Goal**: `state.x` is not a Python value; it’s a JS expression placeholder.

**Spec coverage**
- State Proxy / Expr semantics: docs/spec-state-proxy.md

**TDD tasks**
- Unit tests:
  - `state.name` compiles to `name`.
  - `state.user.email` compiles to `user.email`.
  - Missing fields raise a clear compile-time error.
  - Truthiness (`bool(expr)` / `if expr`) raises immediately.
  - Operator compilation for the initial set: `+`, `-`, `==` (→ `===`), `>=`, `and` (→ `&&`), `or` (→ `||`), `not` (→ `!`).
  - Literal normalization: `True/False/None` → `true/false/null`.
- Implement `Expr` + proxy generation for a declared Pydantic state model.

**Acceptance**
- Nested paths compile correctly; invalid references fail fast with actionable errors.

---

## Milestone 4: DSL node tree + `ml.render()` (static HTML first)

**Goal**: Build HTML structure in Python without manual HTML authoring.

**Spec coverage**
- DSL builder + context semantics: docs/spec-dsl.md

**TDD tasks**
- Unit tests:
  - Context nesting creates correct parent/child structure.
  - `class_name` → `class`, `attrs` → raw attributes.
  - `ml.render()` produces valid, deterministic HTML.
- Implement a minimal node model (elements + text nodes) and a builder (`ml`).

**Acceptance**
- A simple tree (`div` + `span`) renders to valid HTML.

---

## Milestone 5: Alpine bindings (x-data / x-text / x-model / x-show)

**Goal**: Local reactivity works without network calls.

**Spec coverage**
- Local reactivity: docs/spec-architecture.md
- Rendering rules: docs/spec-dsl.md
- Component contracts: docs/component-catalog.md

**TDD tasks**
- Unit tests (HTML generation):
  - `ml.text(expr)` emits `x-text="..."`.
  - Mixed text parts emit a concatenated JS expression.
  - `ml.input(state.name)` emits `x-model="name"`.
  - `show_if=expr` emits `x-show="..."` (optional: default `display:none` to avoid flicker).
- Integration test: SSR includes `x-data` init code that reads the state script tag.

**Acceptance**
- Generated HTML includes correct Alpine directives for text, inputs, and conditional display.

---

## Milestone 6: Tailwind defaults (preset + document shell)

**Goal**: “Battery-included styling” with a minimal, neutral default UI.

**Spec coverage**
- Preset + shell requirements: docs/spec-architecture.md
- Default component classes: docs/component-catalog.md
- Delivery constraints: docs/spec-security-ops.md

**TDD tasks**
- Unit tests:
  - Default classes are present for `button`, `input`, `card`, `checkbox`, `select`, `textarea` under `ui_preset="tailwind"`.
  - `class_name` merges by appending after defaults.
  - `ui_preset="none"` disables default classes.
- Integration test: full-document mode includes the default shell structure and classes:
  - `body`: `min-h-screen bg-gray-50 text-gray-900 antialiased`
  - `main`: `mx-auto w-full max-w-4xl p-6`

**Acceptance**
- A demo page looks acceptable with zero user CSS.

---

## Milestone 7: Actions (btn.set only) → working `@click`

**Goal**: Declaratively collect actions and compile them into an event handler.

**Spec coverage**
- Action model: docs/spec-rpc-actions.md
- Button + action API: docs/component-catalog.md

**TDD tasks**
- Unit tests:
  - `with ml.button(...) as btn: btn.set(state.x, 1)` produces a `<button ... @click="...">`.
  - Assignments compile to valid JS statements.
- Implement `ButtonBuilder` as a context manager that records actions.

**Acceptance**
- Clicking toggles state and updates `x-text/x-show`-driven UI.

---

## Milestone 8: Typed RPC (btn.call) minimum

**Goal**: Callable→URL resolution + mixed payload compilation + ResponseProxy.

**Spec coverage**
- Endpoint resolution: docs/spec-rpc-actions.md
- Payload compilation: docs/spec-rpc-actions.md
- ResponseProxy typing: docs/spec-rpc-actions.md

**TDD tasks**
- Unit tests:
  - Callable→URL resolves deterministically via `app.routes` and `route.endpoint is func`.
  - Ambiguity and “not found” raise clear errors.
  - Payload from Pydantic model/dict with literals + Expr compiles to a JS object expression.
  - ResponseProxy field access compiles to `res.field`.
- Integration test: generated handler calls `$api("/path", payload)`.

**Acceptance**
- A button click issues an RPC (at least in compiled JS) and applies response fields to state via subsequent `btn.set`.

---

## Milestone 9: Async handler + `try/finally` for cleanup

**Goal**: Ensure UI state (e.g. loading flags) cannot get stuck on RPC failure.

**Spec coverage**
- Cleanup requirement: docs/spec-rpc-actions.md
- Ops guidance: docs/spec-security-ops.md

**TDD tasks**
- Unit tests:
  - When actions include RPC and implied cleanup, handler is `async` and wrapped in `try/finally`.
- Implement minimal cleanup detection (start small):
  - If a button sets `loading=true` and later sets `loading=false`, wrap the RPC portion in `try/finally`.

**Acceptance**
- Compiled JS always executes the “cleanup” assignment in `finally`.

---

## Milestone 10: Runtime `$api` + dependency delivery (default: self-hosted)

**Goal**: Provide a tiny runtime for fetch + JSON + errors, compatible with CSP-conscious defaults.

**Spec coverage**
- `$api` contract: docs/spec-rpc-actions.md
- Dependency delivery: docs/spec-security-ops.md

**TDD tasks**
- Integration tests:
  - Static assets are served from a fixed prefix (e.g. `/_mustwebui/...`).
  - Full-document output references self-hosted assets by default.
  - SSR responses include conservative caching headers (e.g. `Cache-Control: no-store`) by default or configuration.
- Unit tests (runtime string generation):
  - `$api` sends JSON, rejects non-2xx, distinguishes parse failures.
- Implement a minimal runtime JS file (or inline minimal script if you choose; keep CSP implications in mind).

**Acceptance**
- Pages can call `$api` on same-origin successfully (when wired with a sample FastAPI endpoint).

---

## Milestone 11: Attribute binding rules (bindable attrs)

**Goal**: Implement the `attrs` + Expr binding rules defined in the DSL spec.

**Spec coverage**
- Attribute rules: docs/spec-dsl.md

**TDD tasks**
- Unit tests:
  - Bindable attrs (e.g. `disabled`, `value`, `min/max/step`, etc.) become bound attributes when value is Expr: `:disabled="..."`.
  - Keys that already start with `:` or `x-bind:` are emitted as-is.
  - Non-bindable attrs (`class`, `id`, `data-*`, `aria-*`) with Expr are stringified and emitted statically (no binding).

**Acceptance**
- `disable_if=expr` reliably emits `:disabled="..."` and works with Alpine.

---

## Milestone 12: State serialization policy (JSON-compat checks)

**Goal**: Guarantee client state is JSON-compatible and fail early with clear errors.

**Spec coverage**
- JSON-compat policy: docs/spec-state-proxy.md

**TDD tasks**
- Unit tests:
  - Strict mode (default): rejects non-JSON types with field path in the error.
  - Optional coercion mode: allows a small explicit set (datetime/date/time→ISO, UUID→str, Enum→value, Decimal→string).

**Acceptance**
- Non-JSON state fails fast and points to the exact offending field.

---

## Appendix: Deferred (phase 2+)

These are explicitly optional / phase-2 items and should not block the first end-to-end demo:

- Index access (`state.items[0]`) and map access.
- `ml.for_each` / `x-for`.
- `ml.link` (simple `<a>` can be added when needed).
- Structured `try_/catch_/finally_` DSL sugar (start with implicit cleanup + `try/finally`).
- Class token de-duplication (ordering and “user tokens last” is more important initially).

---

## Target demo (integration acceptance)

Once milestones 1–10 are complete, the README counter example (name + count + loading + typed RPC) should work as the primary integration acceptance:

- `ml.text` / `ml.input` / `ml.button`
- `btn.set` / `btn.call`
- async handler with `try/finally`
- Tailwind defaults (no user CSS required)
