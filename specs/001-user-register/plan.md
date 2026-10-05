# Technical Plan — User Register, Login and Roles (001-user-register)

This plan answers HOW the `spec.md` will be implemented. It respects Clean Architecture from `AGENT.md` and the current stack (FastAPI, SQLAlchemy, PostgreSQL, Pydantic, Passlib-Bcrypt, python-jose). No implementation code is included here, only contracts, structures, and pseudocode.

## 1. Functional Requirements Mapping to Modules

| Spec rule | Module responsible | Notes |
|---|---|---|
| BR-1 Active on creation, BR-2 No auto-login | `application/use_cases/user/register_user.py` | Creates user, returns user data only, never returns a token. Redirect to login is a frontend concern. |
| BR-3 Email trimming, username never trimmed | `application/dtos/user_dtos.py` (email trim) + `domain/entities/user.py` (username validation) | Email is normalized before validation. Username with any whitespace is rejected, not trimmed. |
| BR-4 Username 8-20, no whitespace | `domain/entities/user.py` | Pure Python validation, zero frameworks. |
| BR-5 Email valid format, unrestricted length | `application/dtos/user_dtos.py` via EmailStr + `domain/entities/user.py` (non-empty guard) | Format is enforced at the boundary; domain keeps a framework-free presence guard. |
| BR-6 Password 8-20, no complexity, not trimmed | `domain/entities/user.py` (length) + `application/use_cases/user/*` (pass-through without trim) | Length only; no character-class checks. |
| BR-7 Login with email OR username | `application/use_cases/user/login_user.py` | Resolves identifier type, then delegates to repository. |
| BR-8 Username unique case-sensitive | `infrastructure/db/models/user_model.py` (UNIQUE) + `infrastructure/repositories/postgres_user_repository.py` (exact match) | Binary/exact comparison. |
| BR-9 Email unique case-insensitive | `infrastructure/db/models/user_model.py` (normalized column + UNIQUE) + `postgres_user_repository.py` (lowered lookup) | `Test@mail.com` equals `test@mail.com`. |
| BR-10 Generic login failure message | `domain/exceptions/user_exceptions.py` (`InvalidCredentialsException`) + `entrypoints/api/v1/routes/user_router.py` (maps to 401 with single message) | Same message for unknown identifier and wrong password. |
| BR-11 No lockout / no abuse protection | Explicit non-goal; no module is created for throttling or lockout | Documented to avoid accidental introduction. |
| BR-12 No logout / no recovery | Explicit non-goal; no logout endpoint, no reset flow | Login issues a stateless token; no server-side session to destroy. |
| BR-13 Role model (USER, ADMIN) | `domain/entities/user.py` (role value object or literal) + `infrastructure/db/models/user_model.py` (role column) + `application/dtos/user_dtos.py` (role in outputs) | Single source of allowed values in domain; DB enforces via CHECK or enum. |
| BR-14 Default USER on register | `application/use_cases/user/register_user.py` (hardcodes USER, ignores client role) | Client-supplied role is never trusted. |
| BR-15 Admin-only promotion | `application/use_cases/user/promote_user.py` (authorization check) + `entrypoints/api/v1/routes/user_router.py` (requires authenticated ADMIN, maps to 403/404) | Caller identity comes from the validated token, never from the request body. |
| BR-16 Initial admin seed | `infrastructure/db/seeds/admin_seed.py` (idempotent seed reading admin credentials from environment) | Runs on demand or at startup; creates ADMIN only when missing. |
| Token carries role | `infrastructure/services/jwt_token_service.py` (role claim) | Login token includes role so routes can authorize without extra lookups. |
| Happy path ordering | `entrypoints/api/v1/routes/user_router.py` -> DTOs -> use cases -> repository | Entrypoints handle HTTP only; all rules live inward. |

## 2. Folder and File Structure

New files only under `app/` following `AGENT.md`. Existing `app/entrypoints/api/v1/main.py` is kept and extended by router registration.

