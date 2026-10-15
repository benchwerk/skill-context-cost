---
name: python-docstrings
description: Write or revise Google-style docstrings for Python functions and methods. Use when the user asks to add, fix, or review docstrings, document a Python function, or when writing new Python functions that need documentation. Produces a one-line summary, Args, Returns, and Raises (only where the code raises), without restating the code line by line.
---

# Python Google-style docstrings

Document what a function *promises to its callers*, not how it works inside.

## Process

1. Read the whole function, including the signature, type hints, `raise` statements, and any helpers whose exceptions propagate on purpose.
2. Write the docstring using the template below.
3. Insert it directly under the `def` line. Change nothing else in the code unless asked.
4. If a docstring already exists, keep any accurate content and fix what is stale or wrong rather than rewriting from scratch.

## Template

```python
def fetch_user(user_id: int, *, include_deleted: bool = False) -> User:
    """Fetch a user record by ID.

    Longer description only if the summary is not enough: context,
    side effects, performance notes, or non-obvious behavior.

    Args:
        user_id: Primary key of the user.
        include_deleted: Whether soft-deleted users may be returned.

    Returns:
        The matching user.

    Raises:
        UserNotFoundError: If no user matches `user_id`.
        PermissionError: If the caller lacks read access.
    """
```

## Rules

**Summary line**
- One line, imperative mood ("Fetch...", "Return...", "Compute..."), ending in a period, fitting on the opening-quote line.
- Say what the function does for the caller, not how. Never just repeat the function name ("Fetch user." for `fetch_user` adds nothing; add the useful detail).
- A blank line follows before any further text.

**Args**
- List every parameter in signature order, including `*args` and `**kwargs` (written as `*args:` / `**kwargs:`). Omit `self` and `cls`.
- Format: `name: Description.` Do not repeat the type when a type hint exists. If there are no hints, give the type in parentheses: `name (int): Description.`
- Describe meaning, units, valid ranges, allowed values, defaults whose behavior is not obvious, and whether `None` is accepted. Do not write "The user_id."
- Continuation lines are indented 4 extra spaces.
- Omit the section if the function takes no parameters.

**Returns**
- Describe the meaning of the returned value, not just its type. For tuples or dicts, say what each element or key holds.
- Omit the section when the function returns nothing (`None` implicit). Do not write "Returns: None".
- For generators use `Yields:` instead of `Returns:`.

**Raises**
- Include only exceptions the function itself raises or deliberately lets propagate as part of its contract. Find them by reading the `raise` statements and the calls that are expected to fail.
- Do not invent exceptions, and do not list ones that merely could happen (e.g. `MemoryError`, `KeyboardInterrupt`).
- Format: `ExceptionType: Condition under which it is raised.`
- Omit the section when nothing is raised.

**No line-by-line restating**
- Bad: "Loops over items, checks if each is None, and appends it to a list."
- Good: "Return the non-null items, preserving order."
- Do not narrate the implementation. Add a longer description only for things a reader cannot see from the signature: side effects (I/O, mutation of arguments, global state), thread-safety, idempotency, complexity, or surprising edge cases.
- Do not add comments or docstring text for trivial behavior. Trivial one-liners (simple getters, obvious wrappers) get a one-line docstring and no sections.

## Special cases

- **Methods:** document behavior on the class, not `self`. Put constructor arguments in the class docstring or `__init__`, following the surrounding code's convention.
- **Properties:** a one-line summary describing the value ("The user's display name."), no Returns section.
- **Async functions:** document as normal; describe the awaited result in Returns.
- **Overrides:** if the method fully honors the parent's contract, a short summary is fine; mention only the differences.
- **Mutation:** if an argument is modified in place, say so in its Args entry.
- **Examples:** add an `Example:` section only when usage is not obvious. Keep it short and correct.

## Style

- Use triple double quotes `"""`.
- Match the project's existing docstring conventions (line length, quoting of identifiers with backticks, sentence case) when they differ from the above.
- Keep line length within the project's limit (default 88, or 79 if the project uses it).
- Avoid filler such as "This function..." or "Helper to...".
- Make sure the docstring matches the code. If the code and its type hints disagree, or a raised exception is undocumentable, flag it to the user rather than guessing.
