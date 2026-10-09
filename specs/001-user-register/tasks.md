# Task Breakdown — User Register, Login and Roles (001-user-register)

Ordered strictly by technical dependencies. Each task is sized for 20-30 minutes. Complete tasks in order; do not skip ahead because later tasks depend on earlier contracts.

Conventions:

- `Covers` = spec business rules and plan sections implemented by the task.
- `Files` = files to create or modify in this task only.
- Progress is tracked with `- [ ]` checkboxes.
- `Done when` is verifiable with a test or command.

---

## T01 — Domain exceptions contract

**Covers:** BR-8, BR-9, BR-10, BR-15, plan §4.2 (exception signatures).

**Files:**

- Create `app/domain/exceptions/user_exceptions.py`
- Create `app/domain/exceptions/__init__.py` if missing

**Steps:**

- [x] Define `UserValidationException` for length, whitespace, required-field, and invalid-role violations.
- [x] Define `DuplicateUsernameException` and `DuplicateEmailException`.
- [x] Define `InvalidCredentialsException` with a single generic message (no cause detail).
- [x] Define `ForbiddenException` for non-admin promotion attempts.
- [x] Define `UserNotFoundException` for promotion of a missing target.
- [x] Export all exceptions from the module `__init__` if applicable.

**Done when:**

- `python -c "from app.domain.exceptions.user_exceptions import UserValidationException, DuplicateUsernameException, DuplicateEmailException, InvalidCredentialsException, ForbiddenException, UserNotFoundException; print('ok')"` prints `ok`.

---

## T02 — Domain User entity with invariants and role

**Covers:** BR-3, BR-4, BR-5 (presence guard), BR-6, BR-13, plan §3.1.

**Files:**

- Create `app/domain/entities/user.py`
- Create `app/domain/entities/__init__.py` if missing
- Create `tests/unit/test_user_entity.py`

**Steps:**

- [x] Implement pure `@dataclass` `User` with fields `id`, `username`, `email`, `password_hash`, `role`, `created_at` (no framework imports).
- [x] Enforce username 8-20 inclusive and rejection of any whitespace (leading, trailing, internal).
- [x] Enforce non-empty username and non-empty email guards in domain.
- [x] Enforce plain-password length 8-20 check helper (hash itself is not built here).
- [x] Enforce role is exactly `USER` or `ADMIN`, defaulting to `USER` when not supplied.
- [x] Write unit tests for: short/long username, whitespace variants (`my user01`, ` user01AB`, `user01AB `), empty values, password 7/8/20/21 boundaries, default role `USER`, invalid role rejected.

**Done when:**

- `pytest tests/unit/test_user_entity.py -v` passes.

---

## T03 — Domain repository and hasher interfaces

**Covers:** BR-8, BR-9, BR-7 lookup needs, BR-15 target lookup, plan §4.2.

**Files:**

- Create `app/domain/repositories/user_repository.py`
- Create `app/domain/services/password_hasher_service.py`
- Create `app/domain/repositories/__init__.py`, `app/domain/services/__init__.py` if missing

**Steps:**

- [x] Define `UserRepository` ABC with `get_by_id`, `get_by_username`, `get_by_email_normalized`, `get_by_identifier`, `save`, `update`.
- [x] Document case-sensitive username vs case-insensitive (lowered) email contract in docstrings.
- [x] Define `PasswordHasher` ABC with `hash` and `verify`.
- [x] Verify no imports of FastAPI, SQLAlchemy, Pydantic, or Passlib in `app/domain`.

**Done when:**

- `python -c "from app.domain.repositories.user_repository import UserRepository; from app.domain.services.password_hasher_service import PasswordHasher; print('ok')"` prints `ok`, and `grep -R "sqlalchemy\|fastapi\|pydantic\|passlib" app/domain` returns no matches.

---

## T04 — Application DTOs with boundary validation and role

