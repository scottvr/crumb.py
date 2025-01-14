#!/usr/bin/env python3

import os
import re
import argparse
import io
import logging
import shutil
from pathlib import Path

try:
    from pathspec import PathSpec
except ImportError:
    PathSpec = None  # Optional dependency for robust .gitignore parsing

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)



def parse_args():
    parser = argparse.ArgumentParser(
        description="Recursively insert a '# crumb:' comment into .py files that don't already have it."
    )
    parser.add_argument(
        "-p", "--path",
        default=os.getcwd(),
        help="Starting directory (defaults to current working directory)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, do not modify any files; just report what would be done."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--backup",
        metavar="EXT",
        help="Backup files with the given extension before modifying (e.g., '.bak' or '.orig')."
    )

    ignore_group = parser.add_mutually_exclusive_group()
    ignore_group.add_argument(
        "--ignore",
        help="Optional path to a file whose patterns should be ignored in addition to .gitignore."
    )
    ignore_group.add_argument(
        "--no-ignore",
        action="store_true",
        help="Ignore .gitignore (and any other ignore file) completely."
    )

    return parser.parse_args()

def load_ignore_patterns(root_path, extra_ignore_file=None, skip_gitignore=False):
    """
    Parse .gitignore and optionally an additional ignore file
    to build a list of ignore patterns. Uses pathspec if available.
    """
    patterns = []

    if not skip_gitignore:
        gitignore_path = os.path.join(root_path, ".gitignore")
        if os.path.isfile(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                patterns.extend(f.readlines())

    if extra_ignore_file and os.path.isfile(extra_ignore_file):
        with open(extra_ignore_file, "r", encoding="utf-8") as f:
            patterns.extend(f.readlines())

    if PathSpec:
        return PathSpec.from_lines("gitwildmatch", patterns)
    else:
        logger.warning("PathSpec not installed; .gitignore handling may be limited.")
        return set(pattern.strip() for pattern in patterns if pattern.strip())


def should_ignore(file_path, root_path, spec):
    """
    Check if file_path should be ignored based on patterns (pathspec or simple patterns).
    """
    rel_path = os.path.relpath(file_path, root_path)
    if PathSpec and isinstance(spec, PathSpec):
        return spec.match_file(rel_path)
    else:
        for pattern in spec:
            if pattern.endswith("/") and rel_path.startswith(pattern[:-1]):
                return True
            elif pattern in rel_path:
                return True
        return False


def find_insertion_index(lines):
    """
    Find the best insertion index for the '# crumb:' line.
    We'll skip over:
      - Shebang (#!)
      - Coding line (# -*- coding: ...)
      - A possible top-level docstring (single/double quotes, any indentation)
    """
    insertion_index = 0  # Candidate for insertion
    in_docstring = False
    docstring_delim = None

    docstring_re = re.compile(r'^\s*["\']{3}')  # Detects triple quotes with any indentation

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for existing '# crumb:'
        if "# crumb:" in stripped:
            return None  # Skip; already present

        # Check for shebang
        if i == 0 and stripped.startswith("#!"):
            insertion_index = i + 1
            continue

        # Check for coding line
        if i <= 1 and stripped.startswith("# -*- coding:"):
            insertion_index = i + 1
            continue

        # Detect start/end of docstring
        if not in_docstring:
            if docstring_re.match(stripped):
                in_docstring = True
                docstring_delim = stripped[:3]  # """ or '''
                if stripped.endswith(docstring_delim) and len(stripped) > 3:
                    in_docstring = False  # Single-line docstring
                insertion_index = i + 1
            else:
                # Found non-docstring content or empty line
                insertion_index = i
                break
        else:
            # Inside a docstring
            if stripped.endswith(docstring_delim):
                in_docstring = False
                insertion_index = i + 1

    return insertion_index

def insert_path_marker(file_path, start_dir, dry_run=False, verbose=False, backup_ext=None):
    """
    Insert the line '# crumb: relative_path' at the appropriate place
    if the file doesn't already have it in the top portion.
    Optionally creates a backup file before modifying.
    Returns True if we modified the file, else False.
    """
    rel_path = os.path.relpath(file_path, start_dir)

    try:
        with io.open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return False

    if not lines:
        logger.info(f"Skipping {file_path}: empty file.")
        return False

    idx = find_insertion_index(lines)
    if idx is None:
        logger.info(f"Skipping {file_path}: already has marker or no insertion point.")
        return False

    marker_line = f"# crumb: {rel_path}\n"
    if verbose:
        logger.debug(f"Inserting marker into {file_path} at line {idx} (dry_run={dry_run}).")

    if not dry_run:
        if backup_ext:
            backup_path = file_path + backup_ext
            try:
                shutil.copy(file_path, backup_path)
                if verbose:
                    logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.error(f"Failed to create backup for {file_path}: {e}")
                return False

        lines.insert(idx, marker_line)
        try:
            with io.open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False

    return True


def main():
    args = parse_args()
    start_dir = os.path.abspath(args.path)

    # Gather ignore patterns
    patterns = set()
    if not args.no_ignore:
        patterns = load_ignore_patterns(start_dir, extra_ignore_file=args.ignore, skip_gitignore=False)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    updated_count = 0
    skipped_count = 0
    total_files = 0

    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            total_files += 1

            if not args.no_ignore and should_ignore(file_path, start_dir, patterns):
                if args.verbose:
                    logger.debug(f"Skipping {file_path} due to ignore pattern.")
                skipped_count += 1
                continue

            modified = insert_path_marker(
                file_path=file_path,
                start_dir=start_dir,
                dry_run=args.dry_run,
                verbose=args.verbose,
                backup_ext=args.backup
            )
            if modified:
                updated_count += 1
            else:
                skipped_count += 1

    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Total .py files considered: {total_files}")
    logger.info(f"Files updated: {updated_count}")
    logger.info(f"Files skipped: {skipped_count}")
    if args.dry_run:
        logger.info("Dry run mode was ON (no files were actually modified).")


if __name__ == "__main__":
    main()
