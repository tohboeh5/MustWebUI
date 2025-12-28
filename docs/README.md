# MustWebUI Docs (Specification)

This directory contains the MustWebUI **specification**: a design-first set of documents intended to be specific enough to implement.

- Audience: implementers and early adopters
- Prereqs: FastAPI / Pydantic / Alpine.js
- Goal: turn **Type-Safe Python to Reactive UI** into a concrete, testable contract

## Recommended reading order

1. [spec-architecture.md](spec-architecture.md)
2. [spec-state-proxy.md](spec-state-proxy.md)
3. [spec-rpc-actions.md](spec-rpc-actions.md)
4. [spec-dsl.md](spec-dsl.md)
5. [component-catalog.md](component-catalog.md)
6. [spec-security-ops.md](spec-security-ops.md)

## Glossary (minimal)

- **State**: client UI state defined as a Pydantic model.
- **Proxy / Expr**: a Python object representing a JS expression (e.g. `state.count` → `count`).
- **Action**: a declarative instruction sequence to run on an event (e.g. button click).
- **Compile/Transpile**: convert Python DSL/Actions into SSR HTML + Alpine expressions + fetch calls.
