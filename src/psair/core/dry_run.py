from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from psair.core.provenance import make_jsonable, write_json


DryRunFormat = str


def build_config_dry_run_payload(
    *,
    program: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    cli_args: Mapping[str, Any] | None = None,
    config_overrides: Mapping[str, Any] | None = None,
    environment: Mapping[str, Any] | None = None,
    paths: Mapping[str, Any] | None = None,
    commands: Sequence[str] | str | None = None,
    warnings: Sequence[str] | None = None,
    errors: Sequence[str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a standard resolved-config dry-run payload.

    Applications are expected to resolve and validate their own config first.
    PSAIR only provides a consistent JSON/YAML-ready envelope for printing or
    saving that resolved state.
    """
    payload: dict[str, Any] = {
        "status": "dry_run_config",
        "program": dict(program),
        "effective_config": dict(effective_config),
    }
    if commands is not None:
        payload["commands"] = commands
    if paths is not None:
        payload["paths"] = dict(paths)
    if cli_args is not None:
        payload["cli_args"] = dict(cli_args)
    if config_overrides is not None:
        payload["config_overrides"] = dict(config_overrides)
    if environment is not None:
        payload["environment"] = dict(environment)
    if warnings:
        payload["warnings"] = list(warnings)
    if errors:
        payload["errors"] = list(errors)
    if extra:
        payload.update(dict(extra))
    return make_jsonable(payload)


def render_config_dry_run(
    payload: Mapping[str, Any],
    *,
    format: DryRunFormat = "json",
) -> str:
    """Render a dry-run payload as deterministic JSON or YAML text."""
    normalized = make_jsonable(dict(payload))
    if format == "json":
        return json.dumps(normalized, indent=2) + "\n"
    if format == "yaml":
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to render dry-run YAML.") from exc
        return yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True)
    raise ValueError(f"Unsupported dry-run format: {format!r}")


def write_config_dry_run(
    path: str | Path,
    payload: Mapping[str, Any],
    *,
    format: DryRunFormat | None = None,
) -> Path:
    """Write a dry-run payload to JSON or YAML, inferring format from suffix."""
    out_path = Path(path)
    resolved_format = format or _format_from_path(out_path)
    if resolved_format == "json":
        return write_json(out_path, payload)
    text = render_config_dry_run(payload, format=resolved_format)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def print_config_dry_run(
    payload: Mapping[str, Any],
    *,
    format: DryRunFormat = "json",
    file: TextIO | None = None,
) -> None:
    """Print a rendered dry-run payload."""
    target = file if file is not None else sys.stdout
    target.write(render_config_dry_run(payload, format=format))


def _format_from_path(path: Path) -> DryRunFormat:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    raise ValueError(
        "Could not infer dry-run format from file suffix; use .json, .yaml, or .yml."
    )
