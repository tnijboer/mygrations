import unittest

from mygrations.formats.mysql.file_reader.parsers.type_plain import TypePlain
class TestTypePlain(unittest.TestCase):
    def test_simple(self):

        # parse typical insert values
        parser = TypePlain()
        returned = parser.parse("created date NOT NULL DEFAULT 'bob',")

        self.assertTrue(parser.matched)
        self.assertEqual('', returned)

        self.assertEqual('created', parser._name)
        self.assertEqual('date', parser._column_type)
        self.assertFalse(parser._null)
        self.assertEqual('bob', parser._default)
        self.assertTrue(parser.has_comma)
        self.assertEqual(0, len(parser._parsing_errors))
        self.assertEqual(0, len(parser._parsing_warnings))

    def test_optional_default(self):

        # parse typical insert values
        parser = TypePlain()
        returned = parser.parse("created date")

        self.assertTrue(parser.matched)
        self.assertEqual('', returned)

        self.assertEqual('created', parser._name)
        self.assertEqual('date', parser._column_type)
        self.assertTrue(parser._null)
        self.assertEqual(None, parser._default)
        self.assertFalse(parser.has_comma)
        self.assertEqual(0, len(parser._parsing_errors))
        self.assertEqual(0, len(parser._parsing_warnings))

    def test_strip_backticks(self):

        # parse typical insert values
        parser = TypePlain()
        returned = parser.parse("`created` date")

        self.assertTrue(parser.matched)
        self.assertEqual('', returned)
        self.assertEqual('created', parser._name)
