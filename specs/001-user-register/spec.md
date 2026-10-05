# User Management — Register, Login and Roles

## 1. Objective

Enable visitors of **Personal Blog** to create a personal account and authenticate to access personalized features.

Problem solved: without user management, the blog cannot distinguish users or protect authenticated actions. This feature establishes identity with minimal friction, requiring only username, email, and password, while supporting a minimal role model so administration can be delegated safely.

Out of scope: email verification, password recovery, profile editing, logout, and abuse protection. Roles are limited to `USER` and `ADMIN`: registration always creates `USER`, and only an existing `ADMIN` can grant `ADMIN`. There is explicitly no logout option in this version.

## 2. Use Cases & User Flow

**Primary actors:**

*   Visitor (unauthenticated person)
*   Registered User (person with an active account, default role `USER`)
*   Admin (registered user with role `ADMIN`)

**Secondary actor:**

*   System (validates inputs, enforces uniqueness, authenticates, enforces role rules, seeds initial admin)

**Happy Path — Register + Login:**

1. Visitor opens registration form.
2. Visitor provides username, email, and password.
3. System validates presence, format, length, and uniqueness (email is trimmed; username is not trimmed).
4. System creates the account in active state with role `USER`.
5. System redirects to login form with success confirmation (no automatic login).
6. User provides identifier (email OR username) + password.
7. System validates credentials.
8. System grants access to authenticated area with the user's role. No logout action is offered.

Why manual login after register: confirms the user knows their credentials and that the account was created correctly before granting access.

Why default `USER`: prevents privilege escalation at registration; administration stays controlled.

**Admin Promotion Flow:**

1. Admin authenticates (same login as any user).
2. Admin requests promotion of an existing `USER` to `ADMIN`.
3. System verifies the requester is `ADMIN`, the target exists, and the role value is valid.
4. System grants `ADMIN` to the target.

**Initial Admin Seed Flow:**

1. On first deployment (or on demand), the system checks whether an `ADMIN` account exists.
2. If none exists, the system creates one from protected configuration (environment), with role `ADMIN`.
3. If it already exists, the system leaves it untouched (idempotent).

## 3. Business Rules

**Preconditions:**

*   User is unauthenticated to register.
*   User must have an active registered account to log in.
*   No email verification step is required; account is active immediately after registration.
*   At least one `ADMIN` exists via seed before any promotion can happen.

**Required inputs:**

*   Register: username (required, 8-20 characters, no whitespace), email (required, valid standard format, length unrestricted), password (required, 8-20 characters). Role is never requested at registration. No other fields are requested.
*   Login: identifier (required, accepts either username OR email) + password (required).
*   Promote: target user identity + role `ADMIN`. Requester must be authenticated as `ADMIN`.

**Operation rules:**

*   BR-1 Active on creation: successful registration leaves account active and redirects to login.
*   BR-2 No auto-login: system must NOT start a session automatically after registration.
*   BR-3 Trimming limited to email: system must remove leading/trailing spaces from email (register and login) before validation. Username is never trimmed: any username containing whitespace, including leading/trailing spaces, is rejected.
*   BR-4 Username constraints: username must be 8-20 characters inclusive, must contain no whitespace characters anywhere. Examples of invalid: `my user01`, ` user01AB`, `user01AB `.
*   BR-5 Email format: email must have a valid standard email format after trimming. Length is unrestricted. Invalid format is rejected. Whitespace-only email counts as empty.
*   BR-6 Password length: password must be 8-20 characters inclusive. No complexity requirements. Password is not trimmed.
*   BR-7 Flexible login identifier: login accepts either the registered username or the registered email, plus the correct password.
*   BR-8 Username uniqueness case-sensitive: `User01AB` is different from `user01ab`. Exact-case duplicate usernames are rejected.
*   BR-9 Email uniqueness case-insensitive: `Test@mail.com` and `test@mail.com` are considered the same. Duplicate emails regardless of case are rejected.
*   BR-10 Generic failure message: failed login (unknown identifier OR wrong password) must show the same generic message without revealing which part failed.
*   BR-11 No lockout, no abuse protection: system does not block accounts or apply rate-limiting/captcha after failed attempts in this version.
*   BR-12 No logout, no recovery: system offers no logout action and no password recovery/reset in this version.
*   BR-13 Role model: every user has exactly one role, either `USER` or `ADMIN`. No other roles exist in this version.
*   BR-14 Default role on register: every self-registration creates a `USER`, even if a role value is sent by the client (client-supplied role is ignored). Only the seed path can create the first `ADMIN`.
*   BR-15 Admin-only promotion: only a user with role `ADMIN` can grant `ADMIN` to another existing user. Non-admin requests are rejected with forbidden, without changing anything.
*   BR-16 Initial admin seed: the system provisions one `ADMIN` from protected configuration when none exists. The seed is idempotent: running it when the admin already exists changes nothing and never duplicates accounts or demotes anyone.

