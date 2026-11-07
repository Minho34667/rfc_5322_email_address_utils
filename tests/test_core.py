import unittest

from rfc_5322_email_address_utils import (
    EmailAddress,
    InvalidEmailAddressError,
    parse_email_address,
)


class ParseEmailAddressTests(unittest.TestCase):
    def test_simple_address(self):
        addr = parse_email_address("user@example.org")
        self.assertEqual(addr, EmailAddress(local="user", domain="example.org"))

    def test_domain_is_lowercased(self):
        addr = parse_email_address("user@EXAMPLE.ORG")
        self.assertEqual(addr.domain, "example.org")

    def test_local_part_case_is_preserved(self):
        addr = parse_email_address("User@example.org")
        self.assertEqual(addr.local, "User")

    def test_quoted_local_part(self):
        addr = parse_email_address('"john..doe"@example.org')
        self.assertEqual(addr.local, "john..doe")
        self.assertEqual(addr.domain, "example.org")

    def test_quoted_local_part_with_escape(self):
        addr = parse_email_address('"john\\\"doe"@example.org')
        self.assertEqual(addr.local, 'john"doe')

    def test_display_name_with_angle_brackets(self):
        addr = parse_email_address("John Doe <john@example.org>")
        self.assertEqual(addr.display_name, "John Doe")
        self.assertEqual(addr.local, "john")
        self.assertEqual(addr.domain, "example.org")

    def test_quoted_display_name(self):
        addr = parse_email_address('"Doe, John" <john@example.org>')
        self.assertEqual(addr.display_name, "Doe, John")

    def test_trailing_comment(self):
        addr = parse_email_address("john@example.org (work)")
        self.assertEqual(addr.comment, "work")
        self.assertEqual(addr.local, "john")

    def test_display_name_and_comment(self):
        addr = parse_email_address("John Doe <john@example.org> (work)")
        self.assertEqual(addr.display_name, "John Doe")
        self.assertEqual(addr.comment, "work")

    def test_str_returns_address(self):
        addr = parse_email_address("John Doe <john@example.org>")
        self.assertEqual(str(addr), "john@example.org")

    def test_invalid_missing_at(self):
        self.assertIsNone(parse_email_address("john.example.org"))

    def test_invalid_empty_local_part(self):
        self.assertIsNone(parse_email_address("@example.org"))

    def test_invalid_empty_domain(self):
        self.assertIsNone(parse_email_address("john@"))

    def test_invalid_trailing_dot(self):
        self.assertIsNone(parse_email_address("john@example.org."))

    def test_invalid_domain_label_starts_with_hyphen(self):
        self.assertIsNone(parse_email_address("john@-example.org"))

    def test_invalid_domain_label_ends_with_hyphen(self):
        self.assertIsNone(parse_email_address("john@example-.org"))

    def test_invalid_unclosed_quote(self):
        self.assertIsNone(parse_email_address('"john@example.org'))

    def test_invalid_unclosed_comment(self):
        self.assertIsNone(parse_email_address("john@example.org (work"))

    def test_invalid_display_name_without_brackets(self):
        self.assertIsNone(parse_email_address("John Doe john@example.org"))

    def test_invalid_extra_text_after_address(self):
        self.assertIsNone(parse_email_address("john@example.org extra"))

    def test_non_string_raises(self):
        with self.assertRaises(InvalidEmailAddressError):
            parse_email_address(123)

    def test_whitespace_is_stripped(self):
        addr = parse_email_address("  john@example.org  ")
        self.assertEqual(addr.local, "john")
        self.assertEqual(addr.domain, "example.org")


if __name__ == "__main__":
    unittest.main()
