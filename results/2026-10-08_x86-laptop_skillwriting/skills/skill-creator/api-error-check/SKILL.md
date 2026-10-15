---
name: api-error-check
description: Review a REST API handler (or router/controller/middleware) for consistent, safe error responses - correct HTTP status codes, a JSON body with `code` and `message`, no stack traces or internal paths leaked, and 4xx vs 5xx used correctly. Use this whenever the user asks to check, audit, review, or harden error handling in an API endpoint, route, controller, or handler (Express, FastAPI, Flask, Django, Spring, Gin, ASP.NET, etc.), or asks "are my error responses okay?", "do we leak stack traces?", "which status code should this return?", even if they don't say "error response" explicitly.
---

# API error response check

Clients and operators depend on error responses being predictable. Inconsistent shapes force clients into brittle parsing, wrong status codes break retries and monitoring, and leaked internals help attackers. This skill reviews handler code against four criteria and reports concrete findings.

## Workflow

1. **Locate the scope.** Read the handler the user named. Also find what it relies on: global error handlers/middleware, exception mappers, shared error helpers, and framework defaults (e.g. debug mode, default error pages). A handler that looks fine may be undermined by a global handler, or rescued by one, so read both.
2. **Enumerate every error path** in the handler: explicit error returns/throws, validation failures, auth checks, not-found lookups, conflict cases, calls to databases or downstream services that can fail, and uncaught exceptions (what happens when nothing catches them?).
3. **Check each path against the criteria below.**
4. **Report findings**, then offer or apply fixes if the user wants them. Do not edit code unless asked.

## Criteria

### 1. Correct status codes
Match the code to what actually went wrong:
- 400 malformed request; 422 well-formed but semantically invalid (pick one convention for validation and use it everywhere)
- 401 missing/invalid credentials; 403 authenticated but not allowed
- 404 resource does not exist; 405 wrong method; 409 state conflict/duplicate; 429 rate limited
- 500 unexpected server fault; 502/503/504 for upstream failure, unavailability, timeout

Flag: errors returned with 200 (`{"success": false}`), 500 for client mistakes (bad input causing an unhandled exception), 404 used for authorization failures where it isn't an intentional choice, 401/403 mixed up, and generic 400 for everything.

### 2. Consistent JSON body with `code` and `message`
Every error response, from every path including framework-generated ones (404 for unknown routes, 405, body-parse failures, auth middleware), should share one shape, e.g.:

```json
{ "code": "USER_NOT_FOUND", "message": "No user with that id." }
```

Check that: `code` is a stable machine-readable string (or the project's established convention), `message` is human-readable, the Content-Type is `application/json` (not HTML or plain text), and fields are not renamed between paths (`error` vs `message` vs `msg`). Extra fields such as `details` or `request_id` are fine if consistent. If the project already has an error shape, treat that as the standard and flag deviations; otherwise recommend the shape above.

### 3. No leaked internals
Responses must not contain stack traces, file paths, SQL or query text, raw exception messages from libraries or the database, framework/version banners, internal hostnames, or config values. Look for: `str(e)` / `err.message` / `err.stack` / `e.getMessage()` placed into the response, debug flags (`DEBUG=True`, `app.debug`, Express default error handler outside production, `server.error.include-stacktrace`), and echoing the raw upstream error body. The right pattern is to log the full detail server-side with a correlation id, and return a generic message (optionally including that id so support can find the log).

Also confirm the detail is actually logged. Hiding it from the response while swallowing it entirely trades one problem for another.

### 4. 4xx vs 5xx used correctly
4xx means the caller can fix it; 5xx means the server (or something it depends on) failed. Flag misclassification in either direction: validation/lookup errors surfacing as 500 because an exception was not caught, and genuine server faults (DB down, null dereference, upstream timeout) reported as 400/404, which hides outages from alerting and tells clients not to retry. Check that catch-all handlers default to 500 and that specific exceptions map to specific 4xx codes rather than the reverse.

## Output format

Start with a one-line verdict, then a table or list of findings, most severe first (leaks and wrong 5xx/4xx classification before style inconsistencies):

```
Verdict: <N issues: X high, Y medium, Z low>

1. [HIGH] <criterion> - <file>:<line>
   Problem: <what the code does>
   Impact: <why it matters>
   Fix: <specific change, with a short code snippet when helpful>
```

End with a short "Paths checked" list so the user can see coverage, and note anything you could not verify (e.g. a global handler that lives outside the files you were given). If everything passes, say so plainly rather than inventing issues.
