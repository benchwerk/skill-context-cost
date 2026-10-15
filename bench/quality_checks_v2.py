"""Version 2 of the mechanical checks: the same 16 prohibitions with the regular-expression weaknesses found by an independent review
(Antigravity, 2026-10-03, which read the code and four generated pages) repaired. The primary analysis of the study keeps the
original checks (quality_checks.py, hash in env.json); version 2 is a secondary, exploratory sensitivity analysis computed offline
from the saved pages. Changes: HTML entities are decoded and comments removed before searching; every fenced block is joined (HTML,
CSS and JavaScript may be split); case-insensitive version labels; wider detection of equal three-column grids, pure black,
section-number separators and inline SVG icons; middle dots counted per line and per 400 characters of visible text."""
import html as htmllib
import re

TAG = re.compile(r"<[^>]+>")
STYLE_SCRIPT = re.compile(r"<(style|script)\b[\s\S]*?</\1>", re.I)
COMMENT = re.compile(r"<!--[\s\S]*?-->|/\*[\s\S]*?\*/")


def prepare(reply):
    blocks = re.findall(r"```[a-zA-Z]*\s*\n([\s\S]*?)```", reply)
    raw = "\n".join(blocks) if blocks else (reply if re.search(r"<html|<!doctype|<body", reply, re.I) else "")
    if not raw:
        return None, None
    h = htmllib.unescape(COMMENT.sub(" ", raw))
    t = htmllib.unescape(TAG.sub(" ", STYLE_SCRIPT.sub(" ", COMMENT.sub(" ", raw))))
    return h, t


def dots_ok(t):
    if any(line.count("·") >= 2 for line in t.splitlines()):
        return False
    pos = [m.start() for m in re.finditer("·", t)]
    return not any(pos[i + 2] - pos[i] <= 400 for i in range(len(pos) - 2))


CHECKS = {
    "no_pure_black": lambda h, t: not re.search(r"(?i)(#000(000)?([0-9a-f]{2})?\b(?![\w-])|(?<![a-z])rgba?\(\s*0[\s,]+0[\s,]+0\s*\)|(?<![-\w])(color|background(-color)?)\s*:\s*black\b)", h),
    "no_em_dash": lambda h, t: "—" not in h,
    "no_filler_verbs": lambda h, t: not re.search(r"(?i)\b(elevate[sd]?|seamless(ly)?|unleash(es|ed)?|next-gen|revolutioni[sz]e[sd]?)\b", t),
    "no_slop_brand_names": lambda h, t: not re.search(r"(?i)\b(acme|nexus|smartflow|cloudly)\b", t),
    "no_generic_names": lambda h, t: not re.search(r"(?i)\b(john doe|jane doe|sarah chan|jack su)\b", t),
    "no_inter_font": lambda h, t: not re.search(r"(?i)(font-family\s*:[^;}]*\binter\b|family=Inter\b)", h),
    "no_fake_perfect_numbers": lambda h, t: not re.search(r"(99\.99\s*%|99\.9\s*%|\b1,?234,?567\b)", t),
    "no_step_stage_labels": lambda h, t: not re.search(r"(?i)\b(step|stage|phase|pass)\s*(0?\d\b|one\b|two\b|three\b)", t),
    "no_section_number_eyebrows": lambda h, t: not re.search(r"(?m)(^|\s)0\d\s*[/·\-.]\s*[A-Za-z]", t),
    "no_version_labels": lambda h, t: not re.search(r"(?i)(\bv\d+\.\d+(\.\d+)?\b|\bbeta\b|\bearly access\b|\binvite-only\b|\balpha\b)", t),
    "middle_dot_rationed": lambda h, t: dots_ok(t),
    "no_unsplash": lambda h, t: not re.search(r"(?i)unsplash\.com", h),
    "no_custom_cursor": lambda h, t: not re.search(r"(?i)cursor\s*:\s*(url|none)", h),
    "no_gradient_text": lambda h, t: not re.search(r"(?i)background-clip\s*:\s*text", h),
    "no_three_equal_cards": lambda h, t: not re.search(r"(?i)(grid-template-columns\s*:\s*(repeat\(\s*3\s*,|1fr\s+1fr\s+1fr\b)|\bgrid-cols-3\b)", h),
    "no_handrolled_svg_icons": lambda h, t: not re.search(r"(?i)<svg\b[\s\S]*?<(path|circle|rect|polygon|polyline|line|ellipse)\b", h),
}


def run_checks_v2(reply):
    h, t = prepare(reply)
    if h is None:
        return {"has_html": False, "results": {}}
    return {"has_html": True, "results": {k: bool(fn(h, t)) for k, fn in CHECKS.items()}}
