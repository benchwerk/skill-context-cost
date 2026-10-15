"""Mechanical checks for the design-taste-frontend skill, each taken from a prohibition in the skill's own section 9
("AI tells"). A check passes when the forbidden pattern is ABSENT from the generated HTML. They are heuristics on text:
they count what a regular expression can see, not what a person would judge. Written before any output was generated."""
import re

TAG = re.compile(r"<[^>]+>")
STYLE_SCRIPT = re.compile(r"<(style|script)\b[\s\S]*?</\1>", re.I)


def visible_text(html):
    return TAG.sub(" ", STYLE_SCRIPT.sub(" ", html))


def extract_html(reply):
    """The largest fenced code block, else the reply itself if it looks like HTML, else ''."""
    blocks = re.findall(r"```(?:html|HTML)?\s*\n([\s\S]*?)```", reply)
    if blocks:
        return max(blocks, key=len)
    return reply if re.search(r"<html|<!doctype|<body", reply, re.I) else ""


CHECKS = {
    "no_pure_black": ("9.A: no pure black (#000000)", lambda h, t: not re.search(r"(?i)(#000(000)?\b(?!\w)|(?<!a)rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)|(?<![-\w])(color|background(-color)?)\s*:\s*black\b)", h)),
    "no_em_dash": ("9.F/9.G: no em-dash anywhere", lambda h, t: "—" not in h),
    "no_filler_verbs": ("9.D: no Elevate / Seamless / Unleash / Next-Gen / Revolutionize", lambda h, t: not re.search(r"(?i)\b(elevate[sd]?|seamless(ly)?|unleash(es|ed)?|next-gen|revolutioni[sz]e[sd]?)\b", t)),
    "no_slop_brand_names": ("9.D: no Acme / Nexus / SmartFlow / Cloudly", lambda h, t: not re.search(r"(?i)\b(acme|nexus|smartflow|cloudly)\b", t)),
    "no_generic_names": ("9.D: no John Doe / Jane Doe / Sarah Chan / Jack Su", lambda h, t: not re.search(r"(?i)\b(john doe|jane doe|sarah chan|jack su)\b", t)),
    "no_inter_font": ("9.B: avoid Inter as the default font", lambda h, t: not re.search(r"(?i)(font-family\s*:[^;}]*\binter\b|family=Inter\b)", h)),
    "no_fake_perfect_numbers": ("9.D: no 99.99% / 99.9% / 1,234,567", lambda h, t: not re.search(r"(99\.99\s*%|99\.9\s*%|\b1,?234,?567\b)", t)),
    "no_step_stage_labels": ("9.F: no Step 1 / Stage 1 / Phase 01 labels", lambda h, t: not re.search(r"(?i)\b(step|stage|phase|pass)\s*(0?\d\b|one\b|two\b|three\b)", t)),
    "no_section_number_eyebrows": ("9.F: no 00 / INDEX style section numbers", lambda h, t: not re.search(r"(?m)(^|\s)0\d\s*[/·]\s*[A-Za-z]", t)),
    "no_version_labels": ("9.F: no V0.6 / BETA / EARLY ACCESS eyebrows", lambda h, t: not re.search(r"(\bv\d+\.\d+(\.\d+)?\b|\bBETA\b|\bEARLY ACCESS\b|\bINVITE-ONLY\b|\bALPHA\b)", t)),
    "middle_dot_rationed": ("9.F: at most one middle dot per line", lambda h, t: not any(line.count("·") >= 2 for line in t.splitlines())),
    "no_unsplash": ("9.E: no Unsplash links", lambda h, t: not re.search(r"(?i)unsplash\.com", h)),
    "no_custom_cursor": ("9.A: no custom mouse cursors", lambda h, t: not re.search(r"(?i)cursor\s*:\s*(url|none)", h)),
    "no_gradient_text": ("9.A: no gradient text", lambda h, t: not re.search(r"(?i)background-clip\s*:\s*text", h)),
    "no_three_equal_cards": ("9.C: no three equal columns (grid repeat(3, 1fr))", lambda h, t: not re.search(r"(?i)grid-template-columns\s*:\s*repeat\(\s*3\s*,\s*(1fr|minmax)", h)),
    "no_handrolled_svg_icons": ("9.E: no hand-rolled inline SVG icons", lambda h, t: not re.search(r"(?i)<svg\b[\s\S]*?<path", h)),
}


def run_checks(reply):
    html = extract_html(reply)
    if not html:
        return {"has_html": False, "results": {}}
    t = visible_text(html)
    return {"has_html": True, "html_chars": len(html), "results": {k: bool(fn(html, t)) for k, (_, fn) in CHECKS.items()}}
