# Functional tests

import pytest
from crumb import find_insertion_index, should_ignore

def test_find_insertion_index():
    # No shebang, no docstring
    lines = ["print('Hello, world!')\n"]
    assert find_insertion_index(lines) == 0

    # Shebang present
    lines = ["#!/usr/bin/env python3\n", "print('Hello, world!')\n"]
    assert find_insertion_index(lines) == 1

    # Shebang + docstring
    lines = [
        "#!/usr/bin/env python3\n",
        '"""Top-level docstring."""\n',
        "print('Hello, world!')\n",
    ]
    assert find_insertion_index(lines) == 2

    # Multiline docstring
    lines = [
        '"""Top-level docstring start.\n',
        "Still in the docstring.\n",
        'End of docstring."""\n',
        "print('Hello, world!')\n",
    ]
    assert find_insertion_index(lines) == 3

def test_should_ignore():
    root_path = "/project"
    file_path = "/project/tests/test_file.py"
    patterns = {"tests/"}

    # Match directory pattern
    assert should_ignore(file_path, root_path, patterns)

    # No match
    patterns = {"docs/"}
    assert not should_ignore(file_path, root_path, patterns)
