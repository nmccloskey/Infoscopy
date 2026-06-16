from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from psair.core.dry_run import (
    build_config_dry_run_payload,
    print_config_dry_run,
    render_config_dry_run,
    write_config_dry_run,
)


def _payload() -> dict:
    return build_config_dry_run_payload(
        program={"name": "DIAAD", "version": "0.3.0"},
        commands=["powers evaluate"],
        paths={
            "config_dir": Path("config"),
            "run_output_dir": Path("diaad_data/output/diaad_260513_0849"),
        },
        cli_args={"command": ["powers", "evaluate"], "dry_run_config": True},
        config_overrides={
            "project.input_dir": {
                "source": "cli",
                "old": "diaad_data/input",
                "new": "diaad_data/input/site1",
            },
        },
        effective_config={
            "project": {
                "input_dir": "diaad_data/input/site1",
                "output_dir": "diaad_data/output",
            },
        },
        environment={
            "python_version": "3.12.x",
            "platform": "test",
            "package_versions": {"diaad": "0.3.0", "psair": "0.0.3a1"},
        },
        warnings=["example warning"],
    )


def test_build_config_dry_run_payload_normalizes_common_values() -> None:
    payload = _payload()

    assert payload["status"] == "dry_run_config"
    assert payload["program"] == {"name": "DIAAD", "version": "0.3.0"}
    assert payload["commands"] == ["powers evaluate"]
    assert payload["paths"]["config_dir"] == "config"
    assert payload["effective_config"]["project"]["input_dir"] == "diaad_data/input/site1"
    assert payload["warnings"] == ["example warning"]


def test_render_config_dry_run_json_is_deterministic_json() -> None:
    text = render_config_dry_run(_payload(), format="json")

    data = json.loads(text)
    assert text.endswith("\n")
    assert data["status"] == "dry_run_config"
    assert data["config_overrides"]["project.input_dir"]["source"] == "cli"


def test_render_config_dry_run_yaml() -> None:
    text = render_config_dry_run(_payload(), format="yaml")

    assert "status: dry_run_config" in text
    assert "effective_config:" in text
    assert "project.input_dir:" in text


def test_render_config_dry_run_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="Unsupported dry-run format"):
        render_config_dry_run(_payload(), format="toml")


def test_write_config_dry_run_infers_json(tmp_path: Path) -> None:
    out = write_config_dry_run(tmp_path / "dry_run_config.json", _payload())

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["status"] == "dry_run_config"


def test_write_config_dry_run_infers_yaml(tmp_path: Path) -> None:
    out = write_config_dry_run(tmp_path / "dry_run_config.yaml", _payload())

    text = out.read_text(encoding="utf-8")
    assert "status: dry_run_config" in text


def test_write_config_dry_run_requires_known_suffix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Could not infer dry-run format"):
        write_config_dry_run(tmp_path / "dry_run_config.txt", _payload())


def test_print_config_dry_run_writes_to_file_like() -> None:
    stream = io.StringIO()

    print_config_dry_run(_payload(), file=stream)

    assert json.loads(stream.getvalue())["status"] == "dry_run_config"
