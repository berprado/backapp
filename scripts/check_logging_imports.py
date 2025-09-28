"""Utility to ensure logging imports stay centralized.

Usage:
    python scripts/check_logging_imports.py [paths...]

When no paths are provided, the repository root is scanned.
Exits with code 1 if disallowed logging imports are found.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

# Paths where direct logging imports are allowed.
ALLOWED_IMPORT_PATHS = {
    Path('facturador/logger_config.py'),
}

DEFAULT_SCAN_ROOTS = [Path('.')]
VENV_MARKERS = ('pyvenv.cfg',)
EXCLUDED_PATHS = {
    Path('facturador/unused'),
}


class Violation(Tuple[Path, int, str]):
    path: Path
    line: int
    text: str


def _is_inside_virtualenv(path: Path) -> bool:
    """Return True if *path* is located inside a virtual environment."""
    try:
        current = path.resolve()
    except FileNotFoundError:
        current = path.absolute()

    for candidate in (current, *current.parents):
        for marker in VENV_MARKERS:
            if (candidate / marker).exists():
                return True
    return False


def _is_excluded_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except FileNotFoundError:
        resolved = path.absolute()

    for excluded in EXCLUDED_PATHS:
        full_excluded = REPO_ROOT / excluded
        try:
            resolved.relative_to(full_excluded)
            return True
        except ValueError:
            continue
    return False


def iter_python_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if _is_excluded_path(root):
            continue
        if root.is_file():
            if (
                root.suffix == '.py'
                and not _is_inside_virtualenv(root)
                and not _is_excluded_path(root)
            ):
                yield root
            continue
        if not root.exists():
            continue
        for candidate in root.rglob('*.py'):
            if _is_inside_virtualenv(candidate) or _is_excluded_path(candidate):
                continue
            yield candidate


def find_logging_imports(path: Path) -> List[Violation]:
    rel_path = path.resolve().relative_to(REPO_ROOT)
    if rel_path in ALLOWED_IMPORT_PATHS:
        return []
    try:
        source = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        source = path.read_text(encoding='latin-1')
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        msg = f'Syntax error while parsing {rel_path}: {exc}'
        return [(rel_path, exc.lineno or 0, msg)]

    violations: List[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'logging':
                    line_text = _line_at(source, node.lineno)
                    violations.append((rel_path, node.lineno, line_text))
        elif isinstance(node, ast.ImportFrom):
            if node.module == 'logging':
                line_text = _line_at(source, node.lineno)
                violations.append((rel_path, node.lineno, line_text))
    return violations


def _line_at(source: str, lineno: int) -> str:
    lines = source.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ''


def main(argv: List[str]) -> int:
    roots = [Path(arg) for arg in argv] if argv else DEFAULT_SCAN_ROOTS
    files = list(iter_python_files(roots))
    if not files:
        print('No Python files found in the specified paths.')
        return 0

    violations: List[Violation] = []
    for file_path in files:
        violations.extend(find_logging_imports(file_path))

    if violations:
        print('Found disallowed logging imports:')
        for rel_path, line, text in sorted(violations):
            print(f'  {rel_path}:{line}: {text}')
        print('\nAllowed direct imports only in:')
        for allowed in sorted(ALLOWED_IMPORT_PATHS):
            print(f'  {allowed}')
        return 1

    print('No disallowed logging imports detected.')
    return 0


if __name__ == '__main__':
    REPO_ROOT = Path(__file__).resolve().parent.parent
    sys.exit(main(sys.argv[1:]))
