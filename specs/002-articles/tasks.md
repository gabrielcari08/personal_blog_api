# Task Breakdown — Articles (002-articles)

Ordered strictly by technical dependencies. Each task is sized for 20-30 minutes. Complete tasks in order; do not skip ahead because later tasks depend on earlier contracts.

Conventions:

- `Covers` = spec business rules and plan sections implemented by the task.
- `Files` = files to create or modify in this task only.
- Progress is tracked with `- [ ]` checkboxes.
- `Done when` is verifiable with a test or command.

---

## T01 — Domain exceptions contract

**Covers:** BR-9, BR-10, BR-5/BR-6 failure modes, plan §4.2 (exception signatures).

**Files:**

- Create `app/domain/exceptions/article_exceptions.py`
- Create `app/domain/exceptions/__init__.py` if missing

**Steps:**

- [x] Define `ArticleValidationException` for title/text violations (carries the exact spec messages).
- [x] Define `ArticleNotFoundException` for edit/delete/get of a missing article.
- [x] Define `ArticleForbiddenException` for non-owner USER mutation attempts (direct bypass).
- [x] Export all exceptions from the module `__init__` if applicable.

**Done when:**

- `python -c "from app.domain.exceptions.article_exceptions import ArticleValidationException, ArticleNotFoundException, ArticleForbiddenException; print('ok')"` prints `ok`.

---

## T02 — Domain Article entity with raw-length invariants

**Covers:** BR-8, BR-9, BR-10, BR-11, BR-4/BR-13 (audit-only time), plan §3.1 and §5.1.

**Files:**

- Create `app/domain/entities/article.py`
- Create `tests/unit/test_article_entity.py`

**Steps:**

- [ ] Implement pure `@dataclass` `Article` with fields `id`, `title`, `user_id`, `text`, `created_at` (no framework imports).
- [ ] Implement `validate_title` enforcing 8-20 raw characters with exact message `title must be 8-20 characters` (empty included, no trim).
- [ ] Implement `validate_text` enforcing empty -> `text is required`, non-empty outside 10-300 -> `text must be 10-300 characters` (no trim).
- [ ] Enforce raw counting: spaces, line breaks, emojis each count as 1 via plain length (no `strip()` anywhere).
- [ ] Enforce `__post_init__` self-validation; `user_id` required, `created_at` optional and never validated from input.
- [ ] Write unit tests for: title 7/8/20/21 boundaries, empty title, text empty, text 9/10/300/301 boundaries, whitespace-only text of length 3 (range message), 7 chars + 1 emoji passing title, surrounding spaces counted (not trimmed), valid construction preserves `user_id` with `created_at` unset.

**Done when:**

- `pytest tests/unit/test_article_entity.py -v` passes.

---

## T03 — Domain repository interface

**Covers:** BR-1 list needs, BR-12 ordering contract, BR-14 deletion contract, plan §4.2.

**Files:**

- Create `app/domain/repositories/article_repository.py`
- Create `app/domain/repositories/__init__.py` if missing

**Steps:**

- [ ] Define `ArticleRepository` ABC with `get_by_id`, `list_all_desc`, `save`, `update`, `delete`.
- [ ] Document in docstrings: `list_all_desc` returns full list most-recent-first with no pagination args; `update` persists only title/text; `delete` is a hard removal.
- [ ] Verify no imports of FastAPI, SQLAlchemy, Pydantic in `app/domain`.

**Done when:**

- `python -c "from app.domain.repositories.article_repository import ArticleRepository; print('ok')"` prints `ok`, and `grep -R "sqlalchemy\|fastapi\|pydantic" app/domain/entities/article.py app/domain/repositories/article_repository.py app/domain/exceptions/article_exceptions.py` returns no matches.

---

## T04 — Application DTOs with delegated validation

**Covers:** BR-8, BR-9, BR-10, BR-11, plan §3.3.

**Files:**

- Create `app/application/dtos/article_dtos.py`
- Create `tests/unit/test_article_dtos.py`

**Steps:**

- [ ] Define `ArticleCreateInput` with raw `title` and raw `text` only (no `user_id`, no `created_at`); validators delegate to domain `validate_title` / `validate_text` so messages stay exact; no trimming.
- [ ] Define `ArticleUpdateInput` with identical required shape (both fields required, full replacement).
- [ ] Define `ArticleOutput` with `id`, `title`, `text`, `user_id`, `created_at` (the `user_id` enables frontend hide logic).
- [ ] Write tests for: valid inputs pass through unchanged (spaces preserved), short/long title rejected with exact message, empty text rejected with `text is required`, 9/301-char text rejected with range message, extra `user_id`/`created_at` in payload is ignored or rejected (never accepted as input).

**Done when:**

- `pytest tests/unit/test_article_dtos.py -v` passes.

---

## T05 — Persistence model and migration

**Covers:** BR-4, BR-8 system limit, BR-12 ordering support, BR-13 (no `updated_at`), plan §3.2.

