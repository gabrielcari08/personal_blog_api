# Technical Plan — Articles (002-articles)

This plan answers HOW the `spec.md` will be implemented. It respects Clean Architecture from `AGENT.md` and the current stack (FastAPI, SQLAlchemy, PostgreSQL, Pydantic). No implementation code is included here, only contracts, structures, and pseudocode.

> **Backend layout note:** the backend lives in `backend/`. All `app/`, `tests/`, and `alembic/` paths in this document are relative to `backend/`, and every command (pytest, alembic, uvicorn) must be run from `backend/`.

## 1. Functional Requirements Mapping to Modules

| Spec rule | Module responsible | Notes |
|---|---|---|
| BR-1 Public read (list + single, no auth) | `entrypoints/api/v1/routes/article_router.py` (open GETs) + `application/use_cases/article/list_articles.py`, `get_article.py` | No `Depends(get_current_user)` on reads. Returns author reference so the frontend can hide actions. |
| BR-2 Authenticated creation (USER or ADMIN) | `entrypoints/api/v1/routes/article_router.py` (requires `get_current_user`) + `application/use_cases/article/create_article.py` | Caller identity comes from the validated token, never from the body. |
| BR-3 Ownership on creation (ignore client author) | `application/use_cases/article/create_article.py` (hardcodes `user_id` from token) | No `user_id` field is accepted in input DTOs. |
| BR-4 Creation time (system-assigned, timezone-aware, audit-only, same as users) | `domain/entities/article.py` (optional at construction) + `infrastructure/db/models/article_model.py` (TIMESTAMPTZ, server default) + `infrastructure/repositories/postgres_article_repository.py` (never writes it, reads it back) | Mirrors `users.created_at` handling. Never requested nor editable. |
| BR-5 Owner-only mutation (USER) + BR-6 Admin override | `application/use_cases/article/update_article.py`, `delete_article.py` (authorization check: owner OR ADMIN) | Role and id come from `AuthContext` (validated token user). |
| BR-7 Hidden actions plus direct enforcement | Frontend hides edit/delete when `current_user.id != article.user_id AND role != ADMIN` (uses `ArticleOutput.user_id`); backend enforces in update/delete use cases raising forbidden | Hiding is UX only; the use-case check is the real guard, returning 403 on bypass. |
| BR-8 Editable fields (only title + text) | `domain/entities/article.py` (immutable `user_id`, `created_at`) + `application/dtos/article_dtos.py` (update input has only title + text) + use cases (construct updated entity preserving originals) | Even ADMIN cannot change authorship or time. |
| BR-9 Title 8-20, exact message | `domain/entities/article.py` (pure validation, message `title must be 8-20 characters`) + `application/dtos/article_dtos.py` (boundary validator delegating to domain, same message) | Raw length, no trimming. |
| BR-10 Text 10-300, exact messages | `domain/entities/article.py` (empty -> `text is required`; out-of-range non-empty -> `text must be 10-300 characters`) + DTOs (same delegation) | Raw length, no trimming. |
| BR-11 Character counting (raw, space/newline/emoji = 1, no trim) | `domain/entities/article.py` (plain `len()` on raw string) | No `strip()` anywhere on this path, unlike email. |
| BR-12 Listing order (most recent first, no pagination) | `infrastructure/repositories/postgres_article_repository.py` (`ORDER BY created_at DESC, id DESC`) + `application/use_cases/article/list_articles.py` (no limit/offset params) | Tiebreaker `id DESC` for equal timestamps. |
| BR-13 No modification timestamp | Explicit non-goal; no `updated_at` column, field, or DTO member | Documented to avoid accidental introduction. |
| BR-14 Permanent deletion, no confirmation | `application/use_cases/article/delete_article.py` + repository `delete()` (hard row removal) | No trash flag, no recovery flow, no confirm step. |
| System limit: one author, no transfer | `infrastructure/db/models/article_model.py` (`user_id` FK NOT NULL, no update path for it) | Transfer is unrepresentable in the API. |

Validation split per `AGENT.md`: DTOs handle transport shape and delegate length/presence to domain helpers (so messages stay exact); domain entities enforce all invariants on construction; use cases handle only orchestration (existence, ownership, persistence); infrastructure handles SQL mapping and ordering; entrypoints handle HTTP only.

## 2. Folder and File Structure

