---
name: api-error-check
description: Review a REST API handler (or route/controller/middleware) for consistent error responses. Checks status codes, a JSON error body with `code` and `message`, no leaked stack traces or internal paths, and correct 4xx vs 5xx usage. Use when the user asks to audit, review, or check error handling in an API endpoint, handler, or controller.
---

# API Error Response Check

Audit the error paths of a REST API handler and report concrete findings with fixes.

## Scope

Use the file(s), function, or route the user names. If none is named, look for handlers in the current change or the most likely route/controller files. Read the handler and any shared error helpers, middleware, or global error handler it relies on. Errors are often normalized in one central place, so check there before flagging per-handler issues.

## Checklist

For every error path (explicit returns/throws, caught exceptions, validation failures, auth checks, not-found cases, uncaught exceptions):

1. **Status code is correct**
   - 400 malformed or invalid input; 422 if the project uses it for semantic validation failures
   - 401 missing or invalid authentication; 403 authenticated but not allowed
   - 404 resource missing; 405 wrong method; 409 conflict or duplicate; 429 rate limited
   - 500 unexpected server fault; 502/503/504 for upstream or availability problems
   - Flag: 200 with an error body, 500 for client mistakes, 4xx for server faults, 404 used to hide a 403 without justification, generic 400 for everything.

2. **Body is JSON with `code` and `message`**
   - Shape such as `{"code": "...", "message": "..."}` (optionally `details`, `requestId`).
   - `code` should be a stable machine-readable identifier; `message` human-readable.
   - Content-Type is `application/json`, not HTML or plain text, including for framework defaults (404/405/500 pages, body-parser errors).
   - Flag: bare strings, differing field names (`error`, `msg`, `err`) across paths, missing fields, shape that differs between handlers.

3. **No leaks**
   - No stack traces, exception class names, raw `err.message`/`str(e)` from internals, SQL or driver errors, file system paths, hostnames, secrets, or config values in responses.
   - Debug or dev mode flags that expose traces must not be on by default or in production.
   - Internal detail belongs in server logs, ideally correlated by a request ID returned to the client.
   - Validation `details` must not echo sensitive input (passwords, tokens).

4. **4xx vs 5xx discipline**
   - Anything caused by the caller is 4xx and is not logged as an error-level incident.
   - Unexpected exceptions are 5xx with a generic message, and are logged with full detail.
   - Catch-all handlers must not turn client errors into 500, or server faults into 4xx.

5. **Consistency and coverage**
   - Every path uses the same helper or shape; no ad hoc `res.status(...).send(...)` mixed with the standard one.
   - Async errors are caught (unhandled promise rejections, missing try/catch, missing error middleware).
   - Auth failures don't reveal whether an account or resource exists unless intended.
   - Relevant headers are present where required (`WWW-Authenticate` on 401, `Retry-After` on 429/503, `Allow` on 405).

## Output

Report in this form:

- **Summary**: one or two sentences with the overall verdict.
- **Findings**: a table or list ordered by severity (leaks first, then wrong status, then body shape, then consistency). Each item: `file:line`, the problem, why it matters, and a concrete fix (a short code snippet when helpful).
- **Passed checks**: brief list of what was verified fine, so the user knows what was covered.
- **Not verified**: anything you could not see (e.g. a global error handler in another file, production config).

If asked to fix the issues, make minimal edits that reuse the project's existing error helper. If none exists, suggest one small shared helper rather than inlining changes everywhere. Do not invent findings; if the handler is clean, say so.
