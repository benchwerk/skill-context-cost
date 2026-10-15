"""SKILL.md helpers shared by build_workload.py and run.py: frontmatter parsing and the two mechanical variants."""
import json
import re

FM = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
KEY = re.compile(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$")
BLOCK = {">", ">-", ">+", "|", "|-", "|+"}


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def frontmatter(text):
    """Flat key -> string (block scalars and continuation lines joined with single spaces)."""
    m = FM.match(text)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        kv = KEY.match(line)
        if kv and not line.startswith((" ", "\t")):
            key = kv.group(1)
            out[key] = "" if kv.group(2).strip() in BLOCK else kv.group(2).strip()
        elif key is not None and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return {k: _unquote(v) for k, v in out.items()}


def listing_chars(fm):
    """Characters the documentation says the listing carries per skill: description plus when_to_use, cut at 1,536."""
    return min(len((fm.get("description") or "") + (" " + fm["when_to_use"] if fm.get("when_to_use") else "")), 1536)


def _key_span(lines, key):
    """(start, end) line indexes of `key:` and its indented continuation lines, or None."""
    for i, line in enumerate(lines):
        kv = KEY.match(line)
        if kv and kv.group(1) == key and not line.startswith((" ", "\t")):
            j = i + 1
            while j < len(lines) and lines[j].startswith((" ", "\t")):
                j += 1
            return i, j
    return None


def _edit_frontmatter(text, fn):
    m = FM.match(text)
    if not m:
        raise ValueError("no frontmatter")
    nl = "\r\n" if "\r\n" in m.group(0) else "\n"
    lines = m.group(1).split("\r\n") if nl == "\r\n" else m.group(1).split("\n")
    lines = fn(lines)
    return text[:m.start(1)] + nl.join(lines) + text[m.end(1):]


def disable_model_invocation(text):
    """Set `disable-model-invocation: true` (replacing an existing value); every other key and the body are untouched."""
    def fn(lines):
        span = _key_span(lines, "disable-model-invocation")
        if span:
            lines[span[0]:span[1]] = ["disable-model-invocation: true"]
        else:
            lines.append("disable-model-invocation: true")
        return lines
    return _edit_frontmatter(text, fn)


def trim_description(text, limit):
    """Cut only the description value at a word boundary within `limit` characters and write it as a quoted
    single-line string. Every other key (including when_to_use) and the body are unchanged."""
    fm = frontmatter(text)
    d = fm["description"]
    if len(d) > limit:
        d = d[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")

    def fn(lines):
        span = _key_span(lines, "description")
        lines[span[0]:span[1]] = ["description: " + json.dumps(d, ensure_ascii=False)]
        return lines
    return _edit_frontmatter(text, fn)


def replace_body(text, new_body):
    """Keep the frontmatter, replace everything after it."""
    m = FM.match(text)
    return (text[:m.end()] if m else "") + new_body.strip() + "\n"


def split_sections(text, core_chars):
    """Mechanical split into a core and on-demand reference files (progressive disclosure).
    The frontmatter and the first sections of the body stay in SKILL.md while their total stays within `core_chars`
    (the introduction before the first '## ' always stays). Every later top-level section ('## ' or '# ', outside code
    fences) becomes references/NN-<slug>.md, and SKILL.md ends with an index of them. No sentence is edited.
    Returns (new SKILL.md text, {relative path: content})."""
    m = FM.match(text)
    head, body = (text[:m.end()], text[m.end():]) if m else ("", text)
    parts, cur, fence = [], [], False
    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{1,2}\s", line) and cur:
            parts.append("".join(cur))
            cur = []
        cur.append(line)
    parts.append("".join(cur))
    core, used, rest = [parts[0]], len(parts[0]), []
    for p in parts[1:]:
        if not rest and used + len(p) <= core_chars:
            core.append(p)
            used += len(p)
        else:
            rest.append(p)
    files, index = {}, []
    for i, p in enumerate(rest, 1):
        title = p.splitlines()[0].lstrip("# ").strip()
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or f"part-{i}"
        path = f"references/{i:02d}-{slug}.md"
        files[path] = p
        index.append(f"- `{path}`: {title[:90]}")
    new = head + "".join(core).rstrip() + "\n\n## References (read the one you need)\n\n" + "\n".join(index) + "\n"
    return new, files