New files only under `backend/app/` following `AGENT.md`. Existing `backend/app/entrypoints/api/main.py` and `backend/app/entrypoints/api/v1/dependencies.py` are extended, not rewritten. Existing user modules are untouched.

```text
app/
├── domain/
│   ├── entities/
│   │   └── article.py                 # Article dataclass + validate_title / validate_text (raw len, exact messages)
│   ├── repositories/
│   │   └── article_repository.py      # ArticleRepository ABC (get_by_id, list_all_desc, save, update, delete)
│   └── exceptions/
│       └── article_exceptions.py      # ArticleValidationException, ArticleNotFoundException, ArticleForbiddenException
├── application/
│   ├── dtos/
│   │   └── article_dtos.py            # ArticleCreateInput, ArticleUpdateInput, ArticleOutput (Pydantic, no user_id in inputs)
│   └── use_cases/
│       └── article/
│           ├── create_article.py      # CreateArticle (auth user injected as caller)
│           ├── list_articles.py       # ListArticles (public, ordered)
│           ├── get_article.py         # GetArticle (public single, 404 when missing)
│           ├── update_article.py      # UpdateArticle (owner-or-admin, immutable author/time)
│           └── delete_article.py      # DeleteArticle (owner-or-admin, hard delete)
├── infrastructure/
│   ├── db/
│   │   └── models/
│   │       └── article_model.py       # SQLAlchemy ArticleModel (articles table + FK to users + TIMESTAMPTZ)
│   └── repositories/
│       └── postgres_article_repository.py  # Concrete ArticleRepository (entity/model mapping + ordering)
└── entrypoints/
    └── api/
        ├── main.py                    # Existing FastAPI app: register article_router + map new exceptions (modify)
        └── v1/
            ├── dependencies.py        # Add get_article_repository + five use-case factories (extend, reuse get_current_user)
            └── routes/
                └── article_router.py  # POST /articles, GET /articles, GET /articles/{id}, PUT /articles/{id}, DELETE /articles/{id}
```

Migration (Alembic): single new revision creating the `articles` table with columns, FK, checks, and indexes described in Section 3. No change to the `users` table.

Tests mirror the structure under `backend/tests/`:

```text
tests/
├── unit/
│   ├── test_article_entity.py
│   ├── test_create_article.py
│   ├── test_list_get_article.py
│   ├── test_update_article.py
│   └── test_delete_article.py
├── integration/
│   └── test_postgres_article_repository.py
└── e2e/
    └── test_article_router.py
```

## 3. Data Model / Schemas

### 3.1 Domain Entity (conceptual)

Attributes:

- `id`: opaque unique identifier, generated by the system.
- `title`: string, 8-20 characters inclusive, raw length, no trimming. Any whitespace, line break, or emoji counts as one character each.
- `user_id`: integer author reference, set once at creation from the authenticated caller. Immutable afterwards. Never supplied by the client.
- `text`: string, 10-300 characters inclusive when non-empty; empty string is a distinct error. Raw length, no trimming. Spaces, line breaks, and emojis each count as one character.
- `created_at`: timestamp of creation (audit only, not part of inputs). Optional at construction; filled by persistence. Immutable.

Invariants enforced by the entity (via `__post_init__` plus reusable helpers):

- Title empty or with length outside 8-20 is invalid with message `title must be 8-20 characters`.
- Text equal to empty string (exactly `""`) is invalid with message `text is required`.
- Text non-empty with length outside 10-300 is invalid with message `text must be 10-300 characters`.
- Non-string title or text is invalid (mapped to the same range messages at the boundary).
- `user_id` missing on a persisted entity is invalid; author cannot be reassigned (entity exposes no setter path for it in updates).
- `created_at` is never accepted from input and never mutated on update.

### 3.2 Persistence Model (PostgreSQL `articles` table)

Columns:

- `id`: serial primary key.
- `title`: VARCHAR(20), NOT NULL, with a CHECK guard on character length 8-20 as defense in depth (domain remains primary).
- `user_id`: INTEGER, NOT NULL, FOREIGN KEY referencing `users(id)` with ON DELETE CASCADE. Indexed for ownership lookups.
- `text`: TEXT, NOT NULL, with a CHECK guard on character length 10-300 as defense in depth (empty is already rejected by the domain; the CHECK documents the range at the storage level).
- `created_at`: TIMESTAMPTZ, NOT NULL, server default `now()`. Identical handling to `users.created_at`.

