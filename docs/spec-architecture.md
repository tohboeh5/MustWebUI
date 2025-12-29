# Specification: Architecture

## 1. Goal

MustWebUI is designed as a UI framework (and effectively a compiler) built around FastAPI + Pydantic, with three non-negotiable properties:

- **SSR-first**: fast initial paint from server-rendered HTML.
- **Lightweight reactivity**: Alpine.js handles local updates (input binding, conditional display) without network calls.
- **Typed RPC**: UI code calls server endpoints via **Python function objects** and **Pydantic models** (not string URLs).

Additionally (UX requirement):

- **Battery-included styling**: the generated HTML MUST have a good default UI without requiring users to author CSS. The default styling MUST be Tailwind CSS-based.

## 2. System components

- **FastAPI (server)**
  - hosts normal API routes.
  - hosts MustWebUI pages (SSR) as regular HTTP routes.
  - MUST expose enough routing metadata so MustWebUI can resolve `Callable → URL`.

- **MustWebUI (compiler/runtime)**
  - registers pages via `@ui.page(path, state=...)`.
  - converts DSL (`ml.*`) + Actions (`btn.*`) into:
    - SSR HTML
    - Alpine directives/expressions (`x-data`, `x-model`, `x-text`, `x-show`, event handlers)
    - a tiny runtime helper (e.g. `$api`) for fetch + JSON.
  - serializes initial State safely.

- **Tailwind CSS (styling)**
  - MustWebUI MUST provide a Tailwind-based default styling preset for generated pages.
  - Users MUST be able to disable or replace this preset.

Component coverage for the initial version is listed in:
- [component-catalog.md](component-catalog.md)

- **Browser (Alpine.js)**
  - owns live state in `x-data`.
  - updates DOM via Alpine v3 directives.
  - executes async handlers that call `$api(...)` and apply results back into state.

## 3. Artifact contract (what MustWebUI generates)

For any page, MustWebUI MUST be able to generate:

- **HTML structure** (plain HTML tags)
- **Styling hooks**
  - When generating a full HTML document, MustWebUI MUST include a Tailwind CSS-based stylesheet by default.
  - Components MUST emit sensible default classes under the Tailwind preset (see [component-catalog.md](component-catalog.md)).
- **Document shell (full-document mode)**
  - When generating a full HTML document with `ui_preset="tailwind"`, MustWebUI MUST wrap the page content in a minimal, good-looking default layout.
  - This shell MUST NOT add application-specific UI (no nav, no menus, no extra “chrome”). It is only responsible for baseline spacing, background, and readability.
  - In fragment-only mode, MustWebUI MUST NOT add any shell; the host template owns the outer layout.
- **Initial state** (JSON) embedded in an XSS-safe way (see [spec-security-ops.md](spec-security-ops.md))
- **Alpine bindings**
  - `x-data` creation that points at the initial state
  - `x-model` for inputs
  - `x-text` for text
  - `x-show` for conditional display
- **Event handlers**
  - `@click` etc containing an `async` expression when actions include RPC
  - `try/finally` when actions include cleanup (e.g. loading flags)

### 3.1 Styling delivery modes (Tailwind)

MustWebUI SHOULD support at least two styling delivery strategies:

- **Self-hosted CSS (recommended)**: ship a prebuilt Tailwind CSS file as a static asset served from the same origin.
- **CDN (development-friendly)**: allow including Tailwind via a versioned external URL when explicitly configured.

Requirements:
- The default MUST be secure and CSP-friendly; detailed guidance lives in [spec-security-ops.md](spec-security-ops.md).
- Styling MUST NOT require users to author a base HTML template to get decent visuals.

### 3.2 Default document shell (Tailwind)

This section defines the minimum “battery-included” page-level layout for full-document output.

Requirements:
- The shell MUST be present by default in full-document mode when `ui_preset="tailwind"`.
- The shell MUST be removable via configuration.
- The shell MUST be implemented purely via HTML structure + Tailwind utility classes (no extra JS behavior).

