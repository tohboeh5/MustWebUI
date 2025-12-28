# Specification: DSL (ml.*)

## 1. Goal

Provide a Python-only way to declare UI.

- No manual HTML authoring required.
- State proxies (Expr) can be embedded naturally.
- Output is plain SSR HTML + Alpine directives (no hydration step).

## 2. Model

### 2.1 Builder

`ml` is a builder that constructs a node tree.

Examples:

- `ml.text(...)`
- `ml.input(state.name)`
- `with ml.button(...): ...`
- `ml.div(...)` / `ml.span(...)`

The concrete list of supported components is defined in:

- [component-catalog.md](component-catalog.md)

### 2.2 Context management

Context managers represent parent/child nesting:

- `with ml.card("Title"):`
- `with ml.button("Save") as btn:`

Requirements:
- Entering a context MUST make subsequent nodes children of that context.
- Exiting a context MUST restore the previous parent.

## 3. Minimal API contract

The initial implementation SHOULD cover at least:

- text nodes with Expr support
- inputs with `x-model`
- buttons with Actions compiled into `@click`
- conditional display (`x-show`)

See [component-catalog.md](component-catalog.md) for signatures.

## 4. Attribute rules

Requirements:
- `class_name` maps to `class`.
- `attrs` keys/values map to raw HTML attributes.
- When an attribute value is an Expr and is bindable, it MUST be emitted as a bound attribute (e.g. `:disabled`).

## 5. Rendering

- `ml.render() -> str`

Requirements:
- Rendering MUST produce valid HTML.
- Rendering MUST not require client-side hydration.

Output modes (configurable):
- fragment-only (embed into a host template)
- full HTML document (includes Alpine and runtime helper)

## 6. Extensibility rules

- Start small; expand only when a real UI requires it.
- Styling is user-controlled (e.g. Tailwind classes via `class_name=`).
- Avoid introducing a new theming/design system in MustWebUI.
