# Contributing to Android-MCP

Thank you for your interest in contributing to **Android-MCP (`android-as-a-tool`)**! We welcome contributions from developers across open-source communities and enterprise engineering teams.

---

## 1. Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 2. Progressive Quality Protocol (Gate 1 & Gate 2)

All code contributed to this repository must pass through our **two-phase quality protocol**:

```
[ Feature / Fix ] ──▶ [ Gate 1: Optimal & Acceptable ] ──▶ [ Gate 2: Well-Crafted ] ──▶ [ Merge ]
                            (Solid MVP, Minimal Blast)       (Hardened, Typed, Benchmarked)
```

1. **Gate 1: Optimal & Acceptable**:
   - Zero hardcoded secrets or credentials.
   - Standard library favored before external dependencies (YAGNI).
   - Corresponding unit tests added in `tests/` and test cases in `evals/`.
   - Any deferred technical debt explicitly documented with `# DEBT: <reason>`.
2. **Gate 2: Well-Crafted (Production Target)**:
   - Complete type annotations across public signatures.
   - Explicit exception handling (no bare `except Exception: pass`).
   - Guardrails integration for any network or shell inputs.
   - 100% test pass rate with zero skips.

Verify both gates locally before submitting your pull request:
```bash
python skills/code-analyzer/scripts/analyze.py
```

---

## 3. Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/buhozurdo/android-as-a-tool.git
   cd android-as-a-tool
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies in editable mode**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify the environment**:
   ```bash
   python skills/android-doctor/scripts/doctor.py
   python -m pytest
   ```

---

## 4. Branching Strategy & PR Workflow

We follow a modified Gitflow / Release Train workflow:
* `main`: Strictly production-ready, stable releases.
* `dev`: Primary integration branch for active development.
* Feature branches: Branch from `dev` as `feature/<name>` or `fix/<name>`.

### Commit Message Guidelines
We strictly enforce [Conventional Commits](https://www.conventionalcommits.org/):
* `feat:` A new feature or tool.
* `fix:` A bug fix.
* `perf:` A code change that improves performance.
* `security:` Security enhancements or guardrail fixes.
* `test:` Adding or refactoring tests.
* `docs:` Documentation updates.
* `refactor:` Code change that neither fixes a bug nor adds a feature.

---

## 5. Submitting a Pull Request

1. Ensure the full test suite passes: `python -m pytest`
2. Run the evaluation suite: `python evals/evaluators/eval_runner.py`
3. Run the code analyzer: `python skills/code-analyzer/scripts/analyze.py`
4. Submit PR targeting the `dev` branch with a clear title and description referencing any related issues.
