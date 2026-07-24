# Git Commit Message Conventions

This document establishes the canonical Git commit message standards for the AI Healthcare System codebase. All commit messages must be professional, concise, imperative, and free of marketing jargon or AI slop.

---

## 1. Core Format

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary in imperative mood>

[optional body explaining why the change was made]
```

### Example Commit Messages

* ✅ `feat(cardiology): add TAVR valve-in-valve coronary obstruction model`
* ✅ `fix(hepatology): clamp lower bound in MELD 3.0 sodium calculation`
* ✅ `test(audit): add boundary condition unit tests for Fick engine`
* ✅ `docs(architecture): update database session dependency guidelines`
* ✅ `refactor(ui): streamline clinical protocol selection component`

---

## 2. Prohibited Patterns ("No AI Slop")

To maintain high code quality and professional repository history, the following patterns are strictly prohibited in commit messages:

1. ❌ **No Theatrical Buzzwords**: Never use words like `SOTA`, `game-changing`, `incredible`, `landmark`, or `revolutionary`.
2. ❌ **No Internal Wave Jargon**: Do not label commits with session wave numbers (e.g., `Wave 35 SOTA Expansion`).
3. ❌ **No Past Tense Verbs**: Do not write `added`, `fixed`, `updated`. Use imperative present tense: `add`, `fix`, `update`.
4. ❌ **No Overly Verbose Subject Lines**: Keep the subject line under 72 characters.

---

## 3. Allowed Types

* `feat`: A new feature or clinical algorithm implementation.
* `fix`: A bug fix or mathematical formula correction.
* `test`: Adding missing tests or refactoring unit test assertions.
* `docs`: Documentation updates only.
* `refactor`: Code change that neither fixes a bug nor adds a feature.
* `perf`: A code change that improves performance or execution time.
* `chore`: Maintenance tasks, dependency updates, or build configuration changes.

---

## 4. Scopes

Common scopes used in this repository:

* `(cardiology)`: Interventional cardiology & hemodynamic modules.
* `(hepatology)`: Gastroenterology & liver disease modules.
* `(neurology)`: Movement disorders & stroke modules.
* `(nephrology)`: Kidney disease & AKI modules.
* `(pulmonology)`: Respiratory disease & nodule models.
* `(ui)`: Vite React frontend components & pages.
* `(api)`: FastAPI backend route handlers & schemas.
* `(db)`: SQLAlchemy models & database migrations.
