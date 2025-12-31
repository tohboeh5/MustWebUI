from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from mustwebui import MustWebUI


class HelloState(BaseModel):
    message: str = "Hello MustWebUI"


def test_ssr_hello_page() -> None:
    app = FastAPI()
    ui = MustWebUI(app)

    @ui.page("/", state=HelloState)
    def home(ml, state) -> str:
        ml.text(state.message)
        return ml.render()

    res = TestClient(app).get("/")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text
    assert 'x-data="__mustwebui_init()"' in res.text
    assert 'x-text="message"' in res.text


class DangerousState(BaseModel):
    payload: str = "</script><img src=x onerror=alert(1)>\u2028\u2029"


def test_state_embedding_is_safely_escaped() -> None:
    app = FastAPI()
    ui = MustWebUI(app)

    @ui.page("/danger", state=DangerousState)
    def danger(ml, state) -> str:
        ml.text(state.payload)
        return ml.render()

    res = TestClient(app).get("/danger")
    assert res.status_code == 200
    assert '<script type="application/json" id="__mustwebui_state">' in res.text
    assert "\\u003c\\/script\\u003e" in res.text
    assert "</script><img" not in res.text
    assert "\\u2028" in res.text
    assert "\\u2029" in res.text
