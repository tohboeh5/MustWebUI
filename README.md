# MustWebUI

Type-safe Python → Reactive UI.

MustWebUI is a framework concept for building “fast-feeling” SSR web applications with client-side reactivity (not full SPA navigation) using **only Python**, powered by **FastAPI** + **Pydantic**, with **SSR + Alpine.js** for lightweight client-side reactivity.

In addition, MustWebUI is designed to be **battery-included for UI styling**: the HTML it generates SHOULD look good out of the box by shipping a Tailwind CSS-based default stylesheet and sensible default utility classes.

This repository currently focuses on the **specification and design**. Implementation will follow the docs.

## Why MustWebUI

- **Fast UX by default**: server-rendered HTML with instant client-side updates (Alpine directives).
- **Type-safe end-to-end**: Pydantic models define client state and RPC payloads.
- **API-first**: server logic stays standard FastAPI endpoints (usable beyond the UI).

## Core idea (high level)

1) SSR renders HTML and embeds initial state as JSON.
2) Alpine handles local interactions without network latency.
3) UI actions call typed FastAPI endpoints and patch state back into the UI.

## Example (concept)

```python
from fastapi import FastAPI
from pydantic import BaseModel
from mustwebui import MustWebUI

app = FastAPI()
ui = MustWebUI(app)

class AppState(BaseModel):
    name: str = "Guest"
    count: int = 0
    loading: bool = False

class IncrementIn(BaseModel):
    amount: int
    current: int

class IncrementOut(BaseModel):
    new_count: int

@app.post("/api/increment", response_model=IncrementOut)
async def increment(data: IncrementIn) -> IncrementOut:
    return IncrementOut(new_count=data.current + data.amount)

@ui.page("/", state=AppState)
def page(ml, state: AppState):
    ml.text("Hello, ", state.name, "!")
    with ml.button("Add 1", disable_if=state.loading) as btn:
        btn.set(state.loading, True)
        res = btn.call(increment, data=IncrementIn(amount=1, current=state.count))
        btn.set(state.count, res.new_count)
        btn.set(state.loading, False)
        # Note: MustWebUI compiles action sequences into JS with `try/finally` when cleanup is implied,
        # so UI state (e.g. loading flags) does not get stuck even if the RPC fails.
        # Conceptual output:
        #   loading = true;
        #   try { const res = await $api(...); count = res.new_count; }
        #   finally { loading = false; }
    return ml.render()
```

## Documentation

See the specification in [docs/README.md](docs/README.md).

## Status

Early stage / design-first. Feedback on the spec is welcome.
