from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


def _js_string_literal(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f"'{escaped}'"


def _to_expr(value: Any) -> "Expr":
    if isinstance(value, Expr):
        return value
    if value is True:
        return Expr("true")
    if value is False:
        return Expr("false")
    if value is None:
        return Expr("null")
    if isinstance(value, str):
        return Expr(_js_string_literal(value))
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValueError("Non-finite numbers are not allowed in expressions")
        return Expr(str(value))
    raise TypeError(f"Unsupported expression literal: {type(value)!r}")


class Expr:
    def __init__(self, code: str):
        self.code = code

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.code

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Expr({self.code!r})"

    def __bool__(self) -> bool:
        raise TypeError("Expr objects cannot be evaluated for truthiness")

    def _wrap(self) -> str:
        if (self.code.startswith("'") and self.code.endswith("'")) or (
            self.code.startswith('"') and self.code.endswith('"')
        ):
            return self.code
        if " " in self.code or "&&" in self.code or "||" in self.code:
            return f"({self.code})"
        return self.code

    def __add__(self, other: Any) -> "Expr":
        right = _to_expr(other)
        return Expr(f"{self._wrap()} + {right._wrap()}")

    def __sub__(self, other: Any) -> "Expr":
        right = _to_expr(other)
        return Expr(f"{self._wrap()} - {right._wrap()}")

    def __eq__(self, other: Any) -> "Expr":  # type: ignore[override]
        right = _to_expr(other)
        return Expr(f"{self._wrap()} === {right._wrap()}")

    def __ge__(self, other: Any) -> "Expr":
        right = _to_expr(other)
        return Expr(f"{self._wrap()} >= {right._wrap()}")

    def __and__(self, other: Any) -> "Expr":
        right = _to_expr(other)
        return Expr(f"{self._wrap()} && {right._wrap()}")

    def __or__(self, other: Any) -> "Expr":
        right = _to_expr(other)
        return Expr(f"{self._wrap()} || {right._wrap()}")

    def __invert__(self) -> "Expr":
        return Expr(f"!{self._wrap()}")

    def not_(self) -> "Expr":
        return ~self


def _resolve_child_model(
    model: type[BaseModel], field_name: str, path: tuple[str, ...] = ()
) -> type[BaseModel] | None:
    model_fields = getattr(model, "model_fields", {})
    if field_name not in model_fields:
        path_str = ".".join(path + (field_name,))
        raise ValueError(f"Field '{path_str}' does not exist on state model")
    annotation = model_fields[field_name].annotation
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


class StateExpr(Expr):
    def __init__(self, model: type[BaseModel] | None, path: tuple[str, ...]):
        code = ".".join(path)
        super().__init__(code)
        self._model = model
        self._path = path

    def __getattr__(self, item: str) -> "StateExpr":
        if self._model is None:
            raise ValueError(
                f"Field '{'.'.join(self._path + (item,))}' does not exist on state model"
            )
        child_model = _resolve_child_model(self._model, item, self._path)
        return StateExpr(child_model, self._path + (item,))


class StateProxy:
    def __init__(self, model: type[BaseModel]):
        self._model = model

    def __getattr__(self, item: str) -> StateExpr:
        child_model = _resolve_child_model(self._model, item, ())
        return StateExpr(child_model, (item,))


def _escape_attr(value: str) -> str:
    return html.escape(value, quote=False)


def _render_attrs(attrs: Mapping[str, str]) -> str:
    if not attrs:
        return ""
    parts = [f'{key}="{_escape_attr(val)}"' for key, val in attrs.items()]
    return " " + " ".join(parts)


def _show_if_attrs(show_if: Any | None) -> MutableMapping[str, str]:
    data: MutableMapping[str, str] = {}
    if show_if is not None:
        data["x-show"] = str(_to_expr(show_if))
        data.setdefault("style", "display: none;")
    return data


@dataclass
class Node:
    """Base DSL node for representing HTML elements in the builder tree."""

    tag: str
    attrs: MutableMapping[str, str]
    children: list["Node"]
    self_closing: bool = False

    def __enter__(self) -> "Node":
        return self

    def __exit__(
        self, exc_type: object, exc: object, tb: object
    ) -> None:  # pragma: no cover - context manager plumbing
        return None

    def render(self) -> str:
        attrs_str = _render_attrs(self.attrs)
        if self.self_closing:
            return f"<{self.tag}{attrs_str} />"
        children_rendered = "".join(child.render() for child in self.children)
        return f"<{self.tag}{attrs_str}>{children_rendered}</{self.tag}>"


class TextNode(Node):
    def __init__(
        self,
        expr: Expr,
        *,
        class_name: str | None = None,
        show_if: Expr | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ):
        attr_map: MutableMapping[str, str] = {"x-text": str(expr)}
        if class_name:
            attr_map["class"] = class_name
        attr_map.update(_show_if_attrs(show_if))
        if attrs:
            attr_map.update(attrs)
        super().__init__("span", attr_map, [])


class ElementNode(Node):
    def __init__(
        self,
        builder: "MarkupBuilder",
        tag: str,
        *,
        class_name: str | None = None,
        show_if: Expr | None = None,
        attrs: MutableMapping[str, str] | None = None,
        self_closing: bool = False,
    ):
        attr_map: MutableMapping[str, str] = {}
        if class_name:
            attr_map["class"] = class_name
        attr_map.update(_show_if_attrs(show_if))
        if attrs:
            attr_map.update(attrs)
        super().__init__(tag, attr_map, [], self_closing=self_closing)
        self._builder = builder

    def __enter__(self) -> "ElementNode":  # pragma: no cover - context manager plumbing
        self._builder._stack.append(self)  # noqa: SLF001
        return self

    def __exit__(
        self, exc_type: object, exc: object, tb: object
    ) -> None:  # pragma: no cover - context manager plumbing
        self._builder._stack.pop()  # noqa: SLF001


class MarkupBuilder:
    def __init__(self, state_model: type[BaseModel], *, ui_preset: str = "tailwind"):
        self.state = StateProxy(state_model)
        self._stack: list[Node] = []
        self._nodes: list[Node] = []
        self.ui_preset = ui_preset

    def _add_node(self, node: Node) -> None:
        if self._stack:
            self._stack[-1].children.append(node)
        else:
            self._nodes.append(node)

    def text(
        self,
        *parts: Any,
        class_name: str | None = None,
        show_if: Expr | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ) -> TextNode:
        if not parts:
            raise ValueError("ml.text requires at least one part")
        expr_parts = [_to_expr(part) for part in parts]
        if len(expr_parts) == 1:
            expr = expr_parts[0]
        else:
            expr = Expr(" + ".join(part._wrap() for part in expr_parts))
        node = TextNode(expr, class_name=class_name, show_if=show_if, attrs=attrs or {})
        self._add_node(node)
        return node

    def div(
        self,
        *,
        class_name: str | None = None,
        show_if: Expr | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ) -> ElementNode:
        node = ElementNode(
            self, "div", class_name=class_name, show_if=show_if, attrs=attrs or {}
        )
        self._add_node(node)
        return node

    def span(
        self,
        *,
        class_name: str | None = None,
        show_if: Expr | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ) -> ElementNode:
        node = ElementNode(
            self, "span", class_name=class_name, show_if=show_if, attrs=attrs or {}
        )
        self._add_node(node)
        return node

    def input(
        self,
        model: StateExpr,
        *,
        type: str = "text",  # noqa: A003
        disable_if: Expr | None = None,
        class_name: str | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ) -> ElementNode:
        attr_map: MutableMapping[str, str] = {"type": type, "x-model": str(model)}
        if class_name:
            attr_map["class"] = class_name
        if disable_if is not None:
            attr_map[":disabled"] = str(disable_if)
        if attrs:
            attr_map.update(attrs)
        node = ElementNode(self, "input", attrs=attr_map, self_closing=True)
        self._add_node(node)
        return node

    def button(
        self,
        label: Any,
        *,
        disable_if: Expr | None = None,
        class_name: str | None = None,
        attrs: MutableMapping[str, str] | None = None,
    ) -> ElementNode:
        attr_map: MutableMapping[str, str] = {"type": "button"}
        if class_name:
            attr_map["class"] = class_name
        if disable_if is not None:
            attr_map[":disabled"] = str(disable_if)
        if attrs:
            attr_map.update(attrs)
        node = ElementNode(self, "button", attrs=attr_map)
        self._add_node(node)
        text_node = TextNode(_to_expr(label))
        node.children.append(text_node)
        return node

    def render(self) -> str:
        return "".join(node.render() for node in self._nodes)


def _ensure_json_compat(value: Any, path: tuple[str, ...] = ()) -> Any:
    """Validate that a value can be safely serialized to JSON for embedding."""
    if isinstance(value, BaseModel):
        return _ensure_json_compat(value.model_dump(), path)
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValueError(f"Field {'.'.join(path) or '<root>'} is not JSON-safe")
        return value
    if isinstance(value, list):
        return [
            _ensure_json_compat(item, path + (str(idx),))
            for idx, item in enumerate(value)
        ]
    if isinstance(value, dict):
        new_dict: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"Field {'.'.join(path)} has non-string key")
            new_dict[key] = _ensure_json_compat(item, path + (key,))
        return new_dict
    raise ValueError(f"Field {'.'.join(path) or '<root>'} is not JSON-serializable")


