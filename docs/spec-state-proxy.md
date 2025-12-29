# Specification: State Proxy / Expression Trees

## 1. Why proxies exist

The core of MustWebUI is that `state.x` is **not a value** at Python runtime. It is a proxy that represents a **JavaScript expression**.

- At Python runtime, `state.count` MUST NOT evaluate to an `int`.
- During compilation, it MUST become a JS reference like `count` (or `user.email` for nested fields).

This is what enables “Python code → Alpine expressions” without writing JS by hand, while still using Pydantic models as a typed source of truth.

## 2. Reference semantics

### 2.1 Field access

- `state.name` → `Expr(path=["name"])` → JS: `name`
- `state.user.email` → `Expr(path=["user","email"])` → JS: `user.email`

Requirements:
- Every referenced field MUST exist on the declared Pydantic State model.
- If a field does not exist, MustWebUI MUST raise a clear error during compilation.

### 2.2 Index access (optional / phase 2)

- `state.items[0]` and `state.map["k"]` are out of scope for the initial version unless explicitly needed.

## 3. Expression operations

Proxies MUST support a minimal set of operations so that common UI expressions are ergonomic.

### 3.1 Supported operators (initial set)

- String concatenation:
  - `"Hello, " + state.name` → `'Hello, ' + name`
- Arithmetic:
  - `state.count + 1` → `count + 1`
  - `state.count - 1` → `count - 1`
- Comparisons:
  - `state.count == 0` → `count === 0`
  - `state.count >= 10` → `count >= 10`
- Boolean ops:
  - `state.loading and state.count > 0` → `loading && (count > 0)`
  - `not state.loading` → `!loading`

### 3.2 Normalization rules

MustWebUI MUST normalize Python values into JS:

- `True/False` → `true/false`
- `None` → `null`
- Strings MUST be JS-string-escaped.

If an operation cannot be represented safely, MustWebUI MUST fail fast with an explicit error.

### 3.3 Forbidden: truthiness in Python

Python will try to coerce objects to `bool` in conditions.

Requirement:
- `if state.loading:` MUST raise an exception (proxy cannot be truth-tested).

Correct usage is to pass the proxy as an expression:
- `ml.text("Loading", show_if=state.loading)`

## 4. State model → client state

### 4.1 Initial values

- Defaults and `default_factory` from the Pydantic model define the initial client state.

### 4.2 JSON-compatibility

Client state MUST be JSON-compatible.

For this spec, a **JSON-compatible value** is:
- A primitive: `bool`, a finite `int`/`float` number, `str`, or `null` (Python `None`).
- A list/array of JSON-compatible values.
- An object/dict with **string keys** and JSON-compatible values.

Any other Python value (for example `datetime`, `date`, `time`, `UUID`, `Decimal`,
`Enum`, or arbitrary custom classes) is considered a **non-JSON type**.

Policy options (configurable):
- **Strict mode (recommended)**:
  - Any non-JSON type in the state MUST cause a clear error during compilation/serialization.
  - No implicit coercion is allowed.
- **Coercion mode**:
  - A small, explicitly supported set of non-JSON types MAY be coerced:
    - `datetime` / `date` / `time` 92 ISO 8601 strings.
    - `UUID` 92 canonical string (e.g. `123e4567-e89b-12d3-a456-426614174000`).
    - `Enum` 92 the enums value (typically a `str` or `int`).
    - `Decimal` 92 decimal string representation.
  - Any other non-JSON type that is not in the supported set above MUST be rejected with a clear error, even in coercion mode.

### 4.3 Field naming

Default rule:
- Use the Pydantic field name as the JS key.

Optional rule:
- Prefer Pydantic `alias` as the JS key (recommended if you already use aliases).

## 5. How proxies map into the DSL

- `ml.text(state.name)` → a node that compiles to `x-text="name"`.
- `ml.text("Hello, ", state.name)` → compiles to a concatenated `x-text` expression.
- `ml.input(state.name)` → compiles to `x-model="name"`.
- `show_if=state.loading` → compiles to `x-show="loading"`.

## 6. Safe serialization into HTML

Initial state embedding MUST be XSS-safe.

Recommended:
- Embed JSON into `<script type="application/json" id="__mustwebui_state">...</script>`.
- Parse via `JSON.parse(el.textContent)`.

See [spec-security-ops.md](spec-security-ops.md).