**System limits:**

*   One account per username value (case-sensitive) and one per email value (case-insensitive).
*   Username under 8 or over 20 characters is invalid. Password under 8 or over 20 characters is invalid.
*   Role is restricted to `USER` and `ADMIN`.

## 4. Scenarios

**Well — Successful paths:**

*   Context: visitor without account, registration form displayed -> When: submits new unique username (8-20 chars, no spaces), valid email, password 8-20 chars -> Then: account created as active with role `USER` and redirected to login with success confirmation.
*   Context: visitor enters `  user@mail.com  ` as email with valid username and password -> When: submits registration -> Then: system trims email to `user@mail.com` and creates the account with role `USER`.
*   Context: registered user on login form -> When: submits registered email + correct password -> Then: authenticated and granted access with their role.
*   Context: registered user on login form -> When: submits registered username + correct password -> Then: authenticated and granted access with their role.
*   Context: registered email is `User@mail.com`, login attempted with `user@mail.com` + correct password -> When: submits login -> Then: authenticated (email match is case-insensitive).
*   Context: authenticated admin selects an existing user with role `USER` -> When: requests promotion to `ADMIN` -> Then: target role becomes `ADMIN`.
*   Context: system has no admin yet -> When: seed runs -> Then: one `ADMIN` account is created from protected configuration.
*   Context: admin from seed already exists -> When: seed runs again -> Then: nothing changes (no duplicate, no demotion).

**Bad — Failure paths:**

*   Context: registration form -> When: submits username already registered (exact case match) -> Then: rejected with duplicate username error, no account created.
*   Context: registration form -> When: submits email already registered with different casing -> Then: rejected with duplicate email error, no account created.
*   Context: registration form -> When: submits username shorter than 8 or longer than 20 characters -> Then: rejected with length error.
*   Context: registration form -> When: submits username containing any whitespace (e.g. `my user01`, ` user01AB`, `user01AB `) -> Then: rejected with no-whitespace error, never trimmed and accepted.
*   Context: registration form -> When: submits email with invalid format -> Then: rejected with invalid email error.
*   Context: registration form -> When: submits password shorter than 8 or longer than 20 characters -> Then: rejected with length error.
*   Context: registration form -> When: submits with any of username/email/password empty or email whitespace-only -> Then: rejected with required field error.
*   Context: registration form -> When: submits a role value such as `ADMIN` alongside valid data -> Then: account is still created as `USER` (client role is ignored).
*   Context: authenticated non-admin attempts promotion -> When: requests promotion of any user to `ADMIN` -> Then: rejected with forbidden, target role unchanged.
*   Context: authenticated admin attempts promotion -> When: target user does not exist -> Then: rejected with not-found, nothing changes.
*   Context: authenticated admin attempts promotion -> When: role value is not `ADMIN` -> Then: rejected with invalid role error.
*   Context: login form with valid account -> When: submits correct identifier but wrong password -> Then: rejected with generic invalid credentials message.
*   Context: login form -> When: submits unregistered identifier with any password -> Then: rejected with same generic invalid credentials message as wrong password.

## [NECESITA ACLARACIÓN]

*   Sin puntos pendientes. Todas las dudas fueron resueltas.