def _safe_json(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=True)
    payload = payload.replace("</", "<\\/")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    payload = (
        payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )
    return payload


def _render_document(fragment: str, initial_state: Mapping[str, Any]) -> str:
    safe_state = _safe_json(initial_state)
    state_script = (
        f'<script type="application/json" id="__mustwebui_state">{safe_state}</script>'
    )
    boot_script = (
        "<script>function __mustwebui_init(){const el="
        "document.getElementById('__mustwebui_state');"
        "return JSON.parse(el.textContent);}</script>"
    )
    body_attrs = ' x-data="__mustwebui_init()"'
    return (
        "<!DOCTYPE html>"
        '<html><head><meta charset="utf-8"></head>'
        f"<body{body_attrs}>{state_script}{boot_script}{fragment}</body></html>"
    )


class MustWebUI:
    """Entry point for registering MustWebUI pages on a FastAPI application."""

    def __init__(self, app: FastAPI, *, ui_preset: str = "tailwind"):
        self.app = app
        self.ui_preset = ui_preset

    def page(self, path: str, *, state: type[BaseModel]):
        def decorator(func: Any):
            async def endpoint() -> HTMLResponse:
                builder = MarkupBuilder(state, ui_preset=self.ui_preset)
                state_proxy = builder.state
                state_instance = state()
                html_fragment = func(builder, state_proxy)
                if html_fragment is None:
                    html_fragment = builder.render()
                initial_state = _ensure_json_compat(state_instance)
                document = _render_document(str(html_fragment), initial_state)
                return HTMLResponse(document)

            self.app.get(path)(endpoint)
            return func

        return decorator
