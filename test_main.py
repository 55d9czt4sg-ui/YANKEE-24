import io
from contextlib import redirect_stdout

from main import main


def test_main_prints_hello_world():
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        main()
    assert buffer.getvalue() == "Hello, World!\n"
