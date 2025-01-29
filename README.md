# crumb

`crumb` is a Python utility for recursively tagging `.py` files with a comment near the top, marking their relative path at the time of tagging. This is particularly useful when files that belong in structured directories (e.g., `sub/dir/path/name.py`) end up in a flat, non-hierarchical space, enabling you to trace their original locations—*as long as you tag them beforehand*.

## Features

- **Automatic Path Tagging**: Inserts a `# crumb: relative_path` comment in `.py` files, ensuring traceability.
- **Configurable Behavior**: Control logging verbosity, dry-run mode, backup creation, and ignore patterns.
- **Backup Support**: Optionally creates backups with user-specified extensions before modifying files.
- **.gitignore Handling**: Supports `.gitignore` parsing for excluding files, with the ability to override or supplement ignore patterns.
- **Safe Insertion Logic**: Intelligently determines the best place to insert the tag, avoiding existing shebangs, encoding headers, and docstrings.

## Installation

`crumb` is a standalone script. Simply download or clone the repository:

```bash
git clone https://github.com/scottvr/crumb.py
cd crumb.py/src/crumb
python crumb.py
```

Ensure Python 3 is installed on your system (`crumb` requires Python 3.6+).

### Optional Dependencies

To improve `.gitignore` parsing, install `pathspec`:

```bash
pip install pathspec
```

`crumb` will function without `pathspec`, but its ignore logic may be less robust.

## Usage

Run `crumb` from the command line to tag `.py` files recursively from the specified directory (default: current working directory).

### Basic Command

```bash
./crumb.py
```

Tags all `.py` files in the current directory and subdirectories.

### Command-Line Arguments

```bash
usage: crumb.py [-h] [-p PATH] [--dry-run] [-v] [--backup EXT] [--ignore IGNORE | --no-ignore]

Recursively insert a '# crumb:' comment into .py files that don't already have it.

options:
  -h, --help            Show this help message and exit.
  -p PATH, --path PATH  Starting directory (defaults to current working directory).
  --dry-run             If set, do not modify any files; just report what would be done.
  -v, --verbose         Enable verbose logging.
  --backup EXT          Backup files with the given extension before modifying (e.g., '.bak' or '.orig').

ignore options:
  --ignore IGNORE       Optional path to a file whose patterns should be ignored in addition to .gitignore.
  --no-ignore           Ignore .gitignore (and any other ignore file) completely.
```

### Examples

#### Tag Files in a Specific Directory
```bash
./crumb.py -p /path/to/codebase
```

#### Dry-Run Mode
```bash
./crumb.py --dry-run
```
Reports changes without modifying any files.

#### Create Backups Before Modifying
```bash
./crumb.py --backup .bak
```
Creates backup files with `.bak` extension before applying changes.

#### Supplement `.gitignore` with Additional Ignore Patterns
```bash
./crumb.py --ignore custom-ignore-file.txt
```
Adds ignore patterns from `custom-ignore-file.txt` to those in `.gitignore`.

#### Disable Ignore Logic Entirely
```bash
./crumb.py --no-ignore
```
Processes all `.py` files, regardless of `.gitignore` or other patterns.

### Verbose Mode
```bash
./crumb.py --verbose
```
Provides detailed logging of each file processed, skipped, or ignored.

## Output

A typical tagged file will look like this:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# crumb: sub/dir/path/name.py

import os

# Your code here...
```

## Known Limitations

- **`.gitignore` Without `pathspec`**: Without `pathspec`, `.gitignore` parsing uses basic matching and may not support all `.gitignore` features.
- **File Encoding**: Files with unusual encodings may fail to process; ensure they are UTF-8 or compatible.
- **Insertion Logic**: If the script cannot find an appropriate insertion point, the file is skipped.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

### Development Setup

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

Add test cases for new functionality under the `tests` directory (if applicable). Use `pytest` for testing:

```bash
pytest
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
