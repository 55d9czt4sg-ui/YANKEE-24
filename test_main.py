import io
import unittest
from contextlib import redirect_stdout

from main import main


class MainTests(unittest.TestCase):
    def test_main_prints_hello_world(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        self.assertEqual(buffer.getvalue(), "Hello, World!\n")