Constraints and indexes:

- PRIMARY KEY on `id`.
- FOREIGN KEY `user_id -> users(id)` ON DELETE CASCADE (articles never orphan; user deletion is out of scope but the rule prevents orphans if it ever happens).
- CHECK on title length and CHECK on text length (safety nets only; exact messages come from the domain).
- Composite ordering support: INDEX on `created_at DESC, id DESC` for the most-recent-first list; INDEX on `user_id` for owner checks.
- No `updated_at`, no status/draft/published flag, no soft-delete flag in this version.

### 3.3 DTO Schemas (boundary)

- `ArticleCreateInput`: `title` (raw string, no trim, delegates to domain title check), `text` (raw string, no trim, delegates to domain text check). No `user_id`, no `created_at` members. Any extra author/time fields sent by the client are ignored (not declared, so rejected or dropped by the boundary per framework default).
- `ArticleUpdateInput`: identical shape to create (both `title` and `text` required, same raw validation). Full replacement, not partial.
- `ArticleOutput`: `id`, `title`, `text`, `user_id`, `created_at`. The `user_id` member is what lets the frontend decide visibility of edit/delete controls. List responses return arrays of this shape ordered most recent first.

Validation split: DTO validators call the domain `validate_title` / `validate_text` helpers so the exact spec messages (`title must be 8-20 characters`, `text must be 10-300 characters`, `text is required`) surface identically whether validation triggers at the boundary or on entity construction. Use cases perform no primitive length or empty checks.

## 4. Interface / API / Signature Contracts

### 4.1 HTTP API

Base prefix: `/api/v1`. Reads are public; all mutations require a Bearer token via the existing `get_current_user` guard (401 when missing or invalid, reusing the users behavior).

- `POST /api/v1/articles`
  - Auth: required (401 otherwise).
  - Input: `ArticleCreateInput` as JSON.
  - Success: `201 Created`, body `ArticleOutput` (with server-assigned `user_id` and `created_at`).
  - Failures: `400` for validation (exact spec messages); `401` when unauthenticated.
  - Side effects: one row inserted; immediately visible in public reads.

- `GET /api/v1/articles`
  - Auth: none (public).
  - Input: none (no pagination params in this version).
  - Success: `200 OK`, body array of `ArticleOutput` ordered by `created_at DESC, id DESC`.
  - Failures: none besides infrastructure errors.

- `GET /api/v1/articles/{article_id}`
  - Auth: none (public).
  - Success: `200 OK`, body `ArticleOutput`.
  - Failures: `404` when the article does not exist.

- `PUT /api/v1/articles/{article_id}`
  - Auth: required (401 otherwise).
  - Input: `ArticleUpdateInput` as JSON (both fields required).
  - Success: `200 OK`, body `ArticleOutput` with original `user_id` and `created_at` preserved.
  - Failures: `400` for validation (same exact messages); `401` when unauthenticated; `403` when authenticated USER is not the owner (including direct bypass attempts); `404` when the article does not exist.
  - Side effects: title and text replaced; nothing else changes.

- `DELETE /api/v1/articles/{article_id}`
  - Auth: required (401 otherwise).
  - Input: none besides the path id.
  - Success: `204 No Content` (no body).
  - Failures: `401` when unauthenticated; `403` when authenticated USER is not the owner; `404` when the article does not exist.
  - Side effects: row permanently removed; subsequent reads return 404 and the item disappears from the list.

- Error body shape: same convention as users (`detail` with the exact spec message plus a stable `code`: `validation_error`, `forbidden`, `article_not_found`). The existing `RequestValidationError` handler continues to map boundary shape errors to `400`.

- Frontend hiding contract: list/single outputs always include `user_id`; the client shows edit/delete controls only when `authenticated_user.id == article.user_id OR authenticated_user.role == ADMIN`. This is presentation only.

### 4.2 Domain and Application Signatures (language-agnostic)

- `ArticleRepository (ABC)`:
  - `get_by_id(article_id: int) -> Article | null`
  - `list_all_desc() -> list[Article]` — full list ordered most recent first, no pagination args.
  - `save(article: Article) -> Article` — persists a new article; returns the stored version with id and creation time.
  - `update(article: Article) -> Article` — persists title/text change for an existing article; raises not-found when missing.
  - `delete(article_id: int) -> void` — hard-removes the row; raises not-found when missing.

