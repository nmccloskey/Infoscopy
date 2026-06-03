from __future__ import annotations

import json
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def scratch_dir(parent: str | Path, *, prefix: str = "_dx_") -> Iterator[Path]:
    """Create a temporary scratch directory under parent and remove it on exit."""
    path = Path(parent) / f"{prefix}{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def long_path(path: str | Path) -> Path:
    """Return a Windows long-path-safe path when needed."""
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = resolved.resolve()
    if not (resolved.drive and not str(resolved).startswith("\\\\?\\")):
        return resolved
    return Path(f"\\\\?\\{resolved}")


def write_text(path: str | Path, text: str, *, force: bool) -> None:
    """Write UTF-8 text, refusing to overwrite unless force is true."""
    target = Path(path)
    if target.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def write_yaml(
    path: str | Path,
    data: dict[str, Any],
    *,
    force: bool,
    allow_unicode: bool = False,
) -> None:
    """Write a YAML mapping, refusing to overwrite unless force is true."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to write YAML example files.") from exc

    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=allow_unicode)
    write_text(path, text, force=force)


def write_json(path: str | Path, data: dict[str, Any], *, force: bool) -> None:
    """Write pretty JSON, refusing to overwrite unless force is true."""
    text = json.dumps(data, indent=2) + "\n"
    write_text(path, text, force=force)


def copy_tree_contents(source: str | Path, target: str | Path) -> None:
    """Copy all files under source into target, preserving relative paths."""
    source_path = Path(source)
    target_path = Path(target)
    for file_path in source_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(source_path)
        destination = target_path / relative
        long_path(destination.parent).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(long_path(file_path), long_path(destination))


def replace_tree(source: str | Path, target: str | Path, *, force: bool) -> None:
    """
    Copy source tree contents into target, refusing existing targets unless force.

    Existing target directories are updated in place when force is true.
    """
    target_path = Path(target)
    if target_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing directory: {target_path}")
    copy_tree_contents(source, target_path)
