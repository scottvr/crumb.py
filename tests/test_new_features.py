# crumb: tests/test_new_features.py
    """Test that --unix works in an integration context"""
    # Skip test if not on Windows
    if os.name != 'nt':
        pytest.skip("Unix path option test only relevant on Windows")
    
    # Create a test file
    test_file = tmp_path / "test.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("print('Test file')\n")
    
    # Mock command line arguments for unix path style
    test_args = ["crumb.py", "--path", str(tmp_path), "--unix"]
    
    # Run main function
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify unix path style was used in marker
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the path from the crumb line
    crumb_line = content.split("\n")[0]
    path = crumb_line.replace("# crumb:", "").strip()
    
    # Should not contain backslashes
    assert '\\' not in pathimport os
import tempfile
import pytest
from pathlib import Path
from crumb import insert_path_marker, main, parse_args

def test_absolute_path_option():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(b"print('Hello, world!')\n")
        temp_file_path = temp_file.name
    
    try:
        # Test inserting with relative path (default)
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is True
        
        # Verify we get relative path in the marker
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert lines[0].startswith("# crumb:")
        assert os.path.basename(temp_file_path) in lines[0]  # Should contain filename
        assert not os.path.isabs(lines[0].replace("# crumb:", "").strip())  # Should not be absolute
        
        # Reset file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write("print('Hello, world!')\n")
            
        # Test inserting with absolute path
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False, use_absolute=True) is True
        
        # Verify we get absolute path in the marker
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert lines[0].startswith("# crumb:")
        assert os.path.isabs(lines[0].replace("# crumb:", "").strip())  # Should be absolute
        assert temp_file_path in lines[0]  # Should contain full path
    finally:
        os.remove(temp_file_path)

def test_file_extensions():
    # Create temporary files with different extensions
    temp_files = []
    extensions = [".py", ".js", ".txt", ".md"]
    
    try:
        # Create files with different extensions
        for ext in extensions:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_file.write(b"console.log('Hello world');\n" if ext == ".js" else b"print('Hello, world!')\n")
                temp_files.append(temp_file.name)
        
        # Test directory is parent of all temp files
        test_dir = os.path.dirname(temp_files[0])
        
        # Test Python only (default behavior)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            modified = insert_path_marker(file_path, test_dir, dry_run=False)
            
            # Only .py files should be modified
            if ext == ".py":
                assert modified is True
            else:
                # For non-.py files, the marker shouldn't be inserted
                assert modified is False
                
            # Reset file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("console.log('Hello world');\n" if ext == ".js" else "print('Hello, world!')\n")
                
        # Now test with specific extension (.js)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            
            # Only check .js files this time
            if ext == ".js":
                assert insert_path_marker(file_path, test_dir, dry_run=False) is True
                
                # Verify the marker was added
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                assert lines[0].startswith("# crumb:")
                assert "console.log" in lines[-1][0])
        
        # Test Python only (default behavior)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            modified = insert_path_marker(file_path, test_dir, dry_run=False)
            
            # Only .py files should be modified
            if ext == ".py":
                assert modified is True
            else:
                # For non-.py files, the marker shouldn't be inserted
                assert modified is False
                
            # Reset file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("console.log('Hello world');\n" if ext == ".js" else "print('Hello, world!')\n")
                
        # Now test with specific extension (.js)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            
            # Only check .js files this time
            if ext == ".js":
                assert insert_path_marker(file_path, test_dir, dry_run=False) is True
                
                # Verify the marker was added
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                assert lines[0].startswith("# crumb:")
                assert "console.log" in lines[-1]
    finally:
        # Clean up
        for file_path in temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)

