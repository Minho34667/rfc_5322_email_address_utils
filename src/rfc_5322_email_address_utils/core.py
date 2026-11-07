"""A small parser for RFC 5322-style email addresses.

The parser accepts the common address forms described by RFC 5322:

    user@example.org
    "quoted local"@example.org
    Display Name <user@example.org>
    user@example.org (comment)
    Display Name <user@example.org> (comment)

It returns ``None`` when the input is not a syntactically valid address,
and it raises :class:`InvalidEmailAddressError` only for programmer errors
such as non-string input.  Returning ``None`` for bad text keeps the
function easy to use in loops over untrusted data.

This is intentionally not a full RFC 5322 parser.  The full grammar
includes obsolete forms, domain literals, and nested comments; supporting
all of that would make the module much larger and would not help the
common case of parsing addresses from headers.  The trade-off is that
some technically valid but rare addresses are rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

__all__ = [
    "EmailAddress",
    "InvalidEmailAddressError",
    "parse_email_address",
]


class InvalidEmailAddressError(ValueError):
    """Raised when the parser is called with an argument of the wrong type."""


@dataclass(frozen=True)
class EmailAddress:
    """A parsed email address.

    Attributes:
        local: The local part, with quotes and escapes removed.
        domain: The domain part, lowercased.
        display_name: The display name, or ``None`` if there was none.
        comment: The trailing comment, or ``None`` if there was none.
    """

    local: str
    domain: str
    display_name: Optional[str] = None
    comment: Optional[str] = None

    def __str__(self) -> str:
        """Return the address in ``local@domain`` form."""
        return f"{self.local}@{self.domain}"


# Characters that may appear unquoted in an atom.  RFC 5322 calls these
# atext.  We use a regex character class because the set is fixed and small.
_ATEXT = r"A-Za-z0-9!#$%&'*+\-/=?^_`{|}~"

# An atom is one or more atext characters.
_ATOM_RE = re.compile(rf"[{_ATEXT}]+")

# A quoted string: a double quote, zero or more characters that are either
# escaped or not a quote or backslash, then a closing double quote.
_QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

# A domain label: starts with a letter or digit, then letters, digits, or
# hyphens.  This is stricter than RFC 5322 (which allows any atom) but
# matches what DNS actually permits and what users expect.
_DOMAIN_LABEL_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")


def _unquote(value: str) -> str:
    """Remove surrounding quotes and unescape backslash escapes."""
    result = []
    i = 1  # skip opening quote
    end = len(value) - 1  # skip closing quote
    while i < end:
        ch = value[i]
        if ch == "\\" and i + 1 < end:
            i += 1
            result.append(value[i])
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def _parse_local_part(text: str) -> Optional[str]:
    """Parse a local part from the start of *text*.

    Returns the unquoted local part and the number of characters consumed,
    or ``None`` if the text does not start with a valid local part.
    """
    if not text:
        return None

    if text[0] == '"':
        match = _QUOTED_RE.match(text)
        if not match:
            return None
        return _unquote(match.group(0)), match.end()

    match = _ATOM_RE.match(text)
    if not match:
        return None
    return match.group(0), match.end()


def _parse_domain(text: str) -> Optional[str]:
    """Parse a domain from the start of *text*.

    Returns the lowercased domain and the number of characters consumed,
    or ``None`` if the text does not start with a valid domain.
    """
    if not text:
        return None

    labels = []
    pos = 0
    while pos < len(text):
        match = _DOMAIN_LABEL_RE.match(text, pos)
        if not match:
            break
        labels.append(match.group(0))
        pos = match.end()
        if pos < len(text) and text[pos] == ".":
            pos += 1
            # A trailing dot is not allowed in this parser.
            if pos >= len(text):
                return None
        else:
            break

    if not labels:
        return None
    return ".".join(labels).lower(), pos


def _skip_ws(text: str, pos: int) -> int:
    """Advance *pos* past spaces and tabs."""
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    return pos


def _parse_comment(text: str, pos: int) -> Optional[tuple[str, int]]:
    """Parse a parenthesised comment starting at *pos*.

    Comments may not contain parentheses or backslashes in this parser;
    that keeps the implementation simple and covers the comments that
    appear in real headers.  Returns the comment text and the position
    after the closing parenthesis, or ``None`` if there is no comment.
    """
    if pos >= len(text) or text[pos] != "(":
        return None
    end = text.find(")", pos + 1)
    if end == -1:
        return None
    inner = text[pos + 1 : end]
    if "(" in inner or ")" in inner or "\\" in inner:
        return None
    return inner, end + 1


def _parse_address(text: str) -> Optional[EmailAddress]:
    """Parse an address from *text*, which may include a display name."""
    if not text:
        return None

    # Try the simple form first: local@domain, optionally followed by a comment.
    local_part = _parse_local_part(text)
    if local_part is not None:
        local, local_end = local_part
        if local_end < len(text) and text[local_end] == "@":
            domain_part = _parse_domain(text[local_end + 1 :])
            if domain_part is not None:
                domain, domain_len = domain_part
                pos = local_end + 1 + domain_len
                pos = _skip_ws(text, pos)
                comment = None
                if pos < len(text):
                    comment_part = _parse_comment(text, pos)
                    if comment_part is None:
                        return None
                    comment, pos = comment_part
                    pos = _skip_ws(text, pos)
                if pos != len(text):
                    return None
                return EmailAddress(local=local, domain=domain, comment=comment)

    # Try the display-name form: name <local@domain> (comment).
    lt = text.find("<")
    if lt == -1:
        return None

    name_part = text[:lt].strip()
    if not name_part:
        return None

    # The display name may be a quoted string or a sequence of atoms.
    display_name = None
    if name_part.startswith('"'):
        match = _QUOTED_RE.fullmatch(name_part)
        if match:
            display_name = _unquote(match.group(0))
        else:
            return None
    else:
        # A display name is one or more atoms separated by whitespace.
        atoms = name_part.split()
        if not atoms:
            return None
        for atom in atoms:
            if not _ATOM_RE.fullmatch(atom):
                return None
        display_name = " ".join(atoms)

    gt = text.find(">", lt + 1)
    if gt == -1:
        return None

    inner = text[lt + 1 : gt].strip()
    addr = _parse_address(inner)
    if addr is None:
        return None

    rest = text[gt + 1 :].strip()
    comment = addr.comment
    if rest:
        comment_part = _parse_comment(rest, 0)
        if comment_part is None:
            return None
        comment, pos = comment_part
        if pos != len(rest):
            return None

    return EmailAddress(
        local=addr.local,
        domain=addr.domain,
        display_name=display_name,
        comment=comment,
    )


def parse_email_address(text: str) -> Optional[EmailAddress]:
    """Parse an email address from *text*.

    Returns an :class:`EmailAddress` on success and ``None`` on failure.

    Raises:
        InvalidEmailAddressError: If *text* is not a string.
    """
    if not isinstance(text, str):
        raise InvalidEmailAddressError(
            f"expected str, got {type(text).__name__}"
        )
    return _parse_address(text.strip())
