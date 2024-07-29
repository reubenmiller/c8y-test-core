"""Util tests
"""
import unittest
from c8y_test_core.utils import to_csv


class TestCSVConversion(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_csv_single_row(self):
        output = to_csv(
            [
                ("col1", ["hello"]),
                ("col2", [True]),
                ("col3", [False]),
                ("col4", [1.234]),
            ]
        )

        expected = """
"col1","col2","col3","col4"
"hello",true,false,1.234
""".strip()
        assert output == expected

    def test_csv_multiple_rows(self):
        output = to_csv(
            [
                ("col1", ["hello", "again"]),
                ("col2", [True, False]),
                ("col3", [False, True]),
                ("col4", [1.234, 10000001]),
            ]
        )

        expected = """
"col1","col2","col3","col4"
"hello",true,false,1.234
"again",false,true,10000001
""".strip()
        assert output == expected


if __name__ == "__main__":
    unittest.main()