**Covers:** BR-3 (email trim), BR-5 (EmailStr), BR-13, BR-14, plan §3.3.

**Files:**

- Create `app/application/dtos/user_dtos.py`
- Create `tests/unit/test_user_dtos.py`

**Steps:**

- [x] Define `RegisterInput` with raw `username`, trimmed + EmailStr `email`, raw `password` (no `role` field accepted).
- [x] Define `LoginInput` with raw `identifier` and raw `password`.
- [x] Define `PromoteInput` with literal `role` restricted to `ADMIN`.
- [x] Define `UserOutput` (`id`, `username`, `email`, `role`) and `LoginOutput` (`access_token`, `token_type`).
- [x] Write tests for: email surrounding spaces trimmed and accepted, invalid email rejected, whitespace-only email rejected, missing fields rejected, `PromoteInput` rejects non-`ADMIN` roles.

**Done when:**

- `pytest tests/unit/test_user_dtos.py -v` passes.

---

## T05 — RegisterUser use case (always USER)

**Covers:** BR-1, BR-2, BR-3, BR-4, BR-5, BR-6, BR-8, BR-9, BR-13, BR-14, plan §5.1.

**Files:**

- Create `app/application/use_cases/user/register_user.py`
- Create `tests/unit/test_register_user.py` (fake in-memory repository + fake hasher)

**Steps:**

- [x] Implement `RegisterUser.execute` following plan pseudocode order: required check, email trim, username whitespace rejection, length checks, format check, uniqueness checks, hash, save with hardcoded `role=USER`.
- [x] Ensure any client-supplied role is ignored and returned value contains no token.
- [x] Test success path returns user with `role=USER` and no token field.
- [x] Test payload containing `role=ADMIN` still yields `USER`.
- [x] Test duplicate username exact-case fails and different-case succeeds.
- [x] Test duplicate email same-case and different-case both fail.
- [x] Test username/password boundaries and username-with-spaces rejection.

**Done when:**

- `pytest tests/unit/test_register_user.py -v` passes.

---

## T06 — LoginUser use case with generic failure and role token

**Covers:** BR-7, BR-9 (case-insensitive email login), BR-10, BR-13, plan §5.2.

**Files:**

- Create `app/application/use_cases/user/login_user.py`
- Create `tests/unit/test_login_user.py` (reuse fakes from T05)

**Steps:**

- [x] Implement identifier routing: contains `@` goes to lowered-trimmed email lookup, otherwise exact username lookup with no trimming.
- [x] Raise the same `InvalidCredentialsException` for unknown user and wrong password.
- [x] Issue stateless token via injected token service carrying `user_id`, `username`, and `role` (mock in unit tests).
- [x] Test login via email, via username, via differently-cased email succeeds with correct role in token request.
- [x] Test wrong password and unknown identifier raise identical exception type and message.
- [x] Test empty identifier and empty password raise validation, not credentials.

**Done when:**

- `pytest tests/unit/test_login_user.py -v` passes.

---

## T07 — PromoteUser use case (admin only)

**Covers:** BR-13, BR-15, plan §4.2 and §5.3.

**Files:**

- Create `app/application/use_cases/user/promote_user.py`
- Create `tests/unit/test_promote_user.py` (fake repository with USER and ADMIN fixtures)

**Steps:**

- [x] Implement `PromoteUser.execute(requester, target_user_id, new_role)` requiring `requester.role == ADMIN`, existing target, and `new_role == ADMIN`.
- [x] Raise `ForbiddenException` for non-admin, `UserNotFoundException` for missing target, `ValidationException` for invalid role.
- [x] Test admin promotion succeeds, non-admin yields forbidden with no change, missing target yields not-found, non-`ADMIN` role yields validation.

**Done when:**

- `pytest tests/unit/test_promote_user.py -v` passes.

---

## T08 — Persistence model and migration with role

**Covers:** BR-8, BR-9, BR-13 persistence guarantees, plan §3.2.