**Files:**

- Create `app/infrastructure/db/models/article_model.py`
- Create Alembic revision under `alembic/versions/` for the `articles` table

**Steps:**

- [ ] Define `articles` table with `id` PK, `title VARCHAR(20) NOT NULL` + length CHECK 8-20, `user_id INTEGER NOT NULL` FK to `users(id)` ON DELETE CASCADE, `text TEXT NOT NULL` + length CHECK 10-300, `created_at TIMESTAMPTZ NOT NULL` server default `now()` (same handling as users).
- [ ] Add indexes for `created_at DESC, id DESC` ordering and for `user_id` ownership lookups.
- [ ] Confirm no `updated_at`, status, draft, or soft-delete columns are added and `users` table is untouched.
- [ ] Generate and review the Alembic revision (create table + FK + CHECKs + indexes).

**Done when:**

- `alembic upgrade head` succeeds on a clean test database and `alembic downgrade -1; alembic upgrade head` also succeeds.

---

## T06 — Postgres repository implementation

**Covers:** BR-1, BR-4, BR-8, BR-12, BR-14 storage behavior, plan §4.2 repository contract.

**Files:**

- Create `app/infrastructure/repositories/postgres_article_repository.py`
- Create `tests/integration/test_postgres_article_repository.py`

**Steps:**

- [ ] Implement `get_by_id`, `list_all_desc` (`ORDER BY created_at DESC, id DESC`), `save` (never writes `created_at`, reads back id + time), `update` (only title/text, raises not-found when missing), `delete` (hard removal, raises not-found when missing).
- [ ] Map entity to/from ORM row preserving `user_id` and `created_at` untouched on update.
- [ ] Test round-trip persists title/text/owner and returns server-assigned id plus timezone-aware time; FK violation on unknown `user_id` fails; ordering returns newest first across mixed timestamps with id tiebreak; update changes only title/text; delete removes so fetch is empty.

**Done when:**

- `pytest tests/integration/test_postgres_article_repository.py -v` passes against a test PostgreSQL database.

---

## T07 — CreateArticle use case (owner = caller)

**Covers:** BR-2, BR-3, BR-4, BR-9, BR-10, BR-11, plan §5.2.

**Files:**

- Create `app/application/use_cases/article/create_article.py`
- Create `tests/unit/test_create_article.py` (fake in-memory repository)

**Steps:**

- [ ] Implement `CreateArticle.execute(caller, input)` constructing the entity with `user_id = caller.id` (no primitive length checks here; entity enforces them).
- [ ] Ensure no client author or timestamp is trusted; returned output carries server `user_id` and time.
- [ ] Test success assigns caller as owner; invalid title/text raise exact spec messages with nothing saved; ADMIN caller is owned like any author.

**Done when:**

- `pytest tests/unit/test_create_article.py -v` passes.

---

## T08 — ListArticles and GetArticle use cases (public)

**Covers:** BR-1, BR-12, plan §5.3.

**Files:**

- Create `app/application/use_cases/article/list_articles.py`
- Create `app/application/use_cases/article/get_article.py`
- Create `tests/unit/test_list_get_article.py` (reuse fake repository)

**Steps:**

- [ ] Implement `ListArticles.execute()` delegating to `list_all_desc` with no auth context and no pagination params.
- [ ] Implement `GetArticle.execute(article_id)` raising `ArticleNotFoundException` when missing.
- [ ] Test list returns fixtures ordered most-recent-first (including equal-timestamp id tiebreak); get returns the row; get of missing id raises not-found.

**Done when:**

- `pytest tests/unit/test_list_get_article.py -v` passes.

---

## T09 — UpdateArticle use case (owner-or-admin)

**Covers:** BR-5, BR-6, BR-7 direct enforcement, BR-8, BR-9, BR-10, plan §5.4.

**Files:**

- Create `app/application/use_cases/article/update_article.py`
- Create `tests/unit/test_update_article.py` (fake repository with two users + ADMIN fixtures)

**Steps:**

- [ ] Implement `UpdateArticle.execute(caller, article_id, input)` requiring existing target (not-found), then owner (`caller.id == target.user_id`) OR `caller.role == ADMIN` else forbidden; rebuild entity preserving `id`, `user_id`, `created_at` and replacing only title/text.
- [ ] Test owner update succeeds with history preserved; ADMIN update of another's article succeeds with originals preserved; non-owner USER raises forbidden with nothing changed; missing id raises not-found; invalid new title/text raise exact messages with originals preserved.

**Done when:**

- `pytest tests/unit/test_update_article.py -v` passes.

---

## T10 — DeleteArticle use case (owner-or-admin, hard delete)

**Covers:** BR-5, BR-6, BR-7 direct enforcement, BR-14, plan §5.5.

**Files:**

- Create `app/application/use_cases/article/delete_article.py`
- Create `tests/unit/test_delete_article.py` (reuse fakes from T09)

