import re

REMOVE_PATTERNS = [r"第?\s*\d{1,3}\s*页", r"Page\s*\d+", r"\d+\s*/\s*\d+", r"版权所有.*", r"保密.*", r"Confidential.*", r"免责声明.*", ]


def is_catalog_line(line: str) -> bool:
    """determine if a line is part of a catalog or table of contents."""
    line = line.strip()
    if len(line) < 10:
        return False
    if re.search(r"[·•\.・\s]{6,}", line):
        if re.search(r"[ixv\d]{1,5}$", line, re.IGNORECASE):
            return True
    if re.match(r"^\d+(\.\d+)*\s", line):
        return True
    return False


def clean_whitespace(line: str) -> str:
    """clean Chinese whitespace in a line - only keep spaces adjacent to English letters and merge multiple spaces"""

    def should_keep_space(s: str, idx: int) -> bool:
        if s[idx] != ' ':
            return True
        prev_char = s[idx - 1] if idx > 0 else ''
        next_char = s[idx + 1] if idx + 1 < len(s) else ''

        prev_is_english = prev_char.isascii() and prev_char.isalpha()
        next_is_english = next_char.isascii() and next_char.isalpha()

        return prev_is_english or next_is_english

    new_line = line.strip()  # remove leading/trailing whitespace
    new_line = ''.join(c if c != ' ' or should_keep_space(new_line, i) else '' for i, c in enumerate(new_line))
    new_line = re.sub(r' +', ' ', new_line)

    return new_line


def check_line_validity(line: str, min_line_len: int = 2) -> str:
    """clean a single line"""

    line = line.strip()  # remove leading/trailing whitespace

    if len(line) <= min_line_len:  # if the line is too short, skip
        return False
    elif re.match(r'^[\d\s。，！——\.\,\=\-\%\&\^\#\@\!\*\(\)\+\_]+$', line):  # if the line only contains numbers or punctuations, skip
        return False
    elif is_catalog_line(line):  # if the line is part of a catalog or table of contents, skip
        return False
    elif any(re.search(pat, line, flags=re.IGNORECASE) for pat in REMOVE_PATTERNS):  # if the line matches any of the remove patterns, skip
        return False
    else:  # if the line is valid, keep
        return True
