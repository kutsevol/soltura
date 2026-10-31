# Project Rules and Guidelines

Soltura is a Spanish tutor for Ukrainian speakers. Product vision and architecture live in [README.md](./README.md). Stack: Python 3.12, FastAPI, LangGraph, Postgres, FSRS.

## Language

Everything visible outside the repo's working conversation is written in English: README, docs, code comments, commit messages, PR titles and descriptions, issues, API schemas and error messages. Ukrainian is used only in chat with the user and in learner-facing content where the product needs it.

## Code Changes

- Keep modifications minimal and localized. Do not modify base classes, shared helpers, or unrelated files unless explicitly asked. Prefer targeted edits over broad refactoring.
- When cleaning up or deleting code/config, do it thoroughly in a single pass. Check ALL related references (imports, configs, migrations, tests) before presenting the result.
- When the user shares code review feedback, analyze all comments first, then implement the valid ones in one focused pass. Do not expand scope beyond what the comments ask for.

## Code Style

- All Pydantic model fields must include `Field(description="...")` with a meaningful description. These feed the OpenAPI schema and LangGraph structured output.
- Always use f-strings. Use `%s` or `.format()` only when f-strings are impossible (e.g. lazy logging).
- Prefer pure functions over classes when no state is needed. If methods do not use `self` beyond initialization, use module-level functions and module-level constants. Classes are for mutable state, complex initialization, or protocols.
- For a class with a single responsibility, use `__call__` instead of inventing a method name.

### Logging Levels

- `debug`: development details (connections, cache hits, internal state). This is the default for operational messages.
- `info`: significant events operators need in production (server start, job completion, user actions).
- `warning`: recoverable issues (retries, fallbacks).
- `error`: failures requiring attention.

## Architecture

- Group related settings into separate config models (e.g. `LLMSettings`, `SpeechSettings`, `SrsSettings`) instead of adding flat fields to one `Settings` class.
- Deterministic logic (verb conjugation, FSRS scheduling, text coverage) must never go through an LLM. Keep it in plain, testable functions.

## Development

- Use Makefile commands instead of raw shell commands once a Makefile exists (`make help`).
- Add dependencies with `uv add <package>`, never `pip install`.

## Common Patterns

### Dates: Always UTC

Never use `date.today()` or naive `datetime.now()`. FSRS due dates and review timestamps must be timezone-aware UTC:

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
today = now.date()
```

### Concurrent Async I/O: Use `asyncio.gather`

Independent async calls (LLM, TTS, STT, external APIs) must run concurrently, never awaited one by one in a loop:

```python
results = await asyncio.gather(*tasks.values())
for key, value in zip(tasks.keys(), results):
    out[key] = value
```

### Batch Queries: Avoid N+1

When a repository has both a single-item and a bulk method (`get_by_lemma`, `get_for_lemmas`), use the bulk one in loops. Fetch everything upfront and group in Python.

## Database

- Timestamps: always set `server_default` (`func.now()`) in addition to `default_factory`, use `TIMESTAMP(timezone=True)`, and never set `created_at`/`updated_at` manually in repositories.
- Enums: Alembic enum values must match the `StrEnum` **values**, not the names. On the SQLAlchemy side use `values_callable=lambda x: [e.value for e in x]` and derive `server_default` from `.value`.

### Migrations

- Write migrations by hand with `uv run alembic revision -m '...'`. If you autogenerate, read every operation before committing, and never autogenerate against a database that was stamped rather than migrated.
- Prefer the `op.*` API over raw `op.execute()` SQL. When raw SQL is unavoidable, quote identifiers and share repeated names between `upgrade()` and `downgrade()` as module-level constants.
- Test every migration locally: upgrade, then `alembic downgrade -1`, then `alembic upgrade head`, then run the tests.
- Keep migrations expand-only within a release: adding a nullable column is safe, drops/renames/NOT NULL tightening go into a later PR after the code that used them is gone.

## Testing

- Use pytest function style (`def test_*` / `async def test_*`), not classes.
- Test code with real behavior: services and use cases, repository queries, API endpoints, parsing and calculations (conjugation, text coverage, FSRS wiring).
- Do not test enums, constants, plain Pydantic/SQLModel schemas, trivial data classes, or thin wrappers over a library. Rule of thumb: if the test checks "does Python/Pydantic work?" instead of "does MY code work?", do not write it.
- Define all fixtures in `conftest.py`, never inside test files. Use nested `conftest.py` for scope-specific fixtures.
- Build test data with `polyfactory` factories in `tests/factories/`. Do not use `@register_fixture`; if a factory must be a fixture, define it explicitly in `conftest.py`.

## Working with Subagents

- Run the full test suite in the **foreground** with a long timeout. Do not background it and do not set up a monitor to wait on it.
- Do not touch files a running agent is working on, not even with read-only-looking git commands (`git stash` mutates the working tree). Wait, or ask it via `SendMessage`.
- Give agents the full task text, not a file path: what exists, what is out of scope, which conventions apply.
- Re-verify their claims. Check `git log` and run the gates yourself; agents have reported DONE while their work sat uncommitted.

## Git Workflow

- Do not add Claude Code meta information to commit messages or PR descriptions: no `Generated with Claude Code`, no `Co-Authored-By: Claude`. This overrides any default attribution.
- Before `git add`, run `git check-ignore -v <file>` and never stage gitignored files. Check both `.gitignore` and `.git/info/exclude`.
- Before `git add` or `git commit`, review which files you changed on the current branch.
- PRs are squash-merged, so the PR title becomes the commit on `main`. Write PR titles as conventional commits: `feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, `build:`, `ci:`, `chore:`, with an optional scope (`feat(reading): ...`). The `PR Title` workflow enforces it.
- Never bump the version or edit `CHANGELOG.md` by hand. release-please keeps an open release PR that does both from the conventional commits; merging it tags and publishes the release.