- `CreateArticle (use case)`:
  - `execute(caller: User, input: ArticleCreateInput) -> ArticleOutput`
  - Constructs the entity with `user_id = caller.id`, ignoring any client author. Entity construction enforces title/text rules. Raises validation on violation.

- `ListArticles (use case)`:
  - `execute() -> list[ArticleOutput]` — delegates to `list_all_desc`, no auth context needed.

- `GetArticle (use case)`:
  - `execute(article_id: int) -> ArticleOutput` — raises `ArticleNotFoundException` when missing.

- `UpdateArticle (use case)`:
  - `execute(caller: User, article_id: int, input: ArticleUpdateInput) -> ArticleOutput`
  - Rules: target must exist else not-found; caller must be owner (`caller.id == target.user_id`) or `caller.role == ADMIN` else forbidden; new entity preserves `id`, `user_id`, `created_at` and replaces only title/text (entity revalidates).
  - Raises: `ArticleNotFoundException`, `ArticleForbiddenException`, `ArticleValidationException`.

- `DeleteArticle (use case)`:
  - `execute(caller: User, article_id: int) -> void`
  - Same existence and owner-or-admin rules as update; then hard-deletes.
  - Raises: `ArticleNotFoundException`, `ArticleForbiddenException`.

- `ArticleValidationException` carries exactly one of the three spec messages; `ArticleNotFoundException` maps to 404; `ArticleForbiddenException` maps to 403.

### 4.3 Dependency Wiring

`entrypoints/api/v1/dependencies.py` adds: `get_article_repository(session) -> ArticleRepository` plus five factories (`get_create_article`, `get_list_articles`, `get_get_article`, `get_update_article`, `get_delete_article`) each receiving the repository. Routers receive only use cases plus `get_current_user` for mutations; they never receive repositories or sessions directly. `main.py` registers the new router and adds exception handlers for the three article exceptions, reusing the same status/code convention as users.

## 5. Main Algorithms / Logic in Pseudocode

### 5.1 Domain validation (raw length, no trim)

```text
FUNCTION validate_title(title):
  IF title is not a string OR LENGTH(title) < 8 OR LENGTH(title) > 20:
    RAISE validation ("title must be 8-20 characters")
  # LENGTH counts the raw value: spaces, line breaks, emojis each count 1
  # no TRIM is applied at any point

FUNCTION validate_text(text):
  IF text is not a string OR text == "":
    RAISE validation ("text is required")
  IF LENGTH(text) < 10 OR LENGTH(text) > 300:
    RAISE validation ("text must be 10-300 characters")
  # same raw counting rule as title; whitespace-only strings fall
  # under the range check (e.g. 3 spaces -> "text must be 10-300 characters")

FUNCTION construct_article(title, user_id, text):
  validate_title(title)
  validate_text(text)
  REQUIRE user_id present
  RETURN entity(id=None, title, user_id, text, created_at=None)
```

### 5.2 Create (caller becomes owner)

```text
FUNCTION create_article(caller, input):
  REQUIRE caller authenticated (else 401 at the route guard)
  # no primitive checks here; entity + DTO boundary already enforce them
  article = construct_article(input.title, caller.id, input.text)
  stored = repository.save(article)   # DB fills id + creation time
  RETURN article_output(stored)
```

### 5.3 Public list and single read

```text
FUNCTION list_articles():
  rows = repository.list_all_desc()   # SQL: ORDER BY created_at DESC, id DESC
  RETURN rows mapped to outputs (no filtering, no pagination)

FUNCTION get_article(article_id):
  row = repository.get_by_id(article_id)
  IF row is null:
    RAISE not-found
  RETURN article_output(row)
```

### 5.4 Update (owner-or-admin, immutable author/time)

```text
FUNCTION update_article(caller, article_id, input):
  REQUIRE caller authenticated (else 401 at the route guard)
  target = repository.get_by_id(article_id)
  IF target is null:
    RAISE not-found (404, nothing changes)

  IF caller.id != target.user_id AND caller.role != ADMIN:
    RAISE forbidden (403, nothing changes)  # covers direct bypass, not just hidden buttons

  # rebuild entity preserving history; construction revalidates new values
  updated = entity(id=target.id, title=input.title, user_id=target.user_id,
                   text=input.text, created_at=target.created_at)
  stored = repository.update(updated)
  RETURN article_output(stored)
```