Recommended reference structure (non-normative HTML shape, normative intent):
- `html` / `head` include required scripts/styles.
- `body` provides baseline background and text defaults.
- A single `main` (or equivalent wrapper) constrains width and adds padding.

Recommended default classes (Tailwind preset):
- `body`: `min-h-screen bg-gray-50 text-gray-900 antialiased`
- `main` wrapper: `mx-auto w-full max-w-4xl p-6`

Rationale:
- This makes the component catalog defaults (cards/inputs/buttons) look acceptable without requiring users to write a template.
- It keeps “layout” responsibility separate from per-component defaults.

## 4. Request/response flow

### 4.1 SSR (initial render)

1. Browser requests `GET /`.
2. FastAPI executes the registered page handler.
3. MustWebUI returns HTML that includes:
   - initial state JSON
   - Alpine runtime setup
   - compiled event handlers.

Requirements:
- Initial state MUST come from the state model's defaults / factories.
- State embedding MUST be XSS-safe.

### 4.2 Local reactivity (no network)

- input: `x-model` updates state instantly.
- visibility: `x-show` toggles instantly.
- text: `x-text` reads state instantly.

MustWebUI MUST compile `state.some_field` (a proxy) into the correct JS identifier/path.

### 4.3 Typed RPC (network)

1. User triggers an event.
2. Alpine executes the compiled handler.
3. Handler calls `$api(resolved_url, payload)`.
4. Response JSON is applied to state (explicit `btn.set`), updating the UI.

Requirements:
- Must resolve **function object → URL** deterministically.
- Payload/response MUST follow Pydantic models declared on the server.

## 5. Page registration

### 5.1 API surface (minimal)

- `ui = MustWebUI(app: FastAPI, *, config: ... = ...)`
- `@ui.page(path: str, *, state: type[BaseModel])`

Page handler signature (minimal):

- `def page(ml, state: StateModel) -> str`

### 5.2 Responsibility of a page handler

The page handler is not “rendering HTML manually”. It:

- builds a node tree via the DSL
- embeds State proxies (Expr)
- declares Actions (instruction sequences)

and then returns `ml.render()`.

### 5.3 Config: UI preset (minimal)

This spec assumes a minimal configuration surface to control built-in styling:

- `ui_preset: str` (default: `"tailwind"`)
  - `"tailwind"`: enable Tailwind-based defaults.
  - `"none"`: no default classes and no CSS inclusion.
- `include_tailwind: bool` (default: `True` when `ui_preset="tailwind"` and generating a full document)
- `tailwind_delivery: str` (default: `"self_hosted"`)
  - `"self_hosted"` (recommended)
  - `"cdn"` (explicit opt-in)

Additional minimal config semantics for the full-document shell:

- `document_shell: str` (default: `"default"`)
  - `"default"`: include the built-in shell (recommended).
  - `"none"`: emit no outer layout wrapper.

If a host wants a custom shell, it SHOULD use fragment-only mode and supply its own HTML template.

The exact config type is implementation-defined, but these semantics MUST be achievable.


## 6. Compatibility / constraints

- Alpine.js v3
- Standard FastAPI routing
- No browser-side Python execution

## 7. Sequence diagram (reference)

```mermaid
sequenceDiagram
    participant User
    participant Alpine (Browser)
    participant FastAPI (Server)

    Note over User, FastAPI: 1) SSR
    User->>FastAPI: GET /
    FastAPI->>Alpine: HTML + initial state JSON (x-data)

    Note over User, Alpine: 2) Local reactivity
    User->>Alpine: input / toggle
    Alpine->>Alpine: x-model / x-show (no network)

    Note over User, FastAPI: 3) Typed RPC
    User->>Alpine: click
    Alpine->>FastAPI: fetch(JSON)
    FastAPI->>Alpine: JSON patch/result
    Alpine->>Alpine: update state -> re-render
```
