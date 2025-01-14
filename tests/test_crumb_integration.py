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
        assert lines[0].startswith("# crumb:")
        assert "print('Hello, world!')" in lines[-1]
    finally:
        os.remove(temp_file_path)
