from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConfigSource:
    """Description of where a sectioned configuration was loaded from."""

    kind: str
    path: Path | None
    files: dict[str, Path]
    missing_sections: list[str]


@dataclass(frozen=True)
class SectionedConfig:
    """Loaded config sections plus source metadata."""

    sections: dict[str, dict[str, Any]]
    source: ConfigSource


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and require its root value to be a mapping."""
    yaml_path = Path(path).expanduser()
    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML config file not found: {yaml_path}")
    if not yaml_path.is_file():
        raise IsADirectoryError(f"YAML config path is not a file: {yaml_path}")

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read YAML config files.") from exc

    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, Mapping):
        raise TypeError(f"YAML config file must contain a mapping: {yaml_path}")
    return dict(data)


def validate_known_sections(
    data: Mapping[str, Any],
    allowed_sections: Sequence[str],
) -> None:
    """Raise when a mapping contains unknown top-level config sections."""
    allowed = set(allowed_sections)
    unknown = sorted(str(key) for key in data if str(key) not in allowed)
    if unknown:
        raise ValueError(
            "Unknown top-level config section(s): " + ", ".join(unknown)
        )


def split_config_sections(
    data: Mapping[str, Any],
    section_names: Sequence[str],
    *,
    allow_missing: bool = True,
    allow_extra: bool = False,
) -> dict[str, dict[str, Any]]:
    """Split a nested config mapping into named mapping sections."""
    if not allow_extra:
        validate_known_sections(data, section_names)

    sections: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for section_name in section_names:
        if section_name not in data:
            missing.append(section_name)
            sections[section_name] = {}
            continue

        value = data[section_name]
        if value is None:
            value = {}
        if not isinstance(value, Mapping):
            raise TypeError(
                f"Config section '{section_name}' must contain a mapping."
            )
        sections[section_name] = dict(value)

    if missing and not allow_missing:
        raise ValueError("Missing required config section(s): " + ", ".join(missing))
    return sections


def merge_defaults(
    defaults: Mapping[str, Any],
    user_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Deep-merge user config over defaults without mutating either mapping."""
    merged = deepcopy(dict(defaults))
    for key, value in user_config.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = merge_defaults(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def build_config_source_metadata(
    source: ConfigSource | Mapping[str, Any] | None = None,
    *,
    kind: str | None = None,
    path: str | Path | None = None,
    files: Mapping[str, str | Path] | None = None,
    missing_sections: Sequence[str] | None = None,
    defaults_applied: bool | None = None,
    default_path: str | Path | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build JSON-ready metadata describing config source and defaults.

    Applications can pass a ConfigSource returned by load_sectioned_config, a
    similar mapping, or explicit keyword values. Keyword arguments override the
    source values, which lets callers record post-merge missing/defaulted
    sections without mutating the loader's source object.
    """
    metadata = _config_source_to_dict(source)

    if kind is not None:
        metadata["kind"] = kind
    if path is not None or "path" not in metadata:
        metadata["path"] = _path_value(path)
    if files is not None or "files" not in metadata:
        metadata["files"] = {
            str(name): _path_value(file_path)
            for name, file_path in (files or {}).items()
        }
    if missing_sections is not None or "missing_sections" not in metadata:
        metadata["missing_sections"] = [
            str(section) for section in (missing_sections or [])
        ]
    if defaults_applied is not None:
        metadata["defaults_applied"] = bool(defaults_applied)
    if default_path is not None:
        metadata["default_path"] = _path_value(default_path)
    if extra:
        metadata.update(_json_ready_mapping(extra))

    return metadata


def load_sectioned_config(
    config_source: str | Path,
    section_names: Sequence[str],
    *,
    split_filenames: Mapping[str, str] | None = None,
    nested_filenames: Sequence[str] = ("config.yaml", "config.yml"),
    allow_missing_sections: bool = True,
    allow_extra_sections: bool = False,
) -> SectionedConfig:
    """
    Load sectioned config from a nested YAML file or split-file directory.

    Directory sources may contain either split section files, such as
    ``project.yaml`` and ``advanced.yaml``, or one nested file such as
    ``config.yaml``. If both forms are present, loading fails as ambiguous.
    """
    source_path = Path(config_source).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(f"Config source not found: {source_path}")

    if source_path.is_file():
        return _load_nested_config_file(
            source_path,
            section_names,
            allow_missing_sections=allow_missing_sections,
            allow_extra_sections=allow_extra_sections,
        )

    if not source_path.is_dir():
        raise ValueError(f"Config source is neither a file nor directory: {source_path}")

    split_names = dict(split_filenames or _default_split_filenames(section_names))
    split_paths = {
        section_name: source_path / filename
        for section_name, filename in split_names.items()
    }
    existing_split_paths = {
        section_name: path
        for section_name, path in split_paths.items()
        if path.exists()
    }
    existing_nested_paths = [
        source_path / filename
        for filename in nested_filenames
        if (source_path / filename).exists()
    ]

    if len(existing_nested_paths) > 1:
        raise ValueError(
            "Multiple nested config files found in "
            f"{source_path}: "
            + ", ".join(path.name for path in existing_nested_paths)
        )
    if existing_split_paths and existing_nested_paths:
        raise ValueError(
            "Ambiguous config directory contains both split section files and "
            f"nested config file: {source_path}"
        )
    if existing_nested_paths:
        return _load_nested_config_file(
            existing_nested_paths[0],
            section_names,
            allow_missing_sections=allow_missing_sections,
            allow_extra_sections=allow_extra_sections,
        )
    if existing_split_paths:
        sections: dict[str, dict[str, Any]] = {}
        missing: list[str] = []
        for section_name in section_names:
            path = split_paths[section_name]
            if path.exists():
                sections[section_name] = load_yaml_mapping(path)
            else:
                missing.append(section_name)
                sections[section_name] = {}

        if missing and not allow_missing_sections:
            raise ValueError(
                "Missing required config file(s): "
                + ", ".join(split_names[section] for section in missing)
            )

        return SectionedConfig(
            sections=sections,
            source=ConfigSource(
                kind="split_dir",
                path=source_path,
                files=dict(existing_split_paths),
                missing_sections=missing,
            ),
        )

    expected = list(split_names.values()) + list(nested_filenames)
    raise FileNotFoundError(
        f"No sectioned config files found in {source_path}; expected one of: "
        + ", ".join(expected)
    )


def _load_nested_config_file(
    path: Path,
    section_names: Sequence[str],
    *,
    allow_missing_sections: bool,
    allow_extra_sections: bool,
) -> SectionedConfig:
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Nested config file must be .yaml or .yml: {path}")

    data = load_yaml_mapping(path)
    sections = split_config_sections(
        data,
        section_names,
        allow_missing=allow_missing_sections,
        allow_extra=allow_extra_sections,
    )
    missing = [section for section in section_names if section not in data]
    return SectionedConfig(
        sections=sections,
        source=ConfigSource(
            kind="nested_file",
            path=path,
            files={"config": path},
            missing_sections=missing,
        ),
    )


def _default_split_filenames(section_names: Sequence[str]) -> dict[str, str]:
    return {section_name: f"{section_name}.yaml" for section_name in section_names}


def _config_source_to_dict(
    source: ConfigSource | Mapping[str, Any] | None,
) -> dict[str, Any]:
    if source is None:
        return {}
    if isinstance(source, ConfigSource):
        return {
            "kind": source.kind,
            "path": _path_value(source.path),
            "files": {
                str(name): _path_value(path)
                for name, path in source.files.items()
            },
            "missing_sections": [str(section) for section in source.missing_sections],
        }
    if isinstance(source, Mapping):
        return _json_ready_mapping(source)
    raise TypeError("source must be a ConfigSource, mapping, or None.")


def _json_ready_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready_value(value) for key, value in data.items()}


def _json_ready_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return _json_ready_mapping(value)
    if isinstance(value, tuple):
        return [_json_ready_value(item) for item in value]
    if isinstance(value, list):
        return [_json_ready_value(item) for item in value]
    return value


def _path_value(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path)
