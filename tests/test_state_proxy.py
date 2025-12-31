from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from mustwebui import MarkupBuilder


class User(BaseModel):
    email: str = "user@example.com"


class DemoState(BaseModel):
    name: str = "Ada"
    count: int = 1
    loading: bool = False
    user: User = User()


def _state() -> tuple[MarkupBuilder, Any]:
    builder = MarkupBuilder(DemoState)
    return builder, builder.state


def test_paths_resolve() -> None:
    _, state = _state()
    assert str(state.name) == "name"
    assert str(state.user.email) == "user.email"


def test_missing_field_errors() -> None:
    _, state = _state()
    with pytest.raises(ValueError):
        _ = state.unknown


def test_truthiness_is_forbidden() -> None:
    _, state = _state()
    with pytest.raises(TypeError):
        bool(state.loading)
    with pytest.raises(TypeError):
        if state.loading:  # pragma: no cover - branch is not executed
            raise AssertionError


def test_operator_compilation() -> None:
    _, state = _state()
    assert str(state.count + 1) == "count + 1"
    assert str(state.count - 1) == "count - 1"
    assert str(state.count == 0) == "count === 0"
    assert str(state.count >= 2) == "count >= 2"
    assert str(state.loading & (state.count >= 1)) == "loading && (count >= 1)"
    assert str(state.loading | (state.count >= 1)) == "loading || (count >= 1)"
    assert str(~state.loading) == "!loading"


def test_literal_normalization() -> None:
    _, state = _state()
    assert str(state.loading | True) == "loading || true"
    assert str(state.loading & False) == "loading && false"
    assert str(state.name == None) == "name === null"  # noqa: E711