### 5.5 Delete (owner-or-admin, hard removal)

```text
FUNCTION delete_article(caller, article_id):
  REQUIRE caller authenticated (else 401 at the route guard)
  target = repository.get_by_id(article_id)
  IF target is null:
    RAISE not-found (404, nothing removed)

  IF caller.id != target.user_id AND caller.role != ADMIN:
    RAISE forbidden (403, nothing removed)

  repository.delete(article_id)   # permanent row removal, no confirmation
  RETURN no-content
```

### 5.6 Router Error Mapping

```text
POST /articles:
  TRY create_article
  CATCH validation -> 400 (exact spec message preserved)
  CATCH unauthenticated -> 401

GET /articles, GET /articles/{id}:
  TRY list / get
  CATCH not-found (single only) -> 404
  # no auth checks, no validation beyond path shape

PUT /articles/{id}:
  REQUIRE authenticated (401 if missing/invalid token)
  TRY update_article
  CATCH validation -> 400 (exact spec message)
  CATCH forbidden -> 403
  CATCH not-found -> 404

DELETE /articles/{id}:
  REQUIRE authenticated (401 if missing/invalid token)
  TRY delete_article
  CATCH forbidden -> 403
  CATCH not-found -> 404
  SUCCESS -> 204 with empty body
```

## 6. Key Technical Decisions with Discarded Alternatives

1. **One use case per operation (five small classes) following `AGENT.md`.**
   Chosen for single responsibility and to mirror the user module (register/login/promote). Each use case stays thin and testable with a fake repository. Discarded: a single god `ArticleService` with five methods (mixes orchestration concerns, harder to wire and test in isolation) and putting authorization inside the router (duplicates owner-or-admin logic across PUT and DELETE).

2. **Authorization inside use cases (owner id check OR ADMIN role), routes only authenticate.**
   Chosen because both PUT and DELETE share the identical rule and the rule needs the stored `user_id`, which only the use case loads. `require_admin` alone is insufficient since owners without ADMIN must pass. Discarded: route-level `require_admin` for all mutations (would block legitimate owners) and frontend-only hiding with no backend check (trivially bypassable; spec now explicitly demands direct 403 enforcement).

3. **Full replacement via PUT with both fields required.**
   Chosen because the spec requires title and text on edit (same shape as create), making PUT semantics exact. Discarded: PATCH with optional fields (implies partial updates the spec never asks for and complicates the required-vs-range error matrix) and separate title-only / text-only endpoints (endpoint sprawl with no spec benefit).

4. **Raw `len()` counting with zero trimming.**
   Chosen because the clarification mandates spaces, line breaks, and emojis each count as 1 with no trimming. Native string length satisfies this directly (each codepoint counts once). Discarded: stripping before measuring (would violate the spec, e.g. turning surrounding spaces invisible) and grapheme-cluster counting (splits some emojis into multiple units or merges sequences; overkill and contradicts the stated rule).

5. **DTO validators delegate to domain helpers for identical messages.**
   Chosen to guarantee the three exact messages surface from both layers, mirroring how password length is handled in the user module. Discarded: duplicating literal messages in DTOs and entities separately (drifts over time) and relying solely on framework length constraints (produces generic messages, not the spec-exact strings).

6. **Persistence mirrors `users.created_at`: TIMESTAMPTZ with server default, audit-only.**
   Chosen for consistency across the schema and to satisfy the explicit clarification to configure it the same way as users. Application code never writes it. Discarded: client-supplied timestamps (forgery and timezone chaos), naive datetimes without timezone (ambiguity the users table already solved), and adding an `updated_at` column (spec BR-13 forbids it in this version).

7. **Ordering in the database (`ORDER BY created_at DESC, id DESC`), no pagination params.**
   Chosen because the spec fixes most-recent-first with no pagination; pushing order to SQL is efficient and the `id` tiebreaker makes equal-timestamp runs deterministic. Discarded: in-memory sorting after fetching (wasteful and nondeterministic on ties) and adding limit/offset params now (spec explicitly says none; they can be introduced later without breaking the contract).

