import os
import tempfile
from crumb import  insert_path_marker

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
