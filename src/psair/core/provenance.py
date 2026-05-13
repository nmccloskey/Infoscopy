from __future__ import annotations

import ast
import json
import platform
import re
import sys
from argparse import Namespace
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from fnmatch import fnmatch
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


_MISSING = object()
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?$"
)


@dataclass(frozen=True)
class ParsedOverride:
    """A parsed CLI-style configuration override."""

    key: str
    value: Any
    raw_value: str


def make_jsonable(value: Any) -> Any:
    """
    Convert common Python objects into JSON-serializable values.

    This is intentionally conservative: mappings, sequences, dataclasses, paths,
    datetimes, and primitive scalar values are preserved structurally. Unknown
    objects fall back to ``str(value)`` so provenance writers do not fail because
    a caller included a nonstandard object in CLI args or manifest metadata.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return make_jsonable(asdict(value))
    if isinstance(value, Namespace):
        return make_jsonable(vars(value))
    if isinstance(value, Mapping):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, set):
        return [make_jsonable(item) for item in sorted(value, key=str)]
    if isinstance(value, tuple):
        return [make_jsonable(item) for item in value]
    if isinstance(value, list):
        return [make_jsonable(item) for item in value]
    return str(value)


def write_json(path: str | Path, data: Any) -> Path:
    """Write JSON with consistent indentation and JSON-safe conversion."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(make_jsonable(data), f, indent=2)
        f.write("\n")
    return out_path


def _display_path(path: Path, root: Path | None) -> str:
    resolved = path.resolve()
    if root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(resolved)


def _matches_ignore(path: Path, rel_path: str, ignore: Iterable[str] | None) -> bool:
    if ignore is None:
        return False
    path_text = str(path)
    normalized_rel = rel_path.replace("\\", "/")
    for pattern in ignore:
        normalized_pattern = str(pattern).replace("\\", "/")
        if fnmatch(normalized_rel, normalized_pattern) or fnmatch(path_text, str(pattern)):
            return True
    return False


def capture_directory_snapshot(
    base: str | Path,
    *,
    root: str | Path | None = None,
    include_dirs: bool = True,
    include_file_stats: bool = True,
    ignore: Iterable[str] | None = None,
) -> dict[str, Any]:
    """
    Capture a stable, JSON-ready snapshot of a directory tree.

    Files are sorted by relative display path. Missing directories return a
    snapshot with ``exists: false`` rather than raising, which lets run metadata
    record attempted paths even when setup fails early.
    """
    base_path = Path(base).expanduser()
    root_path = Path(root).expanduser().resolve() if root is not None else None
    base_display = _display_path(base_path, root_path)

    snapshot: dict[str, Any] = {
        "base": base_display,
        "exists": base_path.exists(),
        "folders": [],
        "files": [],
    }
    if not base_path.exists():
        return snapshot
    if not base_path.is_dir():
        snapshot["files"] = [_file_entry(base_path, root_path, include_file_stats)]
        return snapshot

    folders: list[str] = []
    files: list[Any] = []
    for path in sorted(base_path.rglob("*"), key=lambda item: str(item).lower()):
        rel_path = _display_path(path, root_path)
        if _matches_ignore(path, rel_path, ignore):
            continue
        if path.is_dir():
            if include_dirs:
                folders.append(rel_path)
        else:
            files.append(_file_entry(path, root_path, include_file_stats))

    snapshot["folders"] = folders
    snapshot["files"] = files
    return snapshot


