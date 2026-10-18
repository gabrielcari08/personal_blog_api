# Technical Plan — Frontend (003-frontend)

This plan answers HOW the `spec.md` will be implemented. It respects Clean Architecture and the layer rules from `AGENT.md` (Presentation, Application Logic & State, Service & Infrastructure, Domain & Utility) and consumes the existing backend contract (`/api/v1` from specs `001-user-register` and `002-articles`). No implementation code is included here, only contracts, structures, and pseudocode.

> **Frontend layout note:** the frontend lives in `frontend/`. All `src/`, `index.html`, and test paths in this document are relative to `frontend/`, and every command (dev, build, lint, test) must be run from `frontend/`.

## 1. Functional Requirements Mapping to Modules

| Spec rule | Module responsible | Notes |
|---|---|---|
| BR-1 Public reading (list + detail, no session) | `pages/HomePage.jsx`, `pages/ArticleDetailPage.jsx`, `hooks/use_articles.js`, `hooks/use_article.js`, `services/article_service.js` | Reads call the backend with no auth; list arrives already ordered most-recent-first. |
| BR-2 Client validation mirrors backend | `utils/validators.js` + feature form components | Reused constant rules; submission blocked while invalid, but the backend stays authoritative. |
| BR-3 Exact backend messages surfaced | `utils/api_errors.js`, form components | Maps the backend `detail` field to the corresponding form/field without rewording. |
| BR-4 Inline form errors | `components/features/auth/*`, `components/features/article/ArticleForm.jsx` | Field-level error props rendered under each input. |
| BR-5 Toasts for action results | `context/ToastContext.jsx`, `components/ui/Toast.jsx`, `utils/messages.js` | Single toast surface for create/edit/delete/promote. |
| BR-6 Generic login failure | `services/auth_service.js`, `components/features/auth/LoginForm.jsx` | Any 401 from login maps to one generic message; cause never distinguished. |
| BR-7 No auto-login after register | `pages/RegisterPage.jsx`, `hooks/use_auth.js` | On register success navigate to login with a success confirmation; no token stored. |
| BR-8 Persistent session, no logout | `context/AuthContext.jsx`, `utils/storage.js` | Token persisted in `localStorage`; no logout control is rendered anywhere. |
| BR-9 Session expiry handling | `api/client.js` (response interceptor), `context/AuthContext.jsx`, `routes/ProtectedRoute.jsx`, `utils/messages.js` | On 401: clear session, redirect to login with a session-expired notice and intended-route return. |
| BR-10 Ownership-aware controls | `utils/permissions.js`, `components/features/article/ArticleCard.jsx`, `ArticleDetail.jsx` | `can_edit(article, user)` = owner OR ADMIN; controls hidden otherwise. |
| BR-11 Direct deletion, no confirmation | `hooks/use_article.js`, `ArticleDetail.jsx` | Delete fires immediately; no `Modal` confirmation step. |
| BR-12 Author/time read-only | `components/features/article/ArticleForm.jsx` | Form contains only title/text; author/time never rendered as editable or sent. |
| BR-13 Immediate visibility | `hooks/use_articles.js` | List is refetched (or optimistically updated) after create so the item appears at once. |
| BR-14 Admin-only dashboard | `pages/AdminDashboardPage.jsx`, `components/features/admin/RequireAdmin.jsx`, `routes/ProtectedRoute.jsx` | Route guard rejects non-admins; navbar entry hidden. |
| BR-15 Dark theme only | `tailwind.config.js`, `src/index.css`, `components/layout/*` | Single dark palette; no theme switch and no light tokens. |
| BR-16 Responsive layout | Tailwind responsive utilities across `pages/` and `components/` | Mobile-first breakpoints; forms and reading usable at small widths. |
| BR-17 Loading and empty states | `components/ui/Spinner.jsx`, `components/ui/EmptyState.jsx`, `hooks/use_*` | Hooks expose `loading`/`error`/`data`; empty list renders an empty state. |
| BR-18 Network/backend failure | `api/client.js`, `utils/api_errors.js`, `components/ui/ErrorState.jsx`, `ToastContext` | Non-2xx/exception mapped to a non-technical message; never a blank screen. |
| Use case: Public reading | `HomePage` -> `use_articles` -> `article_service.getAll` | No guard on read routes. |
| Use case: Register | `RegisterForm` -> `use_auth.register` -> `auth_service.register` | Returns no token; navigate to login. |
| Use case: Login | `LoginForm` -> `use_auth.login` -> `auth_service.login` -> `AuthContext` | Stores token, decodes claims, applies role. |
| Use case: Create/Edit/Delete article | `ArticleForm`/`ArticleDetail` -> `use_article` -> `article_service` | Mutations behind `ProtectedRoute`. |
| Use case: Admin promote | `AdminDashboardPage` -> `UserTable` -> `use_admin_users` -> `user_service.promote` | Behind `RequireAdmin`; consumes the users list endpoint. |
| Explicit non-goals | No logout, no recovery, no theme toggle, no pagination controls, no comments/likes/tags | Documented to avoid accidental introduction. |