```text
app/
├── domain/
│   ├── entities/
│   │   └── user.py                    # User dataclass + validation (username, password length, whitespace, role)
│   ├── repositories/
│   │   └── user_repository.py         # UserRepository ABC (adds get_by_id, update)
│   ├── services/
│   │   └── password_hasher_service.py # PasswordHasher ABC (hash, verify)
│   └── exceptions/
│       └── user_exceptions.py         # DuplicateUsername, DuplicateEmail, InvalidCredentials, Forbidden, NotFound, Validation errors
├── application/
│   ├── dtos/
│   │   └── user_dtos.py               # RegisterInput, LoginInput, PromoteInput, UserOutput (+role), LoginOutput (Pydantic)
│   └── use_cases/
│       └── user/
│           ├── register_user.py       # RegisterUser use case (always USER)
│           ├── login_user.py          # LoginUser use case (returns token with role)
│           └── promote_user.py        # PromoteUser use case (admin-only grant of ADMIN)
├── infrastructure/
│   ├── db/
│   │   ├── models/
│   │   │   └── user_model.py          # SQLAlchemy UserModel (users table + role column)
│   │   └── seeds/
│   │       └── admin_seed.py          # ensure_admin_exists() reading ADMIN_* from environment
│   ├── repositories/
│   │   └── postgres_user_repository.py# Concrete UserRepository
│   └── services/
│       ├── bcrypt_password_hasher.py  # Bcrypt implementation of PasswordHasher
│       └── jwt_token_service.py       # Stateless token issuance for login (includes role claim)
└── entrypoints/
    └── api/
        └── v1/
            ├── main.py                # Existing FastAPI app, register user_router (modify, do not rewrite)
            ├── routes/
            │   └── user_router.py     # POST /users/register, POST /users/login, PATCH /users/{id}/role
            └── dependencies.py        # Wiring: session, repository, hasher, token service, use cases, current-user + admin guard
```

Migration (Alembic): single revision creating `users` table with constraints described in Section 3, including the role column. If the table already exists from an earlier revision, a second revision adds the role column with backfill to `USER`.

Tests mirror the structure under `tests/`:

```text
tests/
├── unit/
│   ├── test_user_entity.py
│   ├── test_register_user.py
│   ├── test_login_user.py
│   └── test_promote_user.py
├── integration/
│   ├── test_postgres_user_repository.py
│   └── test_admin_seed.py
└── e2e/
    ├── test_user_register_router.py
    └── test_user_login_router.py
    └── test_user_promote_router.py
```

## 3. Data Model / Schemas

### 3.1 Domain Entity (conceptual)

Attributes:

- `id`: opaque unique identifier, generated by the system.
- `username`: string, 8-20 characters inclusive, no whitespace characters anywhere. Case is preserved. Case-sensitive for uniqueness.
- `email`: string, trimmed of leading/trailing spaces, valid email shape, length unrestricted. Case is preserved for display; a lowered form is used only for uniqueness and login lookup.
- `password_hash`: string, never the plain password. Set once at registration via the hashing service.
- `role`: string literal, exactly `USER` or `ADMIN`. No other value is valid.
- `created_at`: timestamp of creation (audit only, not part of spec inputs).

Invariants enforced by the entity:

- Empty or whitespace-only username is invalid.
- Username length outside 8-20 is invalid.
- Any whitespace inside username (including leading/trailing) is invalid.
- Empty email is invalid.
- Password length outside 8-20 is invalid (plain password length is checked before hashing).
- Role outside `USER` and `ADMIN` is invalid.

### 3.2 Persistence Model (PostgreSQL `users` table)

Columns:

- `id`: UUID or serial primary key.
- `username`: VARCHAR(20), NOT NULL, UNIQUE (binary/case-sensitive comparison).
- `email`: VARCHAR (unrestricted, e.g. VARCHAR(320) or TEXT), NOT NULL. Stores the trimmed value with original casing.
- `email_normalized`: VARCHAR, NOT NULL, UNIQUE. Stores `lower(trimmed email)`. This is the enforcement point for BR-9.
- `password_hash`: TEXT, NOT NULL.
- `role`: VARCHAR(5) or native ENUM(`USER`, `ADMIN`), NOT NULL, DEFAULT `USER`, CHECK constraint limiting values to the two allowed roles.
- `created_at`: TIMESTAMPTZ, NOT NULL, server default.

