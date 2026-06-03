"""LaTeX content validator — regex-based checks for common issues."""

from __future__ import annotations

import re


def _count_unmatched(s: str, left: str, right: str) -> int:
    """Count unmatched pairs. Positive = unmatched left, negative = unmatched right."""
    count = 0
    i = 0
    while i < len(s):
        if s[i] == left:
            count += 1
            i += 1
        elif s[i] == right:
            count -= 1
            i += 1
        elif s[i] == "\\" and i + 1 < len(s):
            i += 2
        else:
            i += 1
    return count


def validate_latex(tex_content: str) -> list[str]:
    """Check LaTeX content for common issues.

    Returns a list of warning messages. Empty list = valid.
    """
    warnings: list[str] = []

    if r"\begin{document}" not in tex_content:
        warnings.append("Missing \\begin{document}")
    if r"\end{document}" not in tex_content:
        warnings.append("Missing \\end{document}")

    if "\\section{}" in tex_content:
        warnings.append("Empty \\section{} found")

    if re.search(r"(?<!\\)\{SECTION_NOTES\}", tex_content):
        warnings.append("Raw LaTeX command found in content")

    brace_count = _count_unmatched(tex_content, "{", "}")
    if brace_count != 0:
        warnings.append(f"Unmatched braces: {brace_count} extra {{{'{' if brace_count > 0 else '}'}}}")

    if re.search(r"[{}]\s*\n\s*[{}]", tex_content):
        warnings.append("Suspicious empty brace pattern")

    unescaped_special = re.findall(r"(?<!\\)[&%$#_~^]", tex_content)
    if unescaped_special:
        warnings.append(f"Possible unescaped special characters: {len(unescaped_special)} occurrences")

    if "None" in tex_content:
        warnings.append("Literal 'None' found in output — likely unset template variable")

    if "\x00" in tex_content or "\x01" in tex_content:
        warnings.append("Null bytes or control characters found in output")

    lines = tex_content.split("\n")
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.search(r"\\textbf\{\s*\}", stripped):
            warnings.append(f"Line {i}: Empty \\textbf{{}}")
        if stripped == r"\item":
            warnings.append(f"Line {i}: Empty \\item")

    return warnings
