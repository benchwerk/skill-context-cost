---
name: python-docstrings
description: Write Google-style docstrings for Python functions and methods. Use this skill whenever the user asks to add, write, fix, improve, or review docstrings, document a Python function, class method, or module, or says a function is "undocumented", even if they don't say "Google style". Also use when writing new Python functions that should ship with documentation.
---

# Python Google-style docstrings

A good docstring tells a caller what they need to use the function without reading its body. Code already says *how*; the docstring says *what*, *what goes in*, *what comes out*, and *what can go wrong*.

## Structure

```python
def fetch_user(user_id: int, include_deleted: bool = False) -> User:
    """Fetch a user record by ID.

    Longer description only if the summary isn't enough: behavior callers
    could trip over, side effects, performance notes, units, or invariants.

    Args:
        user_id: Primary key of the user to look up.
        include_deleted: If True, soft-deleted users are returned too.

    Returns:
        The matching User.

    Raises:
        UserNotFoundError: If no user matches `user_id`.
        DatabaseError: If the connection to the database fails.
    """
```

## Rules

1. **One-line summary.** Imperative mood ("Fetch", "Compute", not "Fetches" or "This function computes"), ends with a period, fits on one line (about 79 chars). It starts on the same line as the opening `"""`. Leave a blank line before any further text.
2. **Args.** List every parameter except `self`/`cls`, in signature order, as `name: description`. Include `*args` and `**kwargs` by name with the star. Describe meaning, units, allowed values, and defaults' effect, not just the type. If the function has type hints, do not repeat types; if it has none, give the type in parentheses: `name (int): ...`. Indent wrapped lines by four spaces.
3. **Returns.** Describe what is returned and any non-obvious structure (e.g. dict keys, tuple order, when `None` is returned). Skip the section when the function returns nothing. For generators use `Yields:` instead.
4. **Raises.** Include only exceptions the code visibly raises (`raise` statements) or that it deliberately propagates from a call callers should expect (e.g. `KeyError` from an unguarded lookup that is part of the contract). Read the body to find them. Don't list every conceivable exception, and omit the section if there are none.
5. **No line-by-line restating.** Never narrate the implementation ("loops over items, then appends to the list"). If a docstring only says what the code literally does, it adds noise and goes stale. Describe intent, contract, and surprises. Mention an algorithm only when it matters to callers (complexity, ordering guarantees, mutation).
6. **Document the non-obvious.** Mutation of arguments, side effects (I/O, network, global state), thread-safety, ordering, and units deserve a sentence. Trivial functions get just the summary line; a short `"""Return the user's full name."""` is correct for a simple getter.

## Process

1. Read the whole function, including nested calls that raise or mutate.
2. Write the summary from the caller's point of view.
3. Fill in Args/Returns/Raises only where there is something to say.
4. Check that the docstring matches the current signature and `raise` statements. When editing existing docstrings, preserve accurate content and fix drift rather than rewriting wholesale.
5. Match the file's existing conventions (quote style, line length, type-hint usage) when they differ from the above.

## Variants

- **Classes:** document the class with a summary and an `Attributes:` section for public attributes; document constructor parameters in `__init__`'s docstring or the class docstring, whichever the file already does.
- **Properties:** a single-line summary describing the value, not "Gets the...".
- **Overrides / dunder methods:** keep brief, or omit when behavior is the standard one.

## Example

Bad (restates the code):

```python
def mean(xs):
    """Loops through xs, adds up each value, divides by len(xs), returns it."""
```

Good:

```python
def mean(xs):
    """Compute the arithmetic mean of a sequence of numbers.

    Args:
        xs (Sequence[float]): Values to average. Must be non-empty.

    Returns:
        The mean as a float.

    Raises:
        ZeroDivisionError: If `xs` is empty.
    """
```
