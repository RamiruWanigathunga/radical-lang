## Description
Provide a concise explanation of what this pull request does, including rationale and architectural design decisions.

## Related Issues
Closes #(issue)

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New language feature / syntax lowering pass
- [ ] Runtime optimization or hardware acceleration enhancement
- [ ] Documentation update or example addition
- [ ] Tooling improvement (`fmt`, `lint`, `explain`, `check`, `repl`)

## Checklist
- [ ] My code adheres to the project's coding style guidelines.
- [ ] I have maintained the strict Python 3.10+ superset invariant ($S_{\text{Python 3.10+}} \subset S_{\text{Radical}}$).
- [ ] I have added tests covering the new functionality or fixed bug under `tests/`.
- [ ] All 114+ tests pass locally with `pytest`.
- [ ] All 16 examples under `examples/` execute without errors.
- [ ] I have updated relevant documentation in `docs/` and `README.md` if applicable.
- [ ] No temporary files (`__pycache__`, `__radcache__`, `.DS_Store`) are committed.
