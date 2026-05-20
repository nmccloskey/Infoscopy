from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from psair.core.config_files import (
    load_sectioned_config,
    load_yaml_mapping,
    merge_defaults,
    split_config_sections,
    validate_known_sections,
)


def _write_yaml(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def test_load_yaml_mapping_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_yaml(path, {"project": {"input_dir": "input"}})

    assert load_yaml_mapping(path) == {"project": {"input_dir": "input"}}


def test_load_yaml_mapping_rejects_non_mapping_root(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_yaml(path, ["not", "a", "mapping"])

    with pytest.raises(TypeError, match="must contain a mapping"):
        load_yaml_mapping(path)


def test_validate_known_sections_rejects_unknown_top_level_section() -> None:
    with pytest.raises(ValueError, match="unknown"):
        validate_known_sections(
            {"project": {}, "unknown": {}},
            ["project", "advanced"],
        )


def test_split_config_sections_returns_empty_missing_sections() -> None:
    sections = split_config_sections(
        {"project": {"input_dir": "input"}},
        ["project", "advanced"],
    )

    assert sections == {
        "project": {"input_dir": "input"},
        "advanced": {},
    }


def test_split_config_sections_can_require_all_sections() -> None:
    with pytest.raises(ValueError, match="Missing required config section"):
        split_config_sections(
            {"project": {}},
            ["project", "advanced"],
            allow_missing=False,
        )


def test_split_config_sections_rejects_non_mapping_section() -> None:
    with pytest.raises(TypeError, match="must contain a mapping"):
        split_config_sections(
            {"project": [], "advanced": {}},
            ["project", "advanced"],
        )


def test_merge_defaults_deep_merges_without_mutating_inputs() -> None:
    defaults = {
        "project": {"input_dir": "input", "random_seed": 99},
        "advanced": {"blind_cols": ["sample_id"], "auto_blind": False},
    }
    user_config = {
        "project": {"input_dir": "site/input"},
        "advanced": {"blind_cols": ["sample_id", "speaker"]},
    }

    merged = merge_defaults(defaults, user_config)

    assert merged == {
        "project": {"input_dir": "site/input", "random_seed": 99},
        "advanced": {"blind_cols": ["sample_id", "speaker"], "auto_blind": False},
    }
    assert defaults["project"]["input_dir"] == "input"


def test_load_sectioned_config_from_nested_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "effective_config.yaml"
    _write_yaml(
        path,
        {
            "project": {"input_dir": "input"},
            "advanced": {"auto_blind": False},
        },
    )

    loaded = load_sectioned_config(path, ["project", "advanced"])

    assert loaded.sections["project"] == {"input_dir": "input"}
    assert loaded.sections["advanced"] == {"auto_blind": False}
    assert loaded.source.kind == "nested_file"
    assert loaded.source.path == path
    assert loaded.source.files == {"config": path}
    assert loaded.source.missing_sections == []


def test_load_sectioned_config_from_split_directory(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(config_dir / "project.yaml", {"input_dir": "input"})
    _write_yaml(config_dir / "advanced.yaml", {"auto_blind": True})

    loaded = load_sectioned_config(config_dir, ["project", "advanced"])

    assert loaded.sections == {
        "project": {"input_dir": "input"},
        "advanced": {"auto_blind": True},
    }
    assert loaded.source.kind == "split_dir"
    assert loaded.source.path == config_dir
    assert loaded.source.files == {
        "project": config_dir / "project.yaml",
        "advanced": config_dir / "advanced.yaml",
    }
    assert loaded.source.missing_sections == []


def test_load_sectioned_config_from_directory_config_yaml(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(
        config_dir / "config.yaml",
        {"project": {"input_dir": "input"}, "advanced": {}},
    )

    loaded = load_sectioned_config(config_dir, ["project", "advanced"])

    assert loaded.sections["project"] == {"input_dir": "input"}
    assert loaded.source.kind == "nested_file"
    assert loaded.source.path == config_dir / "config.yaml"


def test_load_sectioned_config_rejects_ambiguous_directory(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(config_dir / "project.yaml", {"input_dir": "input"})
    _write_yaml(config_dir / "config.yaml", {"project": {"input_dir": "other"}})

    with pytest.raises(ValueError, match="Ambiguous config directory"):
        load_sectioned_config(config_dir, ["project", "advanced"])


def test_load_sectioned_config_tracks_missing_split_sections(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(config_dir / "project.yaml", {"input_dir": "input"})

    loaded = load_sectioned_config(config_dir, ["project", "advanced"])

    assert loaded.sections == {
        "project": {"input_dir": "input"},
        "advanced": {},
    }
    assert loaded.source.missing_sections == ["advanced"]


def test_load_sectioned_config_can_require_split_sections(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(config_dir / "project.yaml", {"input_dir": "input"})

    with pytest.raises(ValueError, match="Missing required config file"):
        load_sectioned_config(
            config_dir,
            ["project", "advanced"],
            allow_missing_sections=False,
        )


def test_load_sectioned_config_rejects_unknown_nested_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_yaml(path, {"project": {}, "advanced": {}, "other": {}})

    with pytest.raises(ValueError, match="Unknown top-level config section"):
        load_sectioned_config(path, ["project", "advanced"])


def test_load_sectioned_config_accepts_custom_split_filenames(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_yaml(config_dir / "main.yaml", {"input_dir": "input"})
    _write_yaml(config_dir / "extras.yaml", {"auto_blind": False})

    loaded = load_sectioned_config(
        config_dir,
        ["project", "advanced"],
        split_filenames={"project": "main.yaml", "advanced": "extras.yaml"},
    )

    assert loaded.sections == {
        "project": {"input_dir": "input"},
        "advanced": {"auto_blind": False},
    }


def test_load_sectioned_config_rejects_empty_directory(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="No sectioned config files"):
        load_sectioned_config(config_dir, ["project", "advanced"])
