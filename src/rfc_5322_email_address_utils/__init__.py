"""RFC 5322 email address parsing utilities.

Public API:
    parse_email_address(text) -> EmailAddress | None
    EmailAddress
    InvalidEmailAddressError
"""

from .core import (
    EmailAddress,
    InvalidEmailAddressError,
    parse_email_address,
)

__all__ = [
    "EmailAddress",
    "InvalidEmailAddressError",
    "parse_email_address",
]
