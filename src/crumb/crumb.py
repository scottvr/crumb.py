#!/usr/bin/env python3
# crumb: src/crumb/crumb.py
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
        description="Recursively insert a '# crumb:' comment into files that don't already have it."
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
    parser.add_argument(
        "--all-ext",
        action="append",
        help="Additional file extensions to process (e.g., '.js', '.txt'). Can be used multiple times."
    )
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Use absolute file paths in the crumb tag instead of relative paths."
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing crumb tags with new ones instead of skipping those files."
    )
    parser.add_argument(
        "--unix",
        action="store_true",
        help="Use Unix-style (forward slash) path separators, even on Windows."
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


def find_insertion_index(lines, replace=False):
    """
    Find the best insertion index for the '# crumb:' line.
    We'll skip over:
      - Shebang (#!)
      - Coding line (# -*- coding: ...)
      - A possible top-level docstring (single/double quotes, any indentation)
      
    If replace=True, return the index of any existing crumb tag to be replaced
    """
    insertion_index = 0  # Candidate for insertion
    in_docstring = False
    docstring_delim = None

    docstring_re = re.compile(r'^\s*["\']{3}')  # Detects triple quotes with any indentation

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for existing '# crumb:'
        if "# crumb:" in stripped:
            if replace:
                return i  # Return existing index for replacement
            else:
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

def insert_path_marker(file_path, start_dir, dry_run=False, verbose=False, backup_ext=None, use_absolute=False, replace=False, use_unix=False):
    """
    Insert the line '# crumb: path' at the appropriate place
    if the file doesn't already have it in the top portion.
    Path can be relative or absolute based on the use_absolute parameter.
    Optionally creates a backup file before modifying.
    When replace=True, replace any existing crumb tag instead of skipping the file.
    When use_unix=True, use Unix-style path separators (/) even on Windows.
    Returns True if we modified the file, else False.
    """
    if use_absolute:
        path = os.path.abspath(file_path)
    else:
        path = os.path.relpath(file_path, start_dir)
        
    # Convert backslashes to forward slashes if requested
    if use_unix and os.sep == '\\':
        path = path.replace('\\', '/')

    try:
        with io.open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return False

    if not lines:
        logger.info(f"Skipping {file_path}: empty file.")
        return False

    idx = find_insertion_index(lines, replace=replace)
    if idx is None:
        logger.info(f"Skipping {file_path}: already has marker and replace=False.")
        return False

    marker_line = f"# crumb: {path}\n"
    if verbose:
        if replace and any("# crumb:" in line for line in lines):
            logger.debug(f"Replacing marker in {file_path} at line {idx} (dry_run={dry_run}).")
        else:
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

        # Replace or insert the marker line
        if replace and any("# crumb:" in line for line in lines):
            lines[idx] = marker_line  # Replace existing marker
        else:
            lines.insert(idx, marker_line)  # Insert new marker
            
        try:
            with io.open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False

    return True
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
        if args.absolute:
            logger.debug("Using absolute paths for crumb tags.")
        if args.replace:
            logger.debug("Will replace existing crumb tags.")
        if args.unix:
            logger.debug("Using Unix-style path separators.")

    # Set up the list of file extensions to process
    extensions = [".py"]  # Always include Python files
    if args.all_ext:
        for ext in args.all_ext:
            # Make sure extension starts with a dot
            if not ext.startswith("."):
                ext = "." + ext
            extensions.append(ext)
        if args.verbose:
            logger.debug(f"Processing files with extensions: {extensions}")

    updated_count = 0
    skipped_count = 0
    replaced_count = 0
    total_files = 0

    for root, dirs, files in os.walk(start_dir):
        for file in files:
            # Check if file has any of the target extensions
            if not any(file.endswith(ext) for ext in extensions):
                continue
                
            file_path = os.path.join(root, file)
            total_files += 1

            if not args.no_ignore and should_ignore(file_path, start_dir, patterns):
                if args.verbose:
                    logger.debug(f"Skipping {file_path} due to ignore pattern.")
                skipped_count += 1
                continue

            # Track if file had existing crumb tag before modification
            had_crumb = False
            try:
                with io.open(file_path, "r", encoding="utf-8") as f:
                    had_crumb = any("# crumb:" in line for line in f.readlines())
            except Exception:
                pass  # Will be handled by insert_path_marker

            modified = insert_path_marker(
                file_path=file_path,
                start_dir=start_dir,
                dry_run=args.dry_run,
                verbose=args.verbose,
                backup_ext=args.backup,
                use_absolute=args.absolute,
                replace=args.replace,
                use_unix=args.unix
            )
            
            if modified:
                if had_crumb and args.replace:
                    replaced_count += 1
                updated_count += 1
            else:
                skipped_count += 1

    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Total files considered: {total_files}")
    logger.info(f"Files updated: {updated_count}")
    if args.replace:
        logger.info(f"Files with replaced crumb tags: {replaced_count}")
    logger.info(f"Files skipped: {skipped_count}")
    if args.dry_run:
        logger.info("Dry run mode was ON (no files were actually modified).")

            
        if modified:
            if had_crumb and args.replace:
                replaced_count += 1
            updated_count += 1
        else:
                skipped_count += 1

    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Total files considered: {total_files}")
    logger.info(f"Files updated: {updated_count}")
    if args.replace:
        logger.info(f"Files with replaced crumb tags: {replaced_count}")
    logger.info(f"Files skipped: {skipped_count}")
    if args.dry_run:
        logger.info("Dry run mode was ON (no files were actually modified).")

        if modified:
            updated_count += 1
        else:
            skipped_count += 1

    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Total files considered: {total_files}")
    logger.info(f"Files updated: {updated_count}")
    logger.info(f"Files skipped: {skipped_count}")
    if args.dry_run:
        logger.info("Dry run mode was ON (no files were actually modified).")


if __name__ == "__main__":
    main()