Constraints:

- UNIQUE on `username` (exact match).
- UNIQUE on `email_normalized` (case-insensitive email uniqueness).
- CHECK on role values; CHECK or length guard on username as safety net (domain remains the primary rule).
- No `is_active`, no `email_verified`, no `locked_until` columns in this version (explicitly out of scope).

Seed data: one row with role `ADMIN` provisioned from environment configuration (never hardcoded in source). The provided admin username, email, and password satisfy the same length and format rules as regular registration.

### 3.3 DTO Schemas (boundary)

- `RegisterInput`: `username` (raw, not pre-trimmed, so whitespace can be rejected), `email` (trimmed then EmailStr-validated), `password` (raw, length 8-20, not trimmed). No `role` field is accepted; any client-sent role is ignored at the use-case level.
- `LoginInput`: `identifier` (raw string; trimmed only for the email path, never for the username path), `password` (raw).
- `PromoteInput`: `role` (must equal `ADMIN` in this version; validated as literal).
- `UserOutput`: `id`, `username`, `email` (display form), `role`.
- `LoginOutput`: `access_token`, `token_type` (always bearer in this version). The token itself carries the role claim.

Validation split: shape and email format at the DTO boundary; business invariants (length, whitespace, role values, uniqueness, authorization) in domain and use cases.

## 4. Interface / API / Signature Contracts

### 4.1 HTTP API

Base prefix: `/api/v1`.

- `POST /api/v1/users/register`
  - Input: `RegisterInput` as JSON.
  - Success: `201 Created`, body `UserOutput` (with `role: USER`) plus a human message indicating redirection to login.
  - Failures: `400` for validation errors (length, whitespace, bad email shape, missing fields), `409` for duplicate username and for duplicate email (distinct error codes, same 409 status).
  - Side effects: none besides persistence. No token is issued. No session is created. Role is always `USER`.

- `POST /api/v1/users/login`
  - Input: `LoginInput` as JSON (`identifier` accepts email or username).
  - Success: `200 OK`, body `LoginOutput` (stateless token carrying the role claim).
  - Failures: `400` for missing fields; `401` with a single generic message for both unknown identifier and wrong password.
  - Side effects: none besides token issuance.

- `PATCH /api/v1/users/{user_id}/role`
  - Auth: required, bearer token of an authenticated user with role `ADMIN` (resolved from the validated token, never from the body).
  - Input: `PromoteInput` as JSON (`role: ADMIN`).
  - Success: `200 OK`, body `UserOutput` with updated role.
  - Failures: `401` when unauthenticated or token invalid; `403` when authenticated but not `ADMIN`; `404` when target user does not exist; `400` when role value is invalid.
  - Side effects: updates target role from `USER` to `ADMIN`. No other role transition exists in this version.

- Seed (not HTTP): `ensure_admin_exists()` invoked from a startup hook or CLI command. Reads admin credentials exclusively from environment variables. Creates the `ADMIN` user when no admin exists; otherwise does nothing. Never updates or demotes an existing admin and never logs the password.

No `POST /logout`, no `POST /password-reset`, no `GET /verify-email` in this version.

### 4.2 Domain and Application Signatures (language-agnostic)

- `UserRepository (ABC)`:
  - `get_by_id(user_id: string) -> User | null`
  - `get_by_username(username: string) -> User | null` — exact, case-sensitive match.
  - `get_by_email_normalized(email_normalized: string) -> User | null` — caller passes already-lowered email.
  - `get_by_identifier(identifier: string) -> User | null` — convenience: if identifier contains `@`, delegates to email path with trimming and lowering; otherwise delegates to username path with no trimming.
  - `save(user: User) -> User` — persists a new user; raises duplicate exceptions on constraint violation (defense in depth against races).
  - `update(user: User) -> User` — persists role change; raises not-found when target is missing.

- `PasswordHasher (ABC)`:
  - `hash(plain_password: string) -> string`
  - `verify(plain_password: string, password_hash: string) -> boolean` — constant-time comparison.

