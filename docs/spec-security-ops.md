# Specification: Security / Operations

MustWebUI generates HTML and JavaScript. Security requirements must be explicit from day one.

## 1. XSS

### 1.1 Initial state embedding

Requirements:
- Initial state MUST be embedded using an XSS-safe encoding strategy.
- The implementation MUST account for problematic sequences/characters such as `</script>`, `<`, `>`, `&`, and Unicode line separators (U+2028/U+2029).

Recommended approach:
- Embed JSON into a non-executing script tag:
	- `<script type="application/json" id="__mustwebui_state">{...}</script>`
- Parse via `JSON.parse(document.getElementById(...).textContent)`.

Rationale:
- Attributes are easier to break accidentally; script-tag JSON is simpler to reason about.

### 1.2 Text insertion

Requirements:
- Prefer `x-text` (textContent) over `x-html`.
- `ml.text()` MUST default to non-HTML interpretation.

## 2. CSRF

Assumption:
- Typed RPC uses JSON POST.

Requirements:
- If cookie-based auth is used, CSRF protection is required.

Recommended:
- SameSite cookies + CSRF token in a header.
- The runtime `$api` helper SHOULD allow sending `X-CSRF-Token`.

## 3. Authentication (Authn) / Authorization (Authz)

Requirements:
- MustWebUI MUST NOT mandate a specific auth system.
- MustWebUI pages and API endpoints MUST be protectable using standard FastAPI dependencies.

Recommendation:
- Apply the same authorization policy to SSR pages and their corresponding RPC endpoints.

## 4. CORS

Requirements:
- Same-origin is the default.
- If cross-origin is required, follow FastAPI CORS middleware configuration.

## 5. Caching

### 5.1 SSR responses

Requirements:
- Pages containing user-specific data MUST have conservative caching headers.

Recommended:
- Auth-required pages: `Cache-Control: no-store`.
- Public pages: consider ETag/Last-Modified.

### 5.2 RPC responses

Requirements:
- State-changing endpoints SHOULD NOT be cacheable.

## 6. Errors & observability

Requirements:
- Log enough data to debug failed RPC calls (status, error category, correlation id).
- Server-side error handling follows FastAPI best practices.

Recommended:
- `$api` helper MAY send `X-Request-Id`.
- Client-side must not get stuck in a “loading” state (use `try/finally`).

## 7. Performance

Requirements:
- Generated HTML/JS MUST be minimal.
- Avoid producing huge inline event handlers.

Recommended:
- Extract shared logic into a small runtime helper when handlers become large.
- Keep `$api` as a thin `fetch` + JSON wrapper.

## 8. Dependency delivery

Requirements:
- Alpine.js MUST be usable via CDN or self-hosting.

Recommended:
- Pin Alpine version in production (e.g. `alpinejs@3.15.3`).
- If using CSP, explicitly decide on an inline-script strategy.
