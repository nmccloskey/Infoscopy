from __future__ import annotations

import json
from argparse import Namespace
from datetime import datetime
from pathlib import Path

import pytest

from psair.core.provenance import (
    capture_directory_snapshot,
    capture_environment,
    diff_config_values,
    overrides_to_mapping,
    parse_key_value_overrides,
    serialize_cli_args,
    write_cli_args,
    write_effective_config,
    write_json,
    write_manifest,
)


def test_write_json_converts_common_values(tmp_path: Path) -> None:
    out = write_json(
        tmp_path / "data.json",
        {
            "path": tmp_path / "input",
            "time": datetime(2026, 5, 13, 8, 49),
            "items": {"b", "a"},
        },
    )

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["path"] == str(tmp_path / "input")
    assert data["time"] == "2026-05-13T08:49:00"
    assert data["items"] == ["a", "b"]


def test_capture_directory_snapshot_records_files_and_folders(tmp_path: Path) -> None:
    base = tmp_path / "input"
    nested = base / "nested"
    nested.mkdir(parents=True)
    (base / "raw.csv").write_text("x\n", encoding="utf-8")
    (nested / "skip.tmp").write_text("tmp\n", encoding="utf-8")

    snapshot = capture_directory_snapshot(
        base,
        root=tmp_path,
        include_file_stats=False,
        ignore=["*.tmp"],
    )

    assert snapshot["base"] == "input"
    assert snapshot["exists"] is True
    assert str(Path("input") / "nested") in snapshot["folders"]
    assert str(Path("input") / "raw.csv") in snapshot["files"]
    assert str(Path("input") / "nested" / "skip.tmp") not in snapshot["files"]


def test_capture_directory_snapshot_can_include_file_stats(tmp_path: Path) -> None:
    base = tmp_path / "input"
    base.mkdir()
    (base / "raw.csv").write_text("x\n", encoding="utf-8")

    snapshot = capture_directory_snapshot(base, root=tmp_path)

    file_entry = snapshot["files"][0]
    assert file_entry["path"] == str(Path("input") / "raw.csv")
    assert file_entry["size_bytes"] == (base / "raw.csv").stat().st_size
    assert "modified_at" in file_entry


def test_capture_directory_snapshot_handles_missing_directory(tmp_path: Path) -> None:
    snapshot = capture_directory_snapshot(tmp_path / "missing", root=tmp_path)

    assert snapshot == {
        "base": "missing",
        "exists": False,
        "folders": [],
        "files": [],
    }


def test_cli_args_serialization_and_write(tmp_path: Path) -> None:
    args = Namespace(command=["powers", "evaluate"], config=tmp_path / "config")

    serialized = serialize_cli_args(args)
    assert serialized == {
        "command": ["powers", "evaluate"],
        "config": str(tmp_path / "config"),
    }

    out = write_cli_args(tmp_path / "cli_args.json", args)
    assert json.loads(out.read_text(encoding="utf-8")) == serialized


def test_write_effective_config_writes_yaml(tmp_path: Path) -> None:
    out = write_effective_config(
        tmp_path / "effective_config.yaml",
        {"project": {"input_dir": "input", "shuffle_samples": True}},
    )

    text = out.read_text(encoding="utf-8")
    assert "project:" in text
    assert "input_dir: input" in text
    assert "shuffle_samples: true" in text


def test_diff_config_values_flattens_nested_changes() -> None:
    before = {
        "project": {"input_dir": "input", "random_seed": 99},
        "advanced": {"auto_blind": False},
    }
    after = {
        "project": {"input_dir": "input/site1", "random_seed": 99},
        "advanced": {"auto_blind": True},
    }

    assert diff_config_values(before, after) == {
        "advanced.auto_blind": {"source": "cli", "old": False, "new": True},
        "project.input_dir": {"source": "cli", "old": "input", "new": "input/site1"},
    }


def test_capture_environment_reports_selected_package_versions() -> None:
    environment = capture_environment(["pytest", "definitely-not-installed-psair-test"])

    assert "python_version" in environment
    assert "platform" in environment
    assert environment["package_versions"]["pytest"] is not None
    assert environment["package_versions"]["definitely-not-installed-psair-test"] is None


def test_write_manifest(tmp_path: Path) -> None:
    out = write_manifest(
        tmp_path / "manifest.json",
        run_id="diaad_260513_0849",
        command=["powers evaluate"],
        status="completed",
        artifacts={"log": "logs/run_log.log"},
    )

    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["run_id"] == "diaad_260513_0849"
    assert manifest["artifacts"]["log"] == "logs/run_log.log"


def test_parse_key_value_overrides_coerces_values() -> None:
    overrides = parse_key_value_overrides(
        [
            "project.input_dir=diaad_data/input/site1",
            "random_seed=42",
            "shuffle_samples=false",
            "exclude_participants=['INV', 'PAR']",
            "stimulus_field=",
        ]
    )

    assert overrides_to_mapping(overrides) == {
        "project.input_dir": "diaad_data/input/site1",
        "random_seed": 42,
        "shuffle_samples": False,
        "exclude_participants": ["INV", "PAR"],
        "stimulus_field": "",
    }


def test_parse_key_value_overrides_rejects_bad_syntax() -> None:
    with pytest.raises(ValueError, match="KEY=VALUE"):
        parse_key_value_overrides(["input_dir"])