**Files:**

- Create `app/infrastructure/db/models/user_model.py`
- Create Alembic revision under `alembic/versions/` for `users` table (or add-role revision if table exists)

**Steps:**

- [x] Define `users` table with `id`, `username VARCHAR(20) UNIQUE NOT NULL`, `email NOT NULL`, `email_normalized UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `role VARCHAR(5) NOT NULL DEFAULT USER` with CHECK (`USER`, `ADMIN`), `created_at TIMESTAMPTZ NOT NULL`.
- [x] Confirm no `is_active`, `email_verified`, or lockout columns are added.
- [x] Generate and review Alembic revision (create table + both UNIQUE constraints + role default; backfill existing rows to `USER` if altering).

**Done when:**

- `alembic upgrade head` succeeds on a clean test database and `alembic downgrade -1; alembic upgrade head` also succeeds.

---

## T09 — Bcrypt hasher implementation

**Covers:** Security rule from `AGENT.md`, plan §6 decision 1.

**Files:**

- Create `app/infrastructure/services/bcrypt_password_hasher.py`
- Create `tests/unit/test_bcrypt_password_hasher.py`

**Steps:**

- [x] Implement `PasswordHasher` with Passlib Bcrypt `hash` and `verify`.
- [x] Test hash differs from plain text, verifies correctly, and rejects wrong password.

**Done when:**

- `pytest tests/unit/test_bcrypt_password_hasher.py -v` passes.

---

## T10 — JWT token service with role claim

**Covers:** Authenticated access after login, BR-12 (no server session), BR-13, plan §4.2.

**Files:**

- Create `app/infrastructure/services/jwt_token_service.py`
- Create `tests/unit/test_jwt_token_service.py`

**Steps:**

- [ ] Implement `issue_token(user_id, username, role)` using `python-jose` and secret from environment (never hardcoded).
- [ ] Test token decodes with expected subject, username, and role claims using the test secret.

**Done when:**

- `pytest tests/unit/test_jwt_token_service.py -v` passes.

---

## T11 — Postgres repository implementation

**Covers:** BR-8, BR-9, BR-13, plan §4.2 repository contract.

**Files:**

- Create `app/infrastructure/repositories/postgres_user_repository.py`
- Create `tests/integration/test_postgres_user_repository.py`

**Steps:**

- [ ] Implement `get_by_id`, exact username lookup, lowered email lookup, identifier routing, `save`, and `update` (role change).
- [ ] Map DB UNIQUE violations on `username` and `email_normalized` to domain duplicate exceptions.
- [ ] Persist trimmed email with original casing plus lowered normalized copy and round-trip `role`.
- [ ] Test case-sensitive username match, case-insensitive email match, duplicate persistence raises domain exceptions, stored email is trimmed, role persists and updates without altering other fields.

**Done when:**

- `pytest tests/integration/test_postgres_user_repository.py -v` passes against a test PostgreSQL database.

---

## T12 — Admin seed (idempotent, env-only)

**Covers:** BR-14, BR-16, plan §4.2 and §5.4.

**Files:**

- Create `app/infrastructure/db/seeds/admin_seed.py`
- Create `tests/integration/test_admin_seed.py`

**Steps:**

- [ ] Implement `ensure_admin_exists()` reading admin credentials exclusively from environment (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`); fail fast when missing.
- [ ] Validate seed values with the same domain rules as registration, hash the password, save with `role=ADMIN`.
- [ ] Ensure idempotency: existing admin by email (any casing) or any existing `ADMIN` means no change, no duplicate, no demotion; never log the password.
- [ ] Test empty DB creates exactly one `ADMIN`, rerun changes nothing, differently-cased existing email prevents duplicates, missing env fails without creating a user.

**Done when:**

- `pytest tests/integration/test_admin_seed.py -v` passes against a test PostgreSQL database.

---

## T13 — Dependency wiring with admin guard

