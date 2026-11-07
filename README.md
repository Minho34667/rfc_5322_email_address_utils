# rfc_5322_email_address_utils

Parses RFC 5322-style email addresses, including display names, quoted
local parts, and trailing comments.

```python
from rfc_5322_email_address_utils import parse_email_address

addr = parse_email_address('"Doe, John" <john@example.org> (work)')
print(addr.display_name)  # Doe, John
print(addr.local)         # john
print(addr.domain)        # example.org
print(addr.comment)       # work
print(str(addr))          # john@example.org
```

## Why this exists

Most code that needs an email address reaches for a regex, and most of those
regexes silently accept nonsense or reject valid quoted local parts.  This
module implements the subset of RFC 5322 that shows up in real headers:
unquoted atoms, quoted strings, display names, and comments.

The trade-off is deliberate.  A complete RFC 5322 parser has to handle
obsolete quoting, domain literals like `[192.0.2.1]`, and nested comments.
Supporting all of that makes the parser harder to read and the failure modes
harder to predict.  Instead, this parser accepts the forms above and returns
`None` for everything else, so callers can decide what to do with bad input.

## The awkward edge

A display name that is not enclosed in angle brackets is rejected.  The
string `John Doe john@example.org` returns `None`, even though a human can
read it.  RFC 5322 requires the angle brackets, and accepting the loose form
would make it impossible to tell a display name from a local part in
ambiguous inputs.

## API

- `parse_email_address(text)` returns an `EmailAddress` or `None`.
- `EmailAddress` has `local`, `domain`, `display_name`, and `comment`.
- `InvalidEmailAddressError` is raised when `text` is not a string.
