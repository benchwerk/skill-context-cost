---
name: python-docstrings
description: Write Google-style docstrings for Python functions and methods. Use when asked to add, write, improve, or fix docstrings on Python code, or when new Python functions lack documentation.
---

# Python Google-style docstrings

Write a docstring for each Python function or method the user points at (or each undocumented one in the file or diff they name). Read the whole body first so the docstring reflects what the code does, including what it raises.

## Structure

```python
def fetch_user(user_id: int, *, timeout: float = 5.0) -> User:
    """Fetch a user record from the accounts service.

    Retries are not attempted; callers that need them should wrap this call.

    Args:
        user_id: Primary key of the user to fetch.
        timeout: Seconds to wait for the service before giving up.

    Returns:
        The matching user.

    Raises:
        UserNotFoundError: If no user has the given ID.
        TimeoutError: If the service does not respond within `timeout`.
    """
```

1. **Summary line**: one line, imperative mood ("Fetch...", not "Fetches..." or "This function fetches..."), ending in a period, fitting on the opening-quote line.
2. **Extended description** (optional): after a blank line, only when behavior, side effects, performance, or constraints are not obvious from the summary and signature. Skip it otherwise.
3. **Args**: one entry per parameter, in signature order, as `name: description`. Include `*args` and `**kwargs` with the star prefix. Omit `self` and `cls`. Do not repeat types that the annotations already give; if the function has no annotations, put the type in parentheses: `name (int): description`. Indent continuation lines by four extra spaces.
4. **Returns**: describe the meaning of the returned value, not just its type. Omit the section when the function returns `None`, unless the `None` carries meaning. For generators use `Yields:` instead. For tuples or dicts, describe each element or key.
5. **Raises**: list only exceptions the function's own code raises explicitly, or that propagate from calls in a way callers should expect and handle. Give the condition for each. Do not list generic exceptions that could come from anywhere (e.g. `MemoryError`). Omit the section if nothing applies.

Add `Attributes:`, `Example:`, or `Note:` sections only where they earn their space (for example, a short usage example for a non-obvious API).

## What to write

- Say what the function is for and what callers can rely on: the contract, units, valid ranges, defaults that matter, mutation of arguments, side effects, and ordering guarantees.
- Explain why, not how. Never narrate the implementation line by line ("loops over items, then appends...") and never restate the code in prose.
- Don't echo names: `x: The x value.` adds nothing. If a parameter is self-evident, keep its description short but still present, with units or constraints if any.
- Match the project's existing conventions if they differ in small ways (quote style, line length, section order). Default to triple double quotes and 79 to 88 columns unless the repo says otherwise.

## What to preserve

- Keep correct existing docstrings. Fix only what is wrong, missing, or stale, and convert other styles (reST, NumPy) to Google style only if asked or if the file is otherwise Google style.
- Never change code, signatures, or behavior. Edit docstrings only.
- Don't invent behavior. If the intent of a parameter or return value is unclear from the code and its callers, describe only what is verifiable rather than guessing.

## Special cases

- **Classes**: put a class docstring with summary and `Attributes:` on the class; document constructor arguments under `Args:` in the class docstring or in `__init__`, following the file's existing choice.
- **Properties**: a single summary line describing the value, not "Gets the...".
- **Overrides and trivial dunder methods**: a docstring is optional when the behavior is standard; skip rather than add noise.
- **Async functions**: document like sync ones; mention what is awaited only if it affects the contract.
- **Private helpers**: a one-line docstring is usually enough unless the logic is subtle.

## Final check

Before finishing, confirm for each docstring: the summary is one imperative line, every parameter is listed in order, `Raises` matches the `raise` statements actually in the code, and nothing merely paraphrases the implementation.