## 2. Folder and File Structure

New project under `frontend/`, following the layer names in `AGENT.md` Section 5–8.

```text
frontend/
├── index.html
├── package.json
├── vite.config.js                     # dev server + /api proxy + env handling
├── tailwind.config.js                 # dark palette, content globs
├── postcss.config.js
├── eslint.config.js
├── .env.example                       # VITE_API_BASE_URL (/api/v1)
└── src/
    ├── main.jsx                       # mounts App with providers
    ├── App.jsx                        # router tree + global providers
    ├── index.css                      # Tailwind directives + dark base tokens
    ├── api/
    │   └── client.js                  # Axios instance: baseURL, JWT request interceptor, 401 response interceptor
    ├── services/
    │   ├── auth_service.js            # register(), login()
    │   ├── article_service.js         # getAll(), getById(), create(), update(), remove()
    │   └── user_service.js            # list(), promote()
    ├── context/
    │   ├── AuthContext.jsx            # session lifecycle, current user, expiry handling (no logout)
    │   └── ToastContext.jsx           # toast queue provider + renderer
    ├── hooks/
    │   ├── use_auth.js                # register/login actions + auth state selectors
    │   ├── use_articles.js            # list loading/error/refetch
    │   ├── use_article.js             # single load, create, update, delete
    │   └── use_admin_users.js         # users list + promote action
    ├── components/
    │   ├── ui/                        # atomic, business-agnostic, Tailwind only
    │   │   ├── Button.jsx
    │   │   ├── Input.jsx
    │   │   ├── Textarea.jsx
    │   │   ├── FieldError.jsx
    │   │   ├── Spinner.jsx
    │   │   ├── EmptyState.jsx
    │   │   ├── ErrorState.jsx
    │   │   ├── Toast.jsx
    │   │   └── Modal.jsx              # generic (not used for delete confirmation)
    │   ├── layout/
    │   │   ├── Navbar.jsx             # public links + auth-aware actions (no logout)
    │   │   └── PageContainer.jsx
    │   └── features/
    │       ├── auth/
    │       │   ├── LoginForm.jsx
    │       │   └── RegisterForm.jsx
    │       ├── article/
    │       │   ├── ArticleCard.jsx
    │       │   ├── ArticleList.jsx
    │       │   ├── ArticleDetail.jsx
    │       │   └── ArticleForm.jsx
    │       └── admin/
    │           ├── UserTable.jsx
    │           └── RequireAdmin.jsx
    ├── pages/
    │   ├── HomePage.jsx
    │   ├── ArticleDetailPage.jsx
    │   ├── ArticleCreatePage.jsx
    │   ├── ArticleEditPage.jsx
    │   ├── LoginPage.jsx
    │   ├── RegisterPage.jsx
    │   ├── AdminDashboardPage.jsx
    │   └── NotFoundPage.jsx
    ├── routes/
    │   ├── ProtectedRoute.jsx         # requires session
    │   └── GuestRoute.jsx             # redirects logged users away from login/register
    ├── utils/
    │   ├── storage.js                 # localStorage wrapper (token key)
    │   ├── jwt.js                     # decode claims (user_id, username, role, exp)
    │   ├── validators.js              # rules mirroring backend
    │   ├── api_errors.js              # error envelope -> { fieldErrors, globalMessage, code }
    │   ├── permissions.js             # can_manage_article(), is_admin()
    │   ├── date.js                    # ISO-8601 UTC -> local display
    │   └── messages.js                # literal success/notice/error copy
    └── types/
        └── models.js                  # JSDoc typedefs: User, Article, AuthSession, ApiError
```