- `RegisterUser (use case)`:
  - `execute(input: RegisterInput) -> UserOutput`
  - Always constructs the user with `role = USER`, ignoring any client role.
  - Raises: `ValidationException`, `DuplicateUsernameException`, `DuplicateEmailException`.

- `LoginUser (use case)`:
  - `execute(input: LoginInput) -> LoginOutput`
  - Raises: `InvalidCredentialsException` for every credential mismatch (unknown user or bad password). Never distinguishes the cause.
  - The issued token embeds `role` so downstream authorization does not require an extra lookup.

- `PromoteUser (use case)`:
  - `execute(requester: AuthContext, target_user_id: string, new_role: string) -> UserOutput`
  - `AuthContext` carries `requester_user_id` and `requester_role` extracted from the validated token.
  - Rules: requester role must be `ADMIN` else raise `ForbiddenException`; target must exist else raise `UserNotFoundException`; `new_role` must be `ADMIN` else raise `ValidationException`.
  - Raises: `ForbiddenException`, `UserNotFoundException`, `ValidationException`.

- `TokenService`:
  - `issue_token(user_id: string, username: string, role: string) -> string` — stateless signed token for the authenticated area, including the role claim.

- `AdminSeed`:
  - `ensure_admin_exists() -> SeedResult (created | already_exists)` — checks for any existing `ADMIN` (by role query or by seeded email lookup); when missing, validates env-supplied username, email, and password with the same domain rules, hashes the password, and saves with `role = ADMIN`. Idempotent and safe to rerun.

### 4.3 Dependency Wiring

`entrypoints/api/v1/dependencies.py` provides: database session, `PostgresUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `RegisterUser`, `LoginUser`, `PromoteUser`, plus `get_current_user` (token validation) and `require_admin` (role guard) via FastAPI `Depends`. Routers receive only use cases and guards, never repositories or sessions directly.

## 5. Main Algorithms / Logic in Pseudocode

### 5.1 Registration (always USER)

```text
FUNCTION register(input):
  IF input.username is missing OR input.email is missing OR input.password is missing:
    RAISE validation error (required field)

  trimmed_email = TRIM(input.email)
  IF trimmed_email is empty:
    RAISE validation error (required field)

  IF input.username CONTAINS ANY whitespace:
    RAISE validation error (no-whitespace)   # never trim username

  IF LENGTH(input.username) < 8 OR LENGTH(input.username) > 20:
    RAISE validation error (username length)

  IF trimmed_email is NOT valid email shape:
    RAISE validation error (invalid email)

  IF LENGTH(input.password) < 8 OR LENGTH(input.password) > 20:
    RAISE validation error (password length)  # password is not trimmed

  IF repository.get_by_username(input.username) EXISTS:
    RAISE duplicate username

  IF repository.get_by_email_normalized(LOWER(trimmed_email)) EXISTS:
    RAISE duplicate email

  password_hash = hasher.hash(input.password)
  user = User(username=input.username, email=trimmed_email, password_hash=password_hash, role=USER)
  saved = repository.save(user)   # DB unique constraints are the final guard; map violations to 409

  RETURN user_output(saved) WITHOUT token
```

### 5.2 Login (token carries role)

```text
FUNCTION login(input):
  IF input.identifier is missing OR input.password is missing OR input.password is empty:
    RAISE validation error (required field)

  IF input.identifier CONTAINS "@":
    candidate = repository.get_by_email_normalized(LOWER(TRIM(input.identifier)))
  ELSE:
    IF input.identifier is empty:
      RAISE validation error (required field)
    # do NOT trim username identifiers; leading/trailing space means no match
    candidate = repository.get_by_username(input.identifier)

  IF candidate is null:
    RAISE invalid credentials (generic message)

  IF hasher.verify(input.password, candidate.password_hash) is FALSE:
    RAISE invalid credentials (same generic message)

  token = token_service.issue_token(candidate.id, candidate.username, candidate.role)
  RETURN login_output(token)
```

### 5.3 Promotion (admin only)

```text
FUNCTION promote(requester, target_user_id, new_role):
  IF requester is unauthenticated:
    RAISE authentication error (401)

  IF requester.role != ADMIN:
    RAISE forbidden error (403)   # nothing is changed

  IF new_role != ADMIN:
    RAISE validation error (invalid role, 400)

  target = repository.get_by_id(target_user_id)
  IF target is null:
    RAISE not-found error (404)

  target.role = ADMIN
  updated = repository.update(target)
  RETURN user_output(updated)