**Covers:** Plan §4.3, `AGENT.md` entrypoints layer rules, BR-15.

**Files:**

- Create `app/entrypoints/api/v1/dependencies.py`

**Steps:**

- [ ] Wire session, repository, hasher, token service, `RegisterUser`, `LoginUser`, and `PromoteUser` via FastAPI `Depends`.
- [ ] Provide `get_current_user` (token validation) and `require_admin` (role guard) dependencies.
- [ ] Ensure routers will receive only use cases and guards, never sessions or repositories directly.

**Done when:**

- `python -c "import app.entrypoints.api.v1.dependencies; print('ok')"` prints `ok` without import errors.

---

## T14 — Register route and HTTP mapping

**Covers:** BR-1, BR-2, BR-4, BR-5, BR-6, BR-8, BR-9, BR-13, BR-14, plan §4.1 and §5.5.

**Files:**

- Create `app/entrypoints/api/v1/routes/user_router.py`
- Modify `app/entrypoints/api/v1/main.py` (register router only)
- Create `tests/e2e/test_user_register_router.py`

**Steps:**

- [ ] Implement `POST /api/v1/users/register` returning `201` with `UserOutput` (`role: USER`) and login-redirect message.
- [ ] Map validation errors to `400` and duplicates to `409` with distinct codes.
- [ ] Assert response contains no token field and role is always `USER` even when payload includes `role: ADMIN`.
- [ ] Test matrix: success `201`, payload with `ADMIN` still yields `USER`, duplicate username `409`, duplicate email different-case `409`, bad email `400`, short/long username `400`, username with spaces `400` (including `user01AB`), short/long password `400`, missing fields `400`.

**Done when:**

- `pytest tests/e2e/test_user_register_router.py -v` passes.

---

## T15 — Login and promotion routes

**Covers:** BR-7, BR-10, BR-13, BR-15, plan §4.1 and §5.5.

**Files:**

- Modify `app/entrypoints/api/v1/routes/user_router.py`
- Create `tests/e2e/test_user_login_router.py`
- Create `tests/e2e/test_user_promote_router.py`

**Steps:**

- [ ] Implement `POST /api/v1/users/login` returning `200` with `LoginOutput` on success.
- [ ] Map all credential mismatches to identical `401` bodies; missing fields to `400`.
- [ ] Implement `PATCH /api/v1/users/{user_id}/role` behind `require_admin`: `200` on success, `401` unauthenticated, `403` non-admin, `404` missing target, `400` invalid role.
- [ ] Test login via email `200`, via username `200`, via differently-cased email `200`, wrong password `401`, unknown identifier `401` with body identical to wrong password, missing fields `400`, token decodes to correct role.
- [ ] Test promotion: admin token plus valid target yields `200` and `ADMIN`; user token yields `403` with no change; missing token yields `401`; unknown target yields `404`; invalid role yields `400`.
- [ ] Test no logout or recovery routes exist (`POST /api/v1/users/logout` and password-reset paths return `404`).

**Done when:**

- `pytest tests/e2e/test_user_login_router.py tests/e2e/test_user_promote_router.py -v` passes.

---

## T16 — Final verification and Definition of Done

**Covers:** `AGENT.md` Definition of Done, full spec scenarios regression including roles and seed.

**Files:**

- Touch no source files; update `specs/001-user-register/tasks.md` checkboxes only.

**Steps:**

- [ ] Run linters and formatters with zero errors.
- [ ] Run full suite: `pytest tests/ -v` passes (unit + integration + e2e).
- [ ] Manually verify register `201` has no token and `role: USER`, login `401` bodies are identical for both failure causes, promotion without admin yields `403`, and seed rerun changes nothing.
- [ ] Confirm `spec.md`, `plan.md`, and `tasks.md` are consistent with delivered behavior.

**Done when:**

- Linter command passes with zero errors and `pytest tests/ -v` passes with zero failures.
