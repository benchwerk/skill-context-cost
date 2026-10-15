---
name: api-error-check
description: Review a REST API handler (or route/controller/middleware) for consistent error responses. Checks status codes, a JSON error body with `code` and `message`, no leaked stack traces or internal paths, and correct 4xx vs 5xx usage. Use when the user asks to check, audit, or review API error handling, error responses, or status codes in endpoint code.
---

# API error response check

Review the handler code the user points to (a file, function, route, or diff). If no target is given, look at the handler(s) in the current file or the most recently discussed one. Read the handler plus any shared error helper, error middleware, or exception mapper it relies on, since the real response is often built there.

Report findings; do not change code unless the user asks.

## What to check

### 1. Status codes
- Every error path sets an explicit status code. Flag paths that return `200` with an error payload, or that fall through to a framework default without intent.
- Codes match the situation:
  - `400` malformed or invalid input; `422` if the API uses it for semantic validation (be consistent)
  - `401` missing or invalid credentials; `403` authenticated but not allowed
  - `404` resource not found; `405` wrong method; `409` conflict or duplicate; `429` rate limited
  - `500` unexpected server failure; `502`/`503`/`504` for upstream or availability problems
- The same failure uses the same code everywhere in the handler (e.g. "not found" is not `404` in one branch and `400` in another).

### 2. 4xx vs 5xx
- 4xx means the client can fix it. 5xx means the server failed. Flag:
  - Validation, auth, or not-found errors returned as `500` (often an uncaught exception or a catch-all that wraps everything).
  - Server faults (DB down, null dereference, upstream timeout) returned as `4xx`.
  - A blanket `catch` that maps all exceptions to one code. Typed or expected errors should map to 4xx; only unexpected ones to 500.
- Check that expected-error exceptions are not swallowed into a generic 500 and that unexpected ones are not reported as 400.

### 3. JSON body shape
- Error responses are JSON with `Content-Type: application/json`, not HTML, plain text, or an empty body.
- The body contains a machine-readable `code` (stable string or number, e.g. `"user_not_found"`) and a human-readable `message`. Optional extras (`details`, `field`, `requestId`) are fine if used consistently.
- Shape is identical across all error paths in the handler and matches any existing convention in the codebase (error helper, OpenAPI spec, other handlers). Note deviations, including different key names (`error` vs `message`, `msg`, `errorCode`).
- `code` is not just the HTTP status echoed back unless that is the project convention.

### 4. No leaks
Flag any error response that can include:
- Stack traces, `err.stack`, `traceback.format_exc()`, or raw exception objects serialized into the body.
- Internal file paths, module names, or line numbers.
- Raw exception messages from the DB, ORM, or HTTP client (SQL text, table or column names, connection strings, hostnames, IPs).
- Secrets, tokens, or config values.
- Debug mode behavior that returns details in production (check for `DEBUG`, `NODE_ENV`, `app.debug` gates; a debug flag that is on by default is a finding).
- Framework default error pages or handlers that expose traces when an exception is unhandled; confirm a global error handler exists.

Details for debugging belong in server-side logs, optionally linked via a `requestId`. Confirm the error is logged server-side, not only returned.

### 5. Coverage
- Unhandled promise rejections, uncaught exceptions, async errors not forwarded to the error handler (e.g. missing `next(err)` or try/catch around `await`).
- Unknown routes and unsupported methods produce the same JSON error shape.
- Early returns after sending an error (no double response, no continuing execution).

## Output format

Start with a one-line verdict: **Consistent**, **Mostly consistent**, or **Inconsistent**.

Then list findings, most severe first. Leaks and 4xx/5xx misuse rank above style issues. For each:

- **Severity**: High / Medium / Low
- **Location**: `file:line`
- **Problem**: what is wrong, in one or two sentences
- **Fix**: the minimal change, with a short code snippet when helpful

End with a short list of what was checked and found correct, and note anything you could not verify (for example, error middleware or a shared helper outside the files you saw).

If there are no problems, say so plainly and do not invent findings.