8. **Hard delete with `204 No Content` and FK `ON DELETE CASCADE`.**
   Chosen to implement permanent direct deletion literally; 204 signals success with nothing to return. CASCADE prevents orphan rows if a user row ever disappears. Discarded: soft delete with a flag (requires list filtering, recovery flows, and contradicts permanence), `200` with a body (no resource left to represent), and `SET NULL` / `RESTRICT` on the FK (first violates NOT NULL authorship, second adds failure modes with no spec demand).

9. **Title as VARCHAR(20) plus CHECKs as safety nets, domain as the authority.**
   Chosen to match the existing `users.username` pattern (VARCHAR with domain-first validation). TEXT for body accommodates 300 characters comfortably. Discarded: making the database the primary validator (error messages would be generic constraint violations, not spec-exact) and omitting CHECKs entirely (loses defense in depth against out-of-band writes).

10. **Reuse of existing auth plumbing (`get_current_user`, 401 behavior, error body shape).**
    Chosen to avoid a parallel auth system; article mutations share the Bearer/JWT guard and the same `detail` + `code` envelope. Only three new exception mappings are added. Discarded: a separate article-scoped token or role guard (duplication, drift risk) and distinct error envelopes per resource (breaks client consistency).

## 7. Test Strategy

Aligned with Definition of Done in `AGENT.md` (linters clean, unit tests passing, docs updated). No implementation files are created in this plan.

- **Unit — domain entity (`tests/unit/test_article_entity.py`):**
  Title boundaries 8 and 20 pass, 7 and 21 fail with `title must be 8-20 characters`; empty title fails with the same message. Text empty (`""`) fails with `text is required`; lengths 10 and 300 pass, 9 and 301 fail with `text must be 10-300 characters`. Whitespace-only text of length 3 fails with the range message (proving no empty-collapse). Raw counting: leading/trailing spaces, embedded newlines, and single emojis each increment length by 1 (e.g. 7 chars plus one emoji passes title; no trimming applied). Construction with valid values preserves `user_id` and leaves `created_at` unset for persistence to fill. No database or frameworks involved.

- **Unit — use cases with fake in-memory repository (`test_create_article.py`, `test_list_get_article.py`, `test_update_article.py`, `test_delete_article.py`):**
  Create assigns `caller.id` as owner even when the input carries no author and stamps no time itself. List returns insertion-shuffled fixtures sorted most-recent-first (including equal-timestamp tiebreak by id). Get returns the row; missing id raises not-found. Update by owner succeeds and preserves `user_id`/`created_at`; update by ADMIN on another's article succeeds with originals preserved; update by non-owner USER raises forbidden with nothing changed; update with invalid title/text raises the exact spec message with originals preserved. Delete by owner and by ADMIN remove; delete by non-owner raises forbidden with nothing removed; delete of missing id raises not-found. No HTTP or SQL here.

- **Integration — repository (`tests/integration/test_postgres_article_repository.py`):**
  Round-trip persists title/text/owner and returns server-assigned id and timezone-aware creation time. FK violation on unknown `user_id` fails. Ordering query returns newest first across mixed timestamps. CHECK guards hold as a safety net. Update changes only title/text; delete removes the row so subsequent fetch is empty.

- **End-to-end — HTTP (`tests/e2e/test_article_router.py`):**
  Full spec matrix: public `GET /articles` and `GET /articles/{id}` succeed with no token and list in most-recent-first order; `POST` without token yields 401 and creates nothing; `POST` with valid token and valid payload yields 201 with correct owner and time; `POST` with short/long title yields 400 `title must be 8-20 characters`; `POST` with empty text yields 400 `text is required`; `POST` with 9/301-char text yields 400 `text must be 10-300 characters`. Owner `PUT` yields 200 with history preserved; non-owner USER `PUT`/`DELETE` via direct call yield 403 despite hidden buttons; ADMIN `PUT`/`DELETE` on another's article succeed; `PUT`/`DELETE` on missing id yield 404; `DELETE` success yields 204 and the item vanishes from the list. Response bodies always include `user_id` for the hiding contract. Byte-compare the three exact error strings.

- **Security and regression:**
  No author or timestamp spoofing (extra `user_id`/`created_at` in request bodies has no effect). Unauthenticated and forbidden attempts change nothing (re-fetch to prove it). Stored rows carry system times, never client times. Linters and formatters pass with zero errors before merge.