**Steps:**

- [ ] Implement `DeleteArticle.execute(caller, article_id)` with same existence and owner-or-admin rules as update, then hard-deletes with no confirmation step.
- [ ] Test owner delete removes; ADMIN delete of another's removes; non-owner USER raises forbidden with nothing removed; missing id raises not-found.

**Done when:**

- `pytest tests/unit/test_delete_article.py -v` passes.

---

## T11 — Dependency wiring for articles

**Covers:** Plan §4.3, `AGENT.md` entrypoints layer rules.

**Files:**

- Modify `app/entrypoints/api/v1/dependencies.py` (extend only; keep existing user wiring intact)

**Steps:**

- [ ] Add `get_article_repository` building the Postgres repository from the request session.
- [ ] Add five factories: `get_create_article`, `get_list_articles`, `get_get_article`, `get_update_article`, `get_delete_article` (each receives only the repository).
- [ ] Reuse existing `get_current_user` for mutation auth; no new token logic; routers will receive only use cases and guards.

**Done when:**

- `python -c "import app.entrypoints.api.v1.dependencies; print('ok')"` prints `ok` without import errors.

---

## T12 — Article router: public reads + create + error mapping

**Covers:** BR-1, BR-2, BR-3, BR-4, BR-9, BR-10, BR-12, plan §4.1 and §5.6 (partial).

**Files:**

- Create `app/entrypoints/api/v1/routes/article_router.py` (GETs + POST only in this task)
- Modify `app/entrypoints/api/main.py` (register router + map article validation/not-found exceptions; keep user handlers intact)
- Create `tests/e2e/test_article_router_read_create.py`

**Steps:**

- [ ] Implement `GET /api/v1/articles` (public, ordered most-recent-first, no auth) and `GET /api/v1/articles/{id}` (public, 404 when missing).
- [ ] Implement `POST /api/v1/articles` behind `get_current_user` returning `201` with `ArticleOutput` (server owner + time).
- [ ] Map `ArticleValidationException` to `400` preserving exact messages, `ArticleNotFoundException` to `404`; keep `RequestValidationError` -> `400` behavior.
- [ ] Test matrix: public list succeeds with no token in newest-first order; public single succeeds with no token and includes `user_id`; POST without token yields `401` creating nothing; POST valid yields `201` with correct owner; POST short/long title yields `400` exact title message; POST empty text yields `400` `text is required`; POST 9/301-char text yields `400` exact range message; extra `user_id` in body has no effect.

**Done when:**

- `pytest tests/e2e/test_article_router_read_create.py -v` passes.

---

## T13 — Article router: update + delete with owner-or-admin enforcement

**Covers:** BR-5, BR-6, BR-7, BR-8, BR-13, BR-14, plan §4.1 and §5.6 (partial).

**Files:**

- Modify `app/entrypoints/api/v1/routes/article_router.py` (add PUT + DELETE)
- Modify `app/entrypoints/api/main.py` (add forbidden mapping if missing)
- Create `tests/e2e/test_article_router_mutations.py`

**Steps:**

- [ ] Implement `PUT /api/v1/articles/{id}` behind `get_current_user` returning `200` with history preserved; `403` for non-owner USER (direct bypass), `404` for missing, `400` exact validation messages.
- [ ] Implement `DELETE /api/v1/articles/{id}` behind `get_current_user` returning `204` empty; `403` for non-owner USER, `404` for missing.
- [ ] Map `ArticleForbiddenException` to `403` with stable code envelope.
- [ ] Test matrix: owner PUT `200` with `user_id`/`created_at` unchanged; non-owner USER PUT/DELETE yield `403` with nothing changed (proving backend enforcement beyond hidden buttons); ADMIN PUT/DELETE on another's succeed; PUT invalid values yield `400` exact messages with originals preserved; PUT/DELETE missing id yield `404`; DELETE success yields `204` and item vanishes from list and single fetch 404s.

**Done when:**

- `pytest tests/e2e/test_article_router_mutations.py -v` passes.

---

## T14 — Final verification and Definition of Done

**Covers:** `AGENT.md` Definition of Done, full spec scenarios regression.

**Files:**

- Touch no source files; update `specs/002-articles/tasks.md` checkboxes only.

**Steps:**

- [ ] Run linters and formatters with zero errors.
- [ ] Run full suite: `pytest tests/ -v` passes (unit + integration + e2e, users + articles).
- [ ] Manually verify public list needs no token and is newest-first with no pagination; POST spoofing `user_id`/`created_at` has no effect; non-owner USER sees `user_id` in output (hide contract) and gets `403` on direct PUT/DELETE; ADMIN manages any article; deleted article disappears.
- [ ] Confirm `spec.md`, `plan.md`, and `tasks.md` are consistent with delivered behavior.

**Done when:**

- Linter command passes with zero errors and `pytest tests/ -v` passes with zero failures.