Tests mirror `frontend/tests/`:

```text
tests/
├── unit/
│   ├── validators.test.js
│   ├── jwt.test.js
│   ├── permissions.test.js
│   ├── api_errors.test.js
│   └── date.test.js
├── component/
│   ├── LoginForm.test.jsx
│   ├── RegisterForm.test.jsx
│   ├── ArticleForm.test.jsx
│   ├── ArticleCard.test.jsx
│   └── UserTable.test.jsx
├── integration/
│   ├── auth_flow.test.jsx
│   ├── article_crud.test.jsx
│   └── admin_promote.test.jsx
└── msw/
    └── handlers.js                  # shared mock backend for integration tests
```

## 3. Data Model / Schemas

### 3.1 Client session model

`AuthSession` (derived from the login token, held in `AuthContext` and persisted by `storage.js`):

- `access_token`: string, opaque bearer token returned by login; the only value persisted.
- `user_id`: string/int, decoded from the token `user_id` claim.
- `username`: string, decoded from the token `username` claim.
- `role`: literal `USER` | `ADMIN`, decoded from the token `role` claim.
- `expires_at`: number, decoded from the token `exp` claim; used for local pre-emptive expiry checks.

Invariants:

- A session is considered valid only while `access_token` exists and `expires_at` is in the future.
- The session never exposes or stores the password.
- No logout mutation exists; the only ways a session ends are token expiry or a backend 401.

### 3.2 View models

`Article` (from `ArticleOutput`):

- `id`: identifier.
- `title`: string, 8-20 characters.
- `text`: string, 10-300 characters.
- `user_id`: owner reference; the only known author signal from the backend.
- `created_at`: ISO-8601 UTC timestamp; formatted locally for display.

`User` (from `UserOutput` / users list):

- `id`, `username`, `email`, `role` (`USER` | `ADMIN`).

`ApiError` (normalized from the backend envelope `{ detail, code }`):

- `status`: HTTP status.
- `code`: stable backend code (`validation_error`, `duplicate_username`, `duplicate_email`, `invalid_credentials`, `forbidden`, `article_not_found`, ...).
- `globalMessage`: human message for form-level or page-level display.
- `fieldErrors`: map of field name -> message (only for field-addressable validation errors).

### 3.3 Form state shapes

