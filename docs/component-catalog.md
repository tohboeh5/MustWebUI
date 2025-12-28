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

## Core text & layout

### `ml.text(*parts, class_name=None, show_if=None, attrs=None)`

- Purpose: render text content.
- `parts`: mixture of `str | Literal | Expr`.

Generated output:
- If `parts` is a single Expr → `<span x-text="<expr>"></span>`
- If `parts` mixes literals/Expr → `<span x-text="<concat-expr>"></span>`
- If `show_if` is provided → add `x-show="<show_if>"`.

### `ml.div(*children, class_name=None, show_if=None, attrs=None)`

- Purpose: container.
- Children can be nested DSL nodes.

### `ml.span(*children, ...)`

- Purpose: inline container.

### `ml.card(title: str | None = None, class_name=None, attrs=None)` (context manager)

- Purpose: a convenience container for demos.
- Output SHOULD be a `div` with a predictable structure, but styling is left to user CSS.

## Form inputs

### `ml.input(model: StateExpr, *, type="text", placeholder=None, disable_if=None, class_name=None, attrs=None)`

- Purpose: bind an input to state.

Generated output:
- MUST include `x-model="<state-path>"`.
- If `disable_if` is provided → `:disabled="<expr>"`.

### `ml.checkbox(model: StateExpr, *, disable_if=None, ...)`

- Purpose: boolean binding.
- MUST use `x-model`.

### `ml.select(model: StateExpr, *, options: list[tuple[str, str|Literal|Expr]] | None = None, disable_if=None, ...)`

- Purpose: select binding.
- Options MAY include Expr labels/values, but simplest form is literal.

### `ml.textarea(model: StateExpr, *, disable_if=None, ...)`

- Purpose: multi-line binding.

## Buttons & actions

### `ml.button(label: str | Expr, *, disable_if=None, class_name=None, attrs=None) -> ButtonBuilder` (context manager)

- Purpose: declare a click handler (Actions).
- `ButtonBuilder` collects Actions like `set()` and `call()`.

Generated output:
- MUST produce a `<button>`.
- MUST generate `@click="<async-handler>"` when actions exist.
- If `disable_if` is provided → `:disabled="<expr>"`.

#### `ButtonBuilder` (actions)

Within the `with ml.button(...) as btn:` block, the builder SHOULD provide:

- `btn.set(target: StateExpr, value: Expr | Literal) -> None`
  - Compiles to an assignment (e.g. `loading = true;`).

- `btn.call(func: Callable, *, data: BaseModel | dict, method: str = "POST") -> ResponseProxy`
  - Compiles to `const res = await $api(url, payload);` and returns a ResponseProxy that can be referenced in later actions.

- `btn.finally_(fn: Callable[[], None] | None = None)` (optional)
  - Allows structured cleanup. In the initial version, this may be internal-only and exposed later.

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

## What’s explicitly not in the initial set

- Complex widgets (date pickers, rich text editors)
- Client-side router
- Component theming system
