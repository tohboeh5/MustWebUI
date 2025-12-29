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
- When an attribute value is an Expr and the attribute is *bindable*, it MUST be emitted as a bound attribute (e.g. `:disabled`).

Explicit bindings (escape hatch):
- If an `attrs` key is already an Alpine/Vue-style binding key (e.g. starts with `:` or `x-bind:`), MustWebUI MUST emit it as-is.
	- This allows advanced customization such as `attrs={":class": <expr>}` without expanding the default bindable-attribute set.

An attribute is considered *bindable* when at least one of the following is true:
- It is a standard boolean or stateful HTML attribute whose semantics depend on runtime state (for example: `disabled`, `readonly`, `required`, `checked`, `selected`, `hidden`).
- It is a value-like attribute on form controls where live state updates are expected (for example: `value`, `min`, `max`, `step`).
- It is explicitly marked as bindable in the component definitions in [component-catalog.md](component-catalog.md).

When an Expr is used as the value of a non-bindable attribute (for example: `class`, `id`, `name`, `style`, `data-*`, `aria-*`), the Expr MUST be evaluated to a string and emitted as a static attribute value (i.e. without a binding prefix such as `:`).

## 5. Rendering

- `ml.render() -> str`

Requirements:
- Rendering MUST produce valid HTML.
- Rendering MUST not require client-side hydration.

Output modes (configurable):
- fragment-only (embed into a host template)
- full HTML document (includes Alpine and runtime helper, and Tailwind CSS by default)

Responsibility split:
- In fragment-only mode, MustWebUI MUST emit only the page fragment (no `<html>`, no `<head>`, no default page layout wrapper).
- In full-document mode, MustWebUI MUST provide a minimal default document shell when `ui_preset="tailwind"`.
  - This shell can be disabled (see [spec-architecture.md](spec-architecture.md)).

## 6. Extensibility rules

- Start small; expand only when a real UI requires it.
- Styling is user-controlled (e.g. classes via `class_name=`), but MustWebUI MUST provide a battery-included default UI under a Tailwind preset.
- Avoid introducing a bespoke theming/design system beyond providing default utility-class presets (Tailwind) and a switch to disable/replace them.
