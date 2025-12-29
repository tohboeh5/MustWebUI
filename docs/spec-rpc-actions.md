# Specification: Typed RPC / Actions

## 1. Goal

MustWebUI MUST allow UI code to invoke server endpoints without writing string URLs.

The canonical form is:

- `btn.call(python_function, data=PydanticModel(...))`

This single call implies:

- endpoint resolution (`Callable → URL`)
- request payload compilation (mix of literals + Expr)
- typed response access (a response proxy)

## 2. Action model

An **Action** is a declarative instruction that will run in the browser when an event fires (e.g. a button click). Actions are collected at Python runtime but MUST NOT perform side effects.

Minimal actions:

- `btn.set(target: StateExpr, value: Expr | Literal)`
- `btn.call(func: Callable, *, data: BaseModel | dict, method: str = "POST") -> ResponseProxy`

Optional (for structured control flow):

- `btn.try_()` / `btn.catch_()` / `btn.finally_()` (or syntactic sugar)

Requirements:
- MustWebUI MUST store actions as an **action tree**.
- MustWebUI MUST transpile the action tree into an Alpine event handler expression.

## 3. Endpoint resolution (function → URL)

MustWebUI resolves a Python function object to a FastAPI route.

Initial scope (recommended):
- Only `POST` + JSON body
- Only routes registered on the same FastAPI app instance

Resolution algorithm (concrete):

1) Iterate `app.routes` and consider only `APIRoute`-like routes.
2) Match candidates where `route.endpoint is func`.
3) If multiple candidates remain:
   - Prefer exact method match (default `POST`).
   - If still ambiguous, raise an error that lists candidate paths/methods.
4) If no candidate exists, raise an error.

Requirements:
- Resolution MUST be deterministic.
- Ambiguity MUST be a hard error.

## 4. Request payload compilation

### 4.1 Mixed literals and expressions

`data=IncrementIn(amount=1, current=state.count)` may contain both literals and Expr.

Compilation rules:
- Literals become JSON literals.
- Expr becomes a JS expression reference at the same object location.

Target JS shape example:

```js
{ amount: 1, current: count }
```

Implementation note:
- The compiler MAY build the payload as a JS object expression string rather than “JSON + patches”.

### 4.2 Client-side validation (best-effort)

Server-side validation is authoritative (FastAPI/Pydantic).

Client-side compilation SHOULD catch:
- missing required fields (for literal-only payload parts)
- obviously invalid shapes (e.g. passing a list where object is expected)

## 5. Response typing and ResponseProxy

`btn.call(...)` returns a **ResponseProxy** representing the JSON response.

Example:

- `res = btn.call(increment, data=...)`
- `btn.set(state.count, res.new_count)`

Requirements:
- MustWebUI MUST determine the response model type for `func`.
- `res.some_field` MUST compile into `res.some_field` in JS (i.e. property access on the response object).

Concrete response-model inference rules (initial set):

1) If the FastAPI route defines `response_model`, use it.
2) Else, if the endpoint has a return type annotation that is a Pydantic model, use it.
3) Else, treat the response as untyped JSON (ResponseProxy still exists, but no field-level validation).

If a field is accessed that is not present in the inferred response model, MustWebUI SHOULD raise an error at compile time.

## 6. Optimistic UI and structured cleanup

MustWebUI MUST support optimistic local state updates before and after RPC.

Example pattern:

- set `loading = true` before RPC
- `finally` set `loading = false`

Requirement:
- When actions imply cleanup, MustWebUI MUST generate `try/finally` so UI state cannot get stuck.

## 7. Error handling (initial semantics)

The runtime helper (e.g. `$api`) MUST distinguish at least:

- network failures (fetch rejects)
- HTTP errors (non-2xx)
- JSON parse errors

### 7.1 Runtime helper contract

MustWebUI SHOULD ship a tiny runtime helper with the following contract:

```js
// url: string
// payload: plain object
// returns: parsed JSON on success
async function $api(url, payload) {
  // Implementation-defined
}
```

Requirements:
- `$api` MUST send `Content-Type: application/json`.
- `$api` MUST treat non-2xx as an error.
- `$api` MUST return parsed JSON for 2xx responses.

Default shape (for the built-in `$api` helper) SHOULD be a tagged union discriminated by `kind`:
- `{ kind: 'network' | 'http' | 'parse', status?: number, message?: string }`

This shape is RECOMMENDED, not required:
- Host integrations MAY use a different error shape, add extra fields, or introduce additional `kind` values, as long as they document the contract.
- Callers that want to be portable across implementations MUST NOT assume this error shape is present unless explicitly advertised by the host.

Initial recommended behavior:
- Always run `finally` actions.
- Report errors via `console.error(...)`.

Deferred feature:
- user-provided `on_error=...` blocks.

## 8. Generated JS (reference)

```js
loading = true;
try {
  const res = await $api('/api/increment', { amount: 1, current: count });
  count = res.new_count;
} finally {
  loading = false;
}
```
