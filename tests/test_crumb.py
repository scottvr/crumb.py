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

# Integration tests
import os
import tempfile
from crumb import insert_path_marker

def test_insert_path_marker():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(b"print('Hello, world!')\n")
        temp_file_path = temp_file.name

    try:
        # Test inserting the path marker
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is True

        # Verify the marker was added
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert lines[0].startswith("# src path:")
        assert "print('Hello, world!')" in lines[-1]
    finally:
        os.remove(temp_file_path)

## Edge cases
def test_empty_file():
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        # Test inserting the path marker on an empty file
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is False

        # Verify the file remains empty
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 0
    finally:
        os.remove(temp_file_path)

def test_non_utf8_file():
    # Create a non-UTF-8 temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(b"\xff\xfe\xfd")
        temp_file_path = temp_file.name

    try:
        # Test inserting the path marker
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is False
    finally:
        os.remove(temp_file_path)
