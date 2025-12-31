from __future__ import annotations

from pydantic import BaseModel

from mustwebui import MarkupBuilder


class PageState(BaseModel):
    name: str = "Taro"
    loading: bool = False


def test_context_nesting() -> None:
    ml = MarkupBuilder(PageState)
    with ml.div(class_name="outer"):
        ml.text("Hello ")
        with ml.span(class_name="inner", show_if=ml.state.loading):
            ml.text(ml.state.name)
    html = ml.render()
    assert '<div class="outer">' in html
    assert 'x-show="loading"' in html
    assert '<span class="inner"' in html
    assert "x-text=\"'Hello '" in html
    assert 'x-text="name"' in html


def test_text_concatenation() -> None:
    ml = MarkupBuilder(PageState)
    ml.text("Hello, ", ml.state.name, "!")
    html = ml.render()
    assert "x-text=\"'Hello, ' + name + '!'\"" in html


def test_input_and_button_bindings() -> None:
    ml = MarkupBuilder(PageState)
    ml.input(ml.state.name, disable_if=ml.state.loading)
    ml.button("Save", disable_if=ml.state.loading)
    html = ml.render()
    assert 'x-model="name"' in html
    assert ':disabled="loading"' in html
    assert "<input" in html
    assert "<button" in html