def test_replace_option():
    """Test the --replace option for existing crumb tags"""
    # Create a temporary file with an existing crumb tag
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(b"# crumb: old/path/file.py\nprint('Hello, world!')\n")
        temp_file_path = temp_file.name
    
    try:
        # Test with replace=False (default)
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is False
        
        # Verify file was not modified
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "# crumb: old/path/file.py" in content
        
        # Test with replace=True
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False, replace=True) is True
        
        # Verify the crumb tag was replaced
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Should have replaced old path with new relative path
        assert lines[0].startswith("# crumb:")
        assert "old/path/file.py" not in lines[0]
        assert os.path.basename(temp_file_path) in lines[0]
        
        # Now test with replace=True and absolute=True
        # First restore old tag
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write("# crumb: old/path/file.py\nprint('Hello, world!')\n")
            
        assert insert_path_marker(
            temp_file_path, 
            start_dir, 
            dry_run=False, 
            replace=True,
            use_absolute=True
        ) is True
        
        # Verify absolute path was used in replacement
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert os.path.isabs(lines[0].replace("# crumb:", "").strip())
        assert temp_file_path in lines[0]
    finally:
        os.remove(temp_file_path)

def test_unix_path_option():
    """Test the --unix option for path separators"""
    # Skip test if not on Windows
    if os.name != 'nt':
        pytest.skip("Unix path option test only relevant on Windows")
        
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(b"print('Hello, world!')\n")
        temp_file_path = temp_file.name
    
    try:
        # Test with normal path separators (default)
        start_dir = os.path.dirname(temp_file_path)
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False) is True
        
        # Verify we get normal Windows path separators
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        crumb_line = content.split("\n")[0].replace("# crumb:", "").strip()
        
        # Only check for backslashes if this is Windows
        if os.sep == '\\':
            assert '\\' in crumb_line or len(crumb_line.split('\\')) == 1  # Has backslashes or is just a filename
        
        # Reset file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write("print('Hello, world!')\n")
            
        # Test with unix path separators
        assert insert_path_marker(temp_file_path, start_dir, dry_run=False, use_unix=True) is True
        
        # Verify we get unix path separators
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        crumb_line = content.split("\n")[0].replace("# crumb:", "").strip()
        
        # Even on Windows, should not have backslashes
        assert '\\' not in crumb_line
        
        # If path has separators (not just a filename), they should be forward slashes
        if len(os.path.normpath(crumb_line).split(os.sep)) > 1:
            assert '/' in crumb_line
    finally:
        os.remove(temp_file_path)