def _file_entry(path: Path, root: Path | None, include_file_stats: bool) -> Any:
    display = _display_path(path, root)
    if not include_file_stats:
        return display
    stat = path.stat()
    return {
        "path": display,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def serialize_cli_args(args: Namespace | Mapping[str, Any]) -> dict[str, Any]:
    """Return argparse or mapping CLI args as a JSON-ready dictionary."""
    if isinstance(args, Namespace):
        raw = vars(args)
    elif isinstance(args, Mapping):
        raw = dict(args)
    else:
        raise TypeError("CLI args must be an argparse.Namespace or mapping.")
    return make_jsonable(raw)


def write_cli_args(path: str | Path, args: Namespace | Mapping[str, Any]) -> Path:
    """Serialize CLI args to JSON."""
    return write_json(path, serialize_cli_args(args))


def write_effective_config(path: str | Path, config: Mapping[str, Any]) -> Path:
    """Write the normalized effective configuration as YAML."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to write effective YAML config.") from exc

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(make_jsonable(dict(config)), f, sort_keys=False, allow_unicode=True)
    return out_path


def diff_config_values(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    source: str = "cli",
) -> dict[str, dict[str, Any]]:
    """Return a flattened diff of changed configuration values."""
    changes: dict[str, dict[str, Any]] = {}
    _diff_mapping(before, after, source=source, prefix="", changes=changes)
    return changes


def _diff_mapping(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    source: str,
    prefix: str,
    changes: dict[str, dict[str, Any]],
) -> None:
    keys = sorted(set(before) | set(after), key=str)
    for key in keys:
        name = str(key)
        path = f"{prefix}.{name}" if prefix else name
        old = before.get(key, _MISSING)
        new = after.get(key, _MISSING)

        if isinstance(old, Mapping) and isinstance(new, Mapping):
            _diff_mapping(old, new, source=source, prefix=path, changes=changes)
            continue

        if old is _MISSING and new is _MISSING:
            continue
        if old == new:
            continue

        changes[path] = {
            "source": source,
            "old": None if old is _MISSING else make_jsonable(old),
            "new": None if new is _MISSING else make_jsonable(new),
        }


def capture_environment(package_names: Iterable[str]) -> dict[str, Any]:
    """Capture Python/platform details and selected installed package versions."""
    package_versions: dict[str, str | None] = {}
    for package_name in package_names:
        try:
            package_versions[package_name] = version(package_name)
        except PackageNotFoundError:
            package_versions[package_name] = None

    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "package_versions": package_versions,
    }


def write_manifest(
    path: str | Path,
    *,
    run_id: str,
    command: str | list[str],
    status: str,
    artifacts: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> Path:
    """Write a compact run artifact manifest."""
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "command": command,
        "status": status,
        "artifacts": dict(artifacts),
    }
    if extra:
        manifest.update(dict(extra))
    return write_json(path, manifest)


def parse_key_value_overrides(
    items: Iterable[str] | None,
    *,
    coerce: bool = True,
    key_validator: Callable[[str], bool] | None = None,
) -> list[ParsedOverride]:
    """
    Parse CLI-style ``KEY=VALUE`` overrides without applying policy.

    PSAIR handles syntax and scalar/list/dict coercion. Applications remain
    responsible for deciding which keys are allowed and how they map into their
    configuration model.
    """
    parsed: list[ParsedOverride] = []
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Override must use KEY=VALUE syntax: {item!r}")
        raw_key, raw_value = item.split("=", 1)
        key = raw_key.strip()
        if not key:
            raise ValueError(f"Override key cannot be empty: {item!r}")
        if key_validator is not None and not key_validator(key):
            raise ValueError(f"Override key is not allowed: {key}")
        value_text = raw_value.strip()
        value = _coerce_override_value(value_text) if coerce else value_text
        parsed.append(ParsedOverride(key=key, value=value, raw_value=raw_value))
    return parsed


def overrides_to_mapping(overrides: Iterable[ParsedOverride]) -> dict[str, Any]:
    """Convert parsed overrides into a key/value mapping."""
    return {override.key: make_jsonable(override.value) for override in overrides}


def _coerce_override_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"none", "null"}:
        return None
    if value == "":
        return ""
    if _INT_RE.match(value):
        return int(value)
    if _FLOAT_RE.match(value):
        return float(value)

    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value

    if isinstance(parsed, tuple):
        return list(parsed)
    if isinstance(parsed, (str, int, float, bool, list, dict)) or parsed is None:
        return parsed
    return value
