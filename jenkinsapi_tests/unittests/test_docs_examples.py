from pathlib import Path


def _assert_python_files_compile(directory: str) -> None:
    for path in Path(directory).glob("*.py"):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")


def test_how_to_examples_are_valid_python():
    _assert_python_files_compile("examples/how_to")


def test_low_level_examples_are_valid_python():
    _assert_python_files_compile("examples/low_level")