def test_command_line_arguments(monkeypatch, caplog):
    """Test that command line arguments are correctly parsed"""
    # Mock sys.argv for absolute path argument
    test_args = ["crumb.py", "--absolute", "--path", "/test/path"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.absolute is True
    assert args.path == "/test/path"
    
    # Mock sys.argv for file extensions
    test_args = ["crumb.py", "--all-ext", ".js", "--all-ext", "txt"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.all_ext == [".js", "txt"]
    assert args.absolute is False  # Default
    
    # Mock sys.argv for replace option
    test_args = ["crumb.py", "--replace"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.replace is True
    
    # Mock sys.argv for unix option
    test_args = ["crumb.py", "--unix"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.unix is True

def test_integration_replace_option(monkeypatch, tmp_path):
    """Test that --replace works in an integration context"""
    # Create a test file with an existing crumb tag
    test_file = tmp_path / "test.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# crumb: different/path/test.py\nprint('Test file')\n")
    
    # Mock command line arguments for replace
    test_args = ["crumb.py", "--path", str(tmp_path), "--replace"]
    
    # Run main function
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify crumb tag was replaced
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Should not contain old path
    assert "different/path/test.py" not in content
    
    # Should contain the new relative path
    assert "# crumb: test.py\n" in content

def test_integration_all_extensions(monkeypatch, tmp_path):
    """Test that --all-ext works in an integration context"""
    # Create various files in a temp directory
    test_files = {
        "test.py": "print('Python file')\n",
        "test.js": "console.log('JS file');\n",
        "test.txt": "Plain text file\n",
        "test.md": "# Markdown file\n"
    }
    
    # Create the test files
    for name, content in test_files.items():
        file_path = tmp_path / name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    # Mock command line arguments and run main
    test_args = ["crumb.py", "--path", str(tmp_path), "--all-ext", ".js", "--all-ext", ".md"]
    monkeypatch.setattr("sys.argv", test_args)
    
    # Run main function to process files
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify markers were added to the right files
    for name in test_files:
        file_path = tmp_path / name
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Python files (default) and specified extensions should have markers
        if name.endswith((".py", ".js", ".md")):
            assert content.startswith("# crumb:")
        else:
            # .txt files should not have markers
            assert not content.startswith("# crumb:")

def test_integration_absolute_path(monkeypatch, tmp_path):
    """Test that --absolute works in an integration context"""
    # Create a test file
    test_file = tmp_path / "test.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("print('Test file')\n")
    
    # Mock command line arguments for absolute path
    test_args = ["crumb.py", "--path", str(tmp_path), "--absolute"]
    
    # Run main function
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify absolute path was used in marker
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the path from the crumb line
    crumb_line = content.split("\n")[0]
    path = crumb_line.replace("# crumb:", "").strip()
    
    # Should be an absolute path
    assert os.path.isabs(path)
    # Should contain the full path to the test file
    assert str(test_file) == path[0])
        
        # Test Python only (default behavior)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            modified = insert_path_marker(file_path, test_dir, dry_run=False)
            
            # Only .py files should be modified
            if ext == ".py":
                assert modified is True
            else:
                # For non-.py files, the marker shouldn't be inserted
                assert modified is False
                
            # Reset file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("console.log('Hello world');\n" if ext == ".js" else "print('Hello, world!')\n")
                
        # Now test with specific extension (.js)
        for file_path in temp_files:
            ext = os.path.splitext(file_path)[1]
            
            # Only check .js files this time
            if ext == ".js":
                assert insert_path_marker(file_path, test_dir, dry_run=False) is True
                
                # Verify the marker was added
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                assert lines[0].startswith("# crumb:")
                assert "console.log" in lines[-1]
    finally:
        # Clean up
        for file_path in temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)

def test_command_line_arguments(monkeypatch, caplog):
    """Test that command line arguments are correctly parsed"""
    # Mock sys.argv for absolute path argument
    test_args = ["crumb.py", "--absolute", "--path", "/test/path"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.absolute is True
    assert args.path == "/test/path"
    
    # Mock sys.argv for file extensions
    test_args = ["crumb.py", "--all-ext", ".js", "--all-ext", "txt"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_args()
    assert args.all_ext == [".js", "txt"]
    assert args.absolute is False  # Default

def test_integration_all_extensions(monkeypatch, tmp_path):
    """Test that --all-ext works in an integration context"""
    # Create various files in a temp directory
    test_files = {
        "test.py": "print('Python file')\n",
        "test.js": "console.log('JS file');\n",
        "test.txt": "Plain text file\n",
        "test.md": "# Markdown file\n"
    }
    
    # Create the test files
    for name, content in test_files.items():
        file_path = tmp_path / name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    # Mock command line arguments and run main
    test_args = ["crumb.py", "--path", str(tmp_path), "--all-ext", ".js", "--all-ext", ".md"]
    monkeypatch.setattr("sys.argv", test_args)
    
    # Run main function to process files
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify markers were added to the right files
    for name in test_files:
        file_path = tmp_path / name
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Python files (default) and specified extensions should have markers
        if name.endswith((".py", ".js", ".md")):
            assert content.startswith("# crumb:")
        else:
            # .txt files should not have markers
            assert not content.startswith("# crumb:")

def test_integration_absolute_path(monkeypatch, tmp_path):
    """Test that --absolute works in an integration context"""
    # Create a test file
    test_file = tmp_path / "test.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("print('Test file')\n")
    
    # Mock command line arguments for absolute path
    test_args = ["crumb.py", "--path", str(tmp_path), "--absolute"]
    
    # Run main function
    with monkeypatch.context() as m:
        m.setattr("sys.argv", test_args)
        main()
    
    # Verify absolute path was used in marker
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the path from the crumb line
    crumb_line = content.split("\n")[0]
    path = crumb_line.replace("# crumb:", "").strip()
    
    # Should be an absolute path
    assert os.path.isabs(path)
    # Should contain the full path to the test file
    assert str(test_file) == path