```

### 5.4 Admin seed (idempotent)

```text
FUNCTION ensure_admin_exists():
  admin_username = READ_ENV(ADMIN_USERNAME)
  admin_email = READ_ENV(ADMIN_EMAIL)
  admin_password = READ_ENV(ADMIN_PASSWORD)
  IF any is missing or empty:
    RAISE configuration error (fail fast, create nothing)

  trimmed_email = TRIM(admin_email)
  VALIDATE username, trimmed_email, and password with the SAME domain rules as register
  IF repository.get_by_email_normalized(LOWER(trimmed_email)) EXISTS:
    RETURN already_exists   # do not update, demote, or duplicate
  IF any existing user with role ADMIN EXISTS:
    RETURN already_exists   # seed runs once; later admins come from promotion

  password_hash = hasher.hash(admin_password)
  admin = User(username=admin_username, email=trimmed_email, password_hash=password_hash, role=ADMIN)
  repository.save(admin)   # UNIQUE constraints remain the final guard
  RETURN created (without logging the password)
```

### 5.5 Router Error Mapping

```text
POST /users/register:
  TRY execute register
  CATCH validation error -> 400
  CATCH duplicate username -> 409 (code: duplicate_username)
  CATCH duplicate email -> 409 (code: duplicate_email)

POST /users/login:
  TRY execute login
  CATCH validation error -> 400
  CATCH invalid credentials -> 401 with single message (e.g. invalid credentials)
  # no distinction between unknown user and wrong password at any layer

PATCH /users/{id}/role:
  REQUIRE authenticated user (401 if missing or invalid token)
  REQUIRE requester.role == ADMIN (403 otherwise)
  TRY execute promote
  CATCH validation error -> 400
  CATCH not-found -> 404
