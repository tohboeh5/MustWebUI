# MustWebUI requirements (Milestones 0–5)

- **R1: SSR route registration** – A FastAPI page registered via `MustWebUI.page` must return SSR HTML that includes an Alpine `x-data` initializer populated from the state defaults.  
  _Validated by_ `tests/test_ssr_integration.py::test_ssr_hello_page`.

- **R2: Safe initial-state embedding** – The embedded state JSON must escape sequences like `</script>`, `<`, `>`, `&`, and `\u2028/\u2029` so that adversarial payloads cannot break the document.  
  _Validated by_ `tests/test_ssr_integration.py::test_state_embedding_is_safely_escaped`.

- **R3: State proxy semantics** – State access compiles to JS paths, rejects missing fields, forbids truthiness, and supports the baseline operators (`+`, `-`, `===`, `>=`, `&&`, `||`, `!`) with literal normalization.  
  _Validated by_ `tests/test_state_proxy.py::test_paths_resolve`, `test_missing_field_errors`, `test_truthiness_is_forbidden`, `test_operator_compilation`, and `test_literal_normalization`.

- **R4: DSL rendering** – The DSL builder must maintain parent/child context, map `class_name` to `class`, convert `show_if` to `x-show`, and render text parts as deterministic `x-text` expressions.  
  _Validated by_ `tests/test_dsl_render.py::test_context_nesting` and `test_text_concatenation`.

- **R5: Local Alpine bindings** – Form controls and buttons must emit Alpine bindings (`x-model`, `x-text`, `:disabled`) to enable local reactivity without network calls.  
  _Validated by_ `tests/test_dsl_render.py::test_input_and_button_bindings`.
