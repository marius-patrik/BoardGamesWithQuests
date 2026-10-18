---
status: accepted
---
# Direct Supabase Auth identity and bearer-based API security

## Decision

Accepted C1 option B in #350. The single React client, also displayed inside Tauri, owns identities and session management using the official version-pinned Supabase Auth JavaScript SDK. Guests call `signInAnonymously()`; registered users use Supabase email/password/password recovery and optional enabled OAuth providers. Convert anonymous users to permanent accounts by **identity linking** (verified email or `linkIdentity`) while preserving the same provider Auth UUID and all game membership/progression. Logging into a separate existing account is not a silent identity merge.

Private FastAPI routes require `Authorization: Bearer <access JWT>`; use project-scoped issuer/audience/expiry/signature validation (JWKS when the project uses asymmetric keys, provider-backed validation when using HS256), immutable `sub` UUID and private database membership/ownership checks. Supabase Auth owns tokens, password, email verification, MFA/refresh/revocation; no FastAPI `GET /session`, `/auth/*` identity proxy, application cookie-backed session or duplicate password store. Application `GET/PATCH /me` owns only application profile data.

## Consequences

The desired application API now has **27 proposed operations** rather than 33, with **26 proposed DTO components** rather than 28. These counts are editable design inventory, **not** a contract asserted by CI; the actual OpenAPI derives only from FastAPI after implementation. Native/single-page auth uses browser-side token management, so XSS/CSP, redirect allowlisting/PKCE, CORS, token refresh, tab isolation, sensitive operation session-liveness and WebView persistence require explicit review. An anonymous Supabase user carries the database `authenticated` role; always authorize by UUID and membership, not role alone. Supabase's same-IP anonymous-signup throttling and default limited email delivery require real classroom/provider acceptance. Better Auth introduces an unnecessary parallel TypeScript identity backend in this architecture and is not selected.