```

## 6. Key Technical Decisions with Discarded Alternatives

1. **Password hashing with Bcrypt via Passlib (already in stack).**
   Chosen because it is available, proven, and tutorial-free. Discarded: storing plain passwords (unacceptable security risk) and Argon2 (stronger in theory but not in the declared stack; adds dependency without spec benefit).

2. **Email format with Pydantic EmailStr at the DTO boundary.**
   Chosen because the spec clarification explicitly requests EmailStr and the entrypoint layer already uses Pydantic. Discarded: hand-rolled regex in domain (duplicates a well-tested validator and would import framework concerns into the domain, violating `AGENT.md`).

3. **Case-insensitive email uniqueness via a dedicated `email_normalized` column with UNIQUE.**
   Chosen for portability and race safety: every write computes `lower(trimmed)` and the database guarantees uniqueness even under concurrency. Discarded: PostgreSQL CITEXT (requires an extension and complicates migrations) and application-only pre-check without a DB constraint (vulnerable to race conditions).

4. **Case-sensitive username uniqueness via plain UNIQUE.**
   Chosen to implement BR-8 exactly with default binary comparison. Discarded: lowering usernames or CITEXT (would violate the spec that `User` differs from `user`).

5. **Stateless JWT via python-jose for login, now including the role claim (already in stack).**
   Chosen because the spec demands no logout and no server sessions; a signed token grants access and carries `role` for the admin guard without extra lookups. Discarded: server-side sessions or cookies (imply logout/destruction semantics the spec forbids) and per-request Basic Auth (leaks credentials on every call, no standard authenticated area). Discarded alternative of omitting role from the token (would force a DB lookup on every authorized call).

6. **Strict layering per `AGENT.md`: validation split between DTOs and domain.**
   DTOs handle transport shape (trim email, EmailStr); domain entities enforce business invariants (length, whitespace, role values); use cases orchestrate uniqueness, hashing, and authorization; infrastructure handles persistence, crypto, and seeding; entrypoints handle HTTP only. Discarded: putting SQLAlchemy or Pydantic inside `domain` (violates the zero-framework rule) and putting business rules inside routers (duplicates logic, hurts testability).

7. **No token on register; explicit 201 + frontend redirect.**
   Chosen to satisfy BR-1 and BR-2 literally. Discarded: auto-login on register (convenient but explicitly rejected during spec questions).

8. **Single generic 401 for all login failures; no enumeration.**
   Chosen for BR-10 and to avoid user enumeration. Discarded: distinct messages for unknown user vs wrong password (helpful for debugging but leaks account existence).

9. **Role as a constrained string (`USER`, `ADMIN`) with DEFAULT `USER` instead of a boolean flag.**
   Chosen because it is explicit, extensible, and maps directly to the spec language. Discarded: `is_admin` boolean (obscures the role vocabulary and complicates future roles) and client-controlled role on register (would allow privilege escalation; therefore the use case hardcodes `USER`).

10. **Admin-only promotion behind a dedicated use case plus route guard, and seed from environment.**
    Promotion is authorized from the validated token, never from body-supplied identity. The seed reads credentials exclusively from environment variables and is idempotent. Discarded: allowing self-promotion or registration with `role: ADMIN` (privilege escalation), direct database edits for promotion (no audit, no validation), and hardcoding seed credentials in source (violates the never-hardcode-secrets rule; environment is the only source).

## 7. Test Strategy

Aligned with Definition of Done in `AGENT.md` (linters clean, unit tests passing, docs updated). No implementation files are created in this plan.

- **Unit — domain entity (`tests/unit/test_user_entity.py`):**
  Username too short, too long, with leading/trailing/internal whitespace, empty; password too short, too long; email empty guard; role defaults to `USER`; invalid role rejected. Every spec Bad path that is length, whitespace, or role-shape related is covered here without database or frameworks.

- **Unit — use cases with fake in-memory repository (`tests/unit/test_register_user.py`, `test_login_user.py`, `test_promote_user.py`):**
  Register success returns user with `role: USER` and no token even when input contains a role field; duplicate username exact-case fails while different-case succeeds; duplicate email case-insensitive fails; email with surrounding spaces is trimmed and accepted; password boundaries 8 and 20 pass, 7 and 21 fail. Login success via email, via username, via differently-cased email, with token carrying the correct role; wrong password and unknown identifier both raise the same generic exception; empty identifier or password raises validation, not credentials. Promotion succeeds for admin requester, fails with forbidden for non-admin, fails with not-found for missing target, fails with validation for non-`ADMIN` role.

- **Integration — repository (`tests/integration/test_postgres_user_repository.py`):**
  Exact username lookup is case-sensitive; email lookup by lowered value is case-insensitive; UNIQUE on `username` and on `email_normalized` hold under direct concurrent inserts (expect one 409-mapped failure); trimmed email is what is persisted; role persists and round-trips; update changes role without altering other fields.

- **Integration — seed (`tests/integration/test_admin_seed.py`):**
  Empty database creates exactly one `ADMIN` satisfying domain rules; rerun creates nothing and changes nothing; existing admin by email (any casing) prevents duplicates; missing environment configuration fails fast without creating a user.

- **End-to-end — HTTP (`tests/e2e/test_user_register_router.py`, `test_user_login_router.py`, `test_user_promote_router.py`):**
  Full matrix from spec Scenarios: register 201 with `role: USER` then login 200; register with `role: ADMIN` in payload still yields `USER`; register duplicate username 409; register duplicate email with different case 409; register bad email 400; register short/long password 400; register short/long username 400; register username with spaces 400 (including ` user01AB ` to prove no silent trim); login wrong password 401; login unknown identifier 401 with identical body to wrong password; login missing fields 400; login response token decodes to the correct role. Promotion matrix: admin token plus valid target yields 200 and `ADMIN`; user token yields 403 with no change; missing token yields 401; unknown target yields 404; invalid role yields 400. Assert register response contains no token field.

- **Security and regression:**
  Stored password is a Bcrypt hash, never plain text (assert hash differs and verifies); seed and tests never log passwords; login error bodies for unknown user and wrong password are byte-identical except request echo; no logout or recovery routes exist (assert 404); role escalation via registration is impossible (assert `USER` regardless of payload); linters and formatters pass with zero errors before merge.
