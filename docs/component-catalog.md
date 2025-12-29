# Component Catalog (ml.*)

This document lists the components MustWebUI is expected to provide in the initial implementation.

Scope note:
- These are **server-side builders** that produce SSR HTML + Alpine directives.
- “Component” here means a DSL entrypoint (e.g. `ml.button(...)`).

## Design rules

- Components MUST allow embedding **Expr** (state proxies) where reactive values are expected.
- Components MUST NOT execute side effects at Python runtime.
- Components SHOULD map cleanly to plain HTML and Alpine v3 directives.
- Components SHOULD keep the generated HTML minimal.

## Styling contract (battery-included Tailwind preset)

MustWebUI MUST provide a default UI that looks good without any user-authored CSS.

Requirements:
- Under the default preset (`ui_preset="tailwind"`), components MUST emit sensible Tailwind utility classes even when `class_name` is not provided.
- If `class_name` is provided, it MUST be merged (appended) with the default classes rather than replacing them.
- There MUST be a way to disable default classes entirely (e.g. `ui_preset="none"`).

Notes:
- The goal is not to introduce a new theme system; it is to ship a neutral, good-looking baseline.
- Class lists below are normative for the initial implementation and may be revised, but changes SHOULD be treated as a breaking UX change.

Page-level layout note:
- In full-document mode, the default Tailwind document shell provides baseline background and outer padding (see [spec-architecture.md](spec-architecture.md)).
- Components SHOULD NOT attempt to own page-level layout (e.g. `max-w-*` containers) by default; they should remain composable.

## Common types

- `Expr`: JS expression placeholder (from State Proxy, Response Proxy, or literal expressions).
- `StateExpr`: an Expr that points to a state location (e.g. `state.count`).
- `Literal`: Python literal serializable to JSON (str/int/float/bool/None/list/dict of same).

## Global attributes (available on most components)

Most components SHOULD accept:

- `class_name: str | None`
- `id: str | None`
- `attrs: dict[str, str | Expr] | None`

Rules:
- `attrs` keys map to raw HTML attributes.
- If an attribute value is `Expr`, it MUST be rendered as an Alpine-bound attribute when appropriate.
  - Example: `disabled` is typically `:disabled="<expr>"`.

Class merging rules (Tailwind preset):
- If the component has a default class string `DEFAULT`, and user passes `class_name=USER`:
  - Output MUST include `class="DEFAULT USER"`.
- The implementation MAY optionally de-duplicate tokens, but MUST preserve ordering such that user tokens come last.

## Core text & layout

### `ml.text(*parts, class_name=None, show_if=None, attrs=None)`

- Purpose: render text content.
- `parts`: mixture of `str | Literal | Expr`.

Generated output:
- If `parts` is a single Expr → `<span x-text="<expr>"></span>`
- If `parts` mixes literals/Expr → `<span x-text="<concat-expr>"></span>`
- If `show_if` is provided → add `x-show="<show_if>"`.

Default classes (Tailwind preset):
- If `class_name` is not provided, `ml.text(...)` SHOULD render with no extra classes by default.
  - Rationale: text is frequently embedded inline; forcing typography everywhere can be surprising.

### `ml.div(*children, class_name=None, show_if=None, attrs=None)`

- Purpose: container.
- Children can be nested DSL nodes.

Default classes (Tailwind preset):
- `ml.div(...)` SHOULD render with no extra classes by default.

### `ml.span(*children, ...)`

- Purpose: inline container.

### `ml.card(title: str | None = None, class_name=None, attrs=None)` (context manager)

- Purpose: a convenience container for demos.
- Output SHOULD be a `div` with a predictable structure.

Default structure (reference):
- Wrapper `div`
- Optional header area when `title` is provided
- Body area containing children

Default classes (Tailwind preset):
- Wrapper: `rounded-lg border border-gray-200 bg-white p-4 shadow-sm`
- Title: `mb-3 text-base font-semibold text-gray-900`
- Body: `space-y-3`

## Form inputs

### `ml.input(model: StateExpr, *, type="text", disable_if=None, placeholder=None, class_name=None, attrs=None)`

- Purpose: bind an input to state.

Generated output:
- MUST include `x-model="<state-path>"`.
- If `disable_if` is provided → `:disabled="<expr>"`.

Default classes (Tailwind preset):
- `block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm`
- Focus: `focus:border-gray-900 focus:ring-1 focus:ring-gray-900`
- Disabled: `disabled:cursor-not-allowed disabled:opacity-50`

### `ml.checkbox(model: StateExpr, *, disable_if=None, ...)`

- Purpose: boolean binding.
- MUST use `x-model`.

Default classes (Tailwind preset):
- `h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900`

### `ml.select(model: StateExpr, *, options: list[tuple[str, str|Literal|Expr]] | None = None, disable_if=None, ...)`

- Purpose: select binding.
- Options MAY include Expr labels/values, but simplest form is literal.

Default classes (Tailwind preset):
- `block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm`
- Focus/disabled same as `ml.input`

### `ml.textarea(model: StateExpr, *, disable_if=None, ...)`

- Purpose: multi-line binding.

Default classes (Tailwind preset):
- `block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm`
- Focus/disabled same as `ml.input`

## Buttons & actions

### `ml.button(label: str | Expr, *, disable_if=None, class_name=None, attrs=None) -> ButtonBuilder` (context manager)

- Purpose: declare a click handler (Actions).
- `ButtonBuilder` collects Actions like `set()` and `call()`.

Generated output:
- MUST produce a `<button>`.
- MUST generate `@click="<async-handler>"` when actions exist.
- If `disable_if` is provided → `:disabled="<expr>"`.

Default classes (Tailwind preset):
- Base: `inline-flex items-center justify-center rounded-md bg-gray-900 px-3 py-2 text-sm font-semibold text-white`
- Hover: `hover:bg-gray-800`
- Focus: `focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2`
- Disabled: `disabled:cursor-not-allowed disabled:opacity-50`

#### `ButtonBuilder` (actions)

Within the `with ml.button(...) as btn:` block, the builder SHOULD provide:

- `btn.set(target: StateExpr, value: Expr | Literal) -> None`
  - Compiles to an assignment (e.g. `loading = true;`).

- `btn.call(func: Callable, *, data: BaseModel | dict, method: str = "POST") -> ResponseProxy`
  - Compiles to `const res = await $api(url, payload);` and returns a ResponseProxy that can be referenced in later actions.

- `btn.finally_(fn: Callable[[], None] | None = None)` (optional / phase 2)
  - Allows structured cleanup. This is NOT required for the initial implementation and MAY be implemented or exposed in a later phase.

## Conditional rendering

### `show_if` on any element

- `show_if: Expr` renders as `x-show="<expr>"`.
- For flicker avoidance, implementation MAY emit `style="display: none;"` by default when `show_if` is set.

## Iteration (optional / phase 2)

### `ml.for_each(items: Expr, as_: str, render: Callable[[str], None])`

- Purpose: `x-for` lists.
- This is intentionally deferred unless needed.

## Navigation (optional / phase 2)

### `ml.link(label: str|Expr, href: str|Expr, ...)`

- Purpose: anchor.
- SPA navigation is out of scope; this is just `<a>`.

## Items explicitly excluded from the initial set

- Complex widgets (date pickers, rich text editors)
- Client-side router
- Component theming system (beyond the built-in Tailwind preset)
