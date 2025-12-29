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

## 3. Authentication / Authorization (Authn / Authz)

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

- Tailwind CSS MUST be deliverable in a secure, CSP-compatible way.

### 8.1 Delivery principles (normative)

Requirements:
- Production defaults MUST NOT require relaxing CSP to include `unsafe-inline` or `unsafe-eval` solely for dependency loading.
- Dependencies MUST be pinnable to a specific version (or content hash) to avoid silent supply-chain changes.
- The default delivery SHOULD be same-origin (self-hosted) for both JS and CSS.

### 8.2 Self-hosted (recommended default)

Recommended:
- Serve Alpine.js and the MustWebUI runtime helper from the same origin as the app.
- Serve a prebuilt Tailwind CSS file from the same origin as the app.
- Include assets using `<script src="..." defer></script>` and `<link rel="stylesheet" href="...">`.

Operational guidance:
- Use cache-busting filenames (e.g. `app.<hash>.css`, `vendor.<hash>.js`).
- Use long-lived caching for hashed assets (e.g. `Cache-Control: public, max-age=31536000, immutable`).

### 8.3 CDN (allowed, explicit opt-in)

Requirements:
- CDN usage MUST be an explicit configuration choice.
- CDN URLs MUST be versioned (no floating tags).

Recommended:
- Use Subresource Integrity (SRI) via `integrity="..."` and `crossorigin="anonymous"` for CDN-loaded assets.
- Prefer reputable CDNs and minimize third-party origins.

### 8.4 CSP notes (Alpine.js)

Alpine.js commonly relies on dynamic code execution in its standard build.

Recommendations:
- If strict CSP is required, prefer the Alpine "CSP build" (or equivalent approach) so that pages do not need `script-src 'unsafe-eval'`.
- Document the required CSP for the chosen Alpine delivery in the host integration.

### 8.5 Tailwind CSS notes

Requirements:
- MustWebUI MUST NOT depend on browser-side Tailwind JIT/"play CDN" for production behavior.

Recommended:
- Generate Tailwind CSS at build time and ship the resulting static CSS file.