- `RegisterFormState`: `{ username, email, password }` (raw, never pre-trimmed client-side to preserve the backend's whitespace rules; email may be trimmed on blur only for display convenience but the raw value is validated as typed).
- `LoginFormState`: `{ identifier, password }`.
- `ArticleFormState`: `{ title, text }` only.

### 3.4 Validation constants (must stay in sync with backend spec)

- `USERNAME`: length 8-20, no whitespace anywhere.
- `EMAIL`: valid standard format after trimming.
- `PASSWORD`: length 8-20, no complexity, not trimmed.
- `TITLE`: length 8-20, raw length, no trim.
- `TEXT`: required non-empty; non-empty length 10-300, raw length, no trim.
- Exact messages: `title must be 8-20 characters`, `text must be 10-300 characters`, `text is required`.

### 3.5 Persistence keys and config

- `localStorage` key: one namespaced token key (e.g. `personal_blog.access_token`). Only the token string is stored.
- Config: `VITE_API_BASE_URL` defaults to `/api/v1`; the dev server proxies `/api` to the backend so the browser never hardcodes host/port.

### 3.6 Backend response reliance

The frontend consumes the existing envelope: success payloads are the resource objects; failures carry `detail` (+ `code`). The login response exposes only `access_token` and `token_type`; identity fields come from the token claims, not from a profile endpoint.

## 4. Interface / API / Signature Contracts

### 4.1 HTTP API consumed (base `/api/v1`)

| Endpoint | Method | Auth | Used by | Success | Failure surfaced |
|---|---|---|---|---|---|
| `/users/register` | POST | none | `auth_service.register` | 201 + user | 400 field errors, 409 duplicate inline |
| `/users/login` | POST | none | `auth_service.login` | 200 + `access_token` | 400 field error, 401 generic inline |
| `/users` | GET | bearer ADMIN | `user_service.list` | 200 + user array | 403 forbidden, 401 session |
| `/users/{id}/role` | PATCH | bearer ADMIN | `user_service.promote` | 200 + updated user | 400/403/404, 401 session |
| `/articles` | GET | none | `article_service.getAll` | 200 + article array | 5xx -> page error |
| `/articles/{id}` | GET | none | `article_service.getById` | 200 + article | 404 not-found page |
| `/articles` | POST | bearer | `article_service.create` | 201 + article | 400 inline, 401 session |
| `/articles/{id}` | PUT | bearer | `article_service.update` | 200 + article | 400/403/404, 401 session |
| `/articles/{id}` | DELETE | bearer | `article_service.remove` | 204 | 403/404, 401 session |

Note: `GET /users` is a **backend dependency** (see §6, Decision 11); the current backend specs do not define a users-list route. The frontend contract assumes it exists; until then the promotion feature is blocked.

### 4.2 Service signatures (pure functions over the HTTP client)

- `auth_service.register(payload: RegisterFormState) -> User` — POST register, no token.
- `auth_service.login(payload: LoginFormState) -> { access_token }` — POST login.
- `article_service.getAll() -> Article[]` — public list.
- `article_service.getById(id) -> Article` — public single.
- `article_service.create(payload: ArticleFormState) -> Article` — authenticated.
- `article_service.update(id, payload: ArticleFormState) -> Article` — authenticated.
- `article_service.remove(id) -> void` — authenticated, expects 204.
- `user_service.list() -> User[]` — ADMIN only.
- `user_service.promote(id) -> User` — ADMIN only; body sends `role: "ADMIN"`.

All service functions throw a normalized `ApiError`; none touch React state.

### 4.3 HTTP client contract (`api/client.js`)

- Request interceptor: if a token exists and is not expired, attach `Authorization: Bearer <token>`.
- Response interceptor (success): pass through.
- Response interceptor (error): normalize to `ApiError`; on `401` emit a `session-expired` event that `AuthContext` subscribes to (clear session + redirect). Login's own 401 is excluded from the global handler (handled inline by `LoginForm`).
- Network/timeout errors normalize to `ApiError` with `code: network_error`.

### 4.4 Context contracts

- `AuthContext` value: `{ session, user, isAuthenticated, isAdmin, login(payload), register(payload), handleSessionExpired() }`. **No `logout`.**
- `ToastContext` value: `{ showToast({ type, message }) }`; renders a stacked toast region.

### 4.5 Hook contracts

- `use_auth() -> { session, user, isAuthenticated, isAdmin, login, register, loginError, isSubmitting }`.
- `use_articles() -> { articles, loading, error, refetch }`.
- `use_article(id?) -> { article, loading, error, create, update, remove, isSubmitting }`.
- `use_admin_users() -> { users, loading, error, refetch, promote, promotingId }`.

Hooks own data fetching and side effects; components stay presentational and call hooks only (per `AGENT.md` Section 5).

### 4.6 Guard components / routes

- `ProtectedRoute`: if no valid session -> redirect to `/login?reason=session_expired` (or intended route preserved via `state.from`).
- `GuestRoute`: if a valid session exists -> redirect to `/`.
- `RequireAdmin`: if session valid but `role !== ADMIN` -> redirect to `/` and never render the dashboard entry.

Route table:

- `/` -> `HomePage` (public)
- `/articles/:id` -> `ArticleDetailPage` (public)
- `/articles/new` -> `ArticleCreatePage` (protected)
- `/articles/:id/edit` -> `ArticleEditPage` (protected; ownership enforced by hiding + backend 403)
- `/login` -> `LoginPage` (guest)
- `/register` -> `RegisterPage` (guest)
- `/admin` -> `AdminDashboardPage` (protected + admin)
- `*` -> `NotFoundPage`

### 4.7 Component prop contracts (selection)

- `Button`: `{ variant: primary|secondary|danger|ghost, loading, disabled, type }`.
- `Input` / `Textarea`: `{ label, value, onChange, error, maxLength, ... }`.
- `FieldError`: `{ message }`.
- `ArticleCard`: `{ article, canManage, onDelete }`.
- `ArticleForm`: `{ initialValues, onSubmit, submitting, fieldErrors }`.
- `UserTable`: `{ users, onPromote, promotingId }`.
- `EmptyState` / `ErrorState`: `{ title, message, action? }`.

## 5. Main Algorithms / Pseudocode

### 5.1 Session bootstrap (app start)

```text
FUNCTION bootstrap_session():
  raw_token = storage.get_token()
  IF raw_token is null OR raw_token is empty:
    RETURN no_session

  claims = jwt.decode(raw_token)        # user_id, username, role, exp
  IF claims is invalid OR jwt.is_expired(claims):
    storage.clear_token()
    RETURN no_session                   # no redirect on first load; routes decide

  RETURN session(access_token=raw_token, user_id=claims.user_id,
                 username=claims.username, role=claims.role, expires_at=claims.exp)
```

### 5.2 Request/response interception

```text
FUNCTION attach_token(config):
  token = storage.get_token()
  IF token exists AND NOT jwt.is_expired(jwt.decode(token)):
    config.headers.Authorization = "Bearer " + token
  RETURN config

FUNCTION handle_error(error):
  IF error has no response:             # network/timeout
    RETURN normalize(status=0, code="network_error", globalMessage=generic_copy())

  status = error.response.status
  body = error.response.data           # { detail, code }
  api_error = normalize(status, body.code, body.detail)

  IF status == 401 AND request is NOT the login call:
    storage.clear_token()
    emit("session-expired")             # AuthContext clears session + redirects

  RAISE api_error
```

### 5.3 Auth context expiry subscription

```text
FUNCTION on_session_expired():
  clear session in context
  navigate_to_login(reason="session_expired", from=current_route)   # no toast-only fallback
```

### 5.4 Login flow

```text
FUNCTION login(payload):
  fieldErrors = validators.validate_login(payload)     # required fields only
  IF fieldErrors not empty: RETURN fieldErrors

  TRY:
    result = auth_service.login(payload)
  CATCH api_error:
    IF api_error.code == "invalid_credentials":
      RETURN { global: generic_message }               # BR-6: single message
    IF api_error.status == 400:
      RETURN { fieldErrors: api_error.fieldErrors }
    RETURN { global: generic_copy() }

  claims = jwt.decode(result.access_token)             # never trust without decode
  storage.set_token(result.access_token)
  set_session(claims + token)
  navigate(to = intended_route OR "/")                 # BR-7 default is the article list
```

### 5.5 Register flow

```text
FUNCTION register(payload):
  fieldErrors = validators.validate_register(payload)  # mirror backend rules
  IF fieldErrors not empty: RETURN fieldErrors

  TRY:
    auth_service.register(payload)
  CATCH api_error:
    IF api_error.status == 409:                        # duplicate username/email
      RETURN { fieldErrors: address by code }
    IF api_error.status == 400:
      RETURN { fieldErrors: api_error.fieldErrors }
    RETURN { global: generic_copy() }

  # BR-7: no token, no session -> go to login
  navigate("/login", state={ notice: register_success_copy() })   # inline confirmation on login page
```

### 5.6 Article list (public)

```text
FUNCTION load_articles():
  state.loading = true
  TRY:
    state.articles = article_service.getAll()          # already newest-first from backend
  CATCH api_error:
    state.error = api_error.globalMessage
  FINALLY:
    state.loading = false

  RENDER:
    IF loading: Spinner
    ELSE IF error: ErrorState(message=error)
    ELSE IF articles empty: EmptyState
    ELSE: ArticleList(articles, canManage=permissions per card)
```

### 5.7 Ownership control logic

```text
FUNCTION can_manage_article(article, session):
  IF session is null: RETURN false
  IF session.role == "ADMIN": RETURN true
  RETURN session.user_id == article.user_id            # BR-10
```

### 5.8 Create / Edit / Delete

```text
FUNCTION create_article(payload):
  fieldErrors = validators.validate_article(payload)   # BR-2, exact rules
  IF fieldErrors not empty: RETURN fieldErrors
  TRY:
    article_service.create(payload)
    toast.show(article_created_copy())                 # BR-5, BR-13
    navigate and refetch list
  CATCH api_error:
    RETURN inline(fieldErrors OR exact message by code)  # BR-3

FUNCTION update_article(id, payload):
  same validation/submission as create but PUT
  on success: toast.show(article_updated_copy()); refetch

FUNCTION delete_article(id, article):
  REQUIRE permissions.can_manage_article(article, session)   # UI gate; backend is final
  # BR-11: no confirmation dialog
  TRY:
    article_service.remove(id)
    toast.show(article_deleted_copy())
    navigate to "/" and refetch list
  CATCH api_error:
    IF code == "article_not_found": toast.show(not_found_copy()); refetch list
    ELSE IF status == 403: toast.show(forbidden_copy())
    ELSE: toast.show(generic_copy())
```

### 5.9 Admin dashboard: list + promote

```text
FUNCTION load_users():
  REQUIRE session.role == "ADMIN"                      # BR-14
  state.loading = true
  TRY:
    state.users = user_service.list()
  CATCH api_error:
    state.error = api_error.globalMessage
  FINALLY:
    state.loading = false

FUNCTION promote(user):
  IF user.role == "ADMIN": RETURN                     # only USER -> ADMIN
  TRY:
    updated = user_service.promote(user.id)           # body { role: "ADMIN" }
    replace updated in state.users
    toast.show(user_promoted_copy())
  CATCH api_error:
    IF status == 403: toast.show(forbidden_copy())
    ELSE IF status == 404: toast.show(generic_not_found_copy())
    ELSE: toast.show(generic_copy())
```

### 5.10 Error normalization

```text
FUNCTION normalize(status, code, detail):
  fieldErrors = {}
  IF code is a known duplicate/invalid code:
    fieldErrors = map_code_to_field(code, detail)      # e.g. duplicate_username -> username
  ELSE IF code == "validation_error":
    fieldErrors = parse_detail_fields(detail)          # best-effort field mapping
  RETURN ApiError(status, code, globalMessage=detail OR generic_copy(), fieldErrors)
```

### 5.11 Presentational helpers

```text
FUNCTION format_created_at(iso_utc):
  RETURN to_local_display(parse_iso(iso_utc))          # AGENT.md: ISO 8601 UTC -> local tz

FUNCTION author_label(article, session):
  IF session AND session.user_id == article.user_id: RETURN "You"
  RETURN "Author #" + article.user_id                  # see Decision 10 (backend dependency)
```

## 6. Key Technical Decisions with Discarded Alternatives

1. **Single-page app with Vite + React as the frontend build (already the declared stack).**
   Chosen because the stack in `AGENT.md` is React with Tailwind and an SPA maps cleanly to the routed views of the spec. Discarded: a server-rendered meta-framework (adds a Node server the current FastAPI-only architecture does not have) and a no-build mult-page app (loses component reuse and shared session context).

2. **Axios instance with interceptors as the single HTTP boundary (`api/client.js`).**
   Chosen because token attachment, 401 handling, and error normalization belong in one place, matching the `AGENT.md` service/infrastructure layer. Discarded: raw `fetch` scattered per service (repeats header/error logic) and a state library's built-in fetcher (couples transport to view state, harder to test in isolation).

3. **Token persisted in `localStorage`, no logout.**
   Chosen to satisfy BR-8 literally: the session must survive refresh and browser restart, and the spec forbids a logout control. Discarded: `sessionStorage` (does not survive browser restart, violates BR-8), in-memory only (lost on refresh), and httpOnly cookies (the backend issues a bearer token in the response body, not a cookie, so this would require backend changes).

4. **Identity derived by decoding the JWT claims client-side, not a new profile endpoint.**
   Chosen because the login token already carries `user_id`, `username`, and `role`, so the ownership/role logic (BR-10, BR-14) needs no extra request. Discarded: adding a `GET /me` endpoint (new backend surface not in scope) and re-fetching the user after login (redundant round-trip).

5. **Auth in React Context, remote data in custom hooks; no global state library.**
   Chosen because only the session is truly global; article/user data is view-scoped and belongs in hooks (`AGENT.md` Sections 6-7). Discarded: Redux/Zustand (adds boilerplate and a dependency for state the app does not need) and prop-drilling session data (fragile and verbose).

6. **Route guards as wrapper components (`ProtectedRoute`, `GuestRoute`, `RequireAdmin`).**
   Chosen so access rules are declared once per route and cannot be forgotten in page bodies. Discarded: inline `if (!session) return <Redirect/>` in every page (duplicated, error-prone) and hiding links only (does not protect direct URL entry).

7. **Dark-only Tailwind theme with a fixed palette; no theme provider.**
   Chosen to implement BR-15 exactly and avoid dead toggle code. Discarded: a light/dark toggle (explicitly out of scope) and a CSS-in-JS theming library (unnecessary given Tailwind is in the stack).

8. **Client-side validation mirrors but never replaces backend validation.**
   Chosen for responsiveness (BR-2) while keeping the backend authoritative; exact messages (BR-3) are surfaced from the API. Discarded: client-only validation (unsafe; backend remains the guard) and no client validation (poor UX with avoidable round-trips).

9. **Custom lightweight toast context instead of a toast library.**
   Chosen to keep the dependency surface minimal and the styling consistent with the dark theme. Discarded: `react-toastify`/similar (extra dependency and theming friction for one small feature) and full-page banners for action results (heavier UX than the spec's toast decision).

10. **Author shown as a derived reference (`You` / `Author #<user_id>`) until the backend exposes a display name.**
    Chosen because `ArticleOutput` only provides `user_id`; this keeps the UI honest without inventing data. Discarded: fetching each author's full record (no public per-user endpoint exists) and hiding authors entirely (loses the spec's "author reference"). This is flagged as a backend dependency: adding `username`/author name to `ArticleOutput` would let the UI show a real name.

11. **Admin dashboard consumes a `GET /users` list endpoint (backend dependency).**
    Chosen because BR-14 and the promote flow require selecting an existing user, but the current backend specs expose no users-list route. The plan defines `user_service.list()` against `GET /api/v1/users`; this route must be added to the backend before the dashboard is functional. Discarded: promote-by-id free text (poor UX and requires the admin to know internal ids) and client-side user inventory (impossible; the frontend has no user directory).

12. **Forced re-login after promotion; admin controls appear only after a fresh login.**
    Because the role lives inside the signed token and no logout/refresh-token exists, a user promoted during an active session keeps the old `role` claim until expiry or a new login. The plan documents this as a known limitation rather than adding logout/refresh machinery the spec forbids. Discarded: client-side role override (would desync from the backend's authoritative token) and silent token refresh (no refresh endpoint exists).

13. **Centralized literal copy in `utils/messages.js`.**
    Chosen so the previously undefined success and session-expired texts live in one place and stay consistent. Discarded: inline strings per component (drift and translation pain) and a full i18n framework (overkill; the spec is single-language and out of scope).

14. **List refetch after mutations (no optimistic delete on the public list).**
    Chosen for correctness around the backend's most-recent-first ordering and 404/403 edge cases. Discarded: optimistic UI without reconciliation (can show deleted items on failure) and full-page reloads (loses the SPA session experience).

## 7. Test Strategy

Aligned with the `AGENT.md` Definition of Done (linters/formatters clean, tests passing, docs updated). Tests use Vitest with React Testing Library; integration tests mock the backend with MSW handlers derived from the API table in §4.1. No implementation code is created in this plan.

- **Unit — validators (`tests/unit/validators.test.js`):**
  Username 7/8/20/21 boundaries and whitespace (leading, trailing, internal) rejected; email format and trimming behavior; password 7/8/20/21; title 7/8/20/21 raw length (spaces/emoji counted, no trim); text empty -> `text is required`, 9/10/300/301 boundaries -> `text must be 10-300 characters`. Assert the exact spec strings.

- **Unit — jwt (`tests/unit/jwt.test.js`):**
  Decoding valid claims yields `user_id`, `username`, `role`, `exp`; malformed token returns null/throws normalized error; expired token is detected by `is_expired`.

- **Unit — permissions (`tests/unit/permissions.test.js`):**
  `can_manage_article` true for ADMIN on any article, true for owner USER, false for non-owner USER, false with no session.

- **Unit — api_errors (`tests/unit/api_errors.test.js`):**
  Maps `duplicate_username`/`duplicate_email` to the right field; `validation_error` detail parsed to field errors; `invalid_credentials` yields a single global generic message; network error (no response) maps to `network_error`; 5xx maps to a non-technical generic message.

- **Unit — date (`tests/unit/date.test.js`):**
  ISO-8601 UTC input renders in local time; invalid input degrades gracefully.

- **Component — forms and cards (`tests/component/*.test.jsx`):**
  `LoginForm` blocks submit when empty, shows inline generic message on 401, calls `login` once. `RegisterForm` mirrors backend rules, shows duplicate errors inline, navigates to login on success with no token stored. `ArticleForm` shows exact title/text messages and never renders author/time fields. `ArticleCard` hides edit/delete for non-owner USER and shows them for owner and ADMIN. `UserTable` disables/hides promote for rows already `ADMIN`.

- **Integration — flows (`tests/integration/*.test.jsx`):**
  `auth_flow`: register -> redirected to login with confirmation -> login -> session persisted in `localStorage` -> survives a simulated reload -> a 401 response clears the session and redirects to login with the session-expired notice. `article_crud`: public list renders (no token) -> create appears -> edit updates -> delete removes without any confirmation dialog and a success toast shows. `admin_promote`: non-admin is redirected away from `/admin` and sees no entry point; admin lists users and promotes a `USER`, seeing the role update and a toast.

- **Security and regression:**
  Assert no logout control exists anywhere; assert author/time are never sent in create/update payloads (extra fields ignored); assert expired/invalid token triggers exactly one redirect to login; assert a 403 on a direct edit/delete URL shows a permission error and leaves data unchanged; linters and formatters pass with zero errors before merge.
