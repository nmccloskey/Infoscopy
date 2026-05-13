from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
import json

import pytest

from psair.core import logger as run_logger


@pytest.fixture(autouse=True)
def reset_logger_state() -> None:
    run_logger._early_logs.clear()
    run_logger._root_dir = None
    run_logger.clear_finalization_hooks()
    for handler in run_logger.logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            run_logger.logger.removeHandler(handler)

    yield

    run_logger._early_logs.clear()
    run_logger._root_dir = None
    run_logger.clear_finalization_hooks()
    for handler in run_logger.logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            run_logger.logger.removeHandler(handler)


def test_root_helpers_return_relative_paths_inside_root(tmp_path: Path) -> None:
    run_logger.set_root(tmp_path)
    nested = tmp_path / "data" / "input.csv"
    nested.parent.mkdir()
    nested.write_text("value\n", encoding="utf-8")

    assert run_logger.get_root() == tmp_path.resolve()
    assert run_logger.get_rel_path(nested) == str(Path("data") / "input.csv")
    assert run_logger.get_rel_path(tmp_path.parent / "outside.txt") == str(
        (tmp_path.parent / "outside.txt").resolve()
    )


def test_early_log_prints_and_flushes_to_logger(
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    run_logger.early_log("warning", "queued before initialization")

    assert "[WARNING] queued before initialization" in capsys.readouterr().out
    assert run_logger._early_logs == [("warning", "queued before initialization")]

    with caplog.at_level(logging.INFO, logger="RunLogger"):
        run_logger.flush_early_logs()

    assert "queued before initialization" in caplog.text
    assert run_logger._early_logs == []


def test_initialize_logger_creates_log_file_and_flushes_early_logs(tmp_path: Path) -> None:
    start = datetime(2026, 4, 20, 14, 30)
    run_logger.set_root(tmp_path)
    run_logger.early_log("info", "startup note")

    log_path = run_logger.initialize_logger(
        start_time=start,
        out_dir=tmp_path / "output",
        program_name="DemoRun",
        version="1.2.3",
    )

    assert log_path == (tmp_path / "output" / "logs" / "run_log.log")
    assert log_path.exists()

    text = log_path.read_text(encoding="utf-8")
    assert "=== DemoRun (version 1.2.3) run initialized" in text
    assert "startup note" in text
    assert run_logger._early_logs == []
    assert any(isinstance(handler, logging.FileHandler) for handler in run_logger.logger.handlers)


def test_configure_file_handler_supports_legacy_output_manager_calls(tmp_path: Path) -> None:
    run_logger.set_root(tmp_path)
    run_logger.early_log("info", "legacy startup")

    log_path = run_logger.configure_file_handler("Demo Run")

    assert log_path.parent == tmp_path / "logs"
    assert log_path.name == "run_log.log"
    assert log_path.exists()
    assert "legacy startup" in log_path.read_text(encoding="utf-8")
    assert run_logger._early_logs == []


def test_record_run_metadata_writes_structured_snapshot(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    config_path = tmp_path / "config.yaml"
    input_dir.mkdir()
    (input_dir / "raw.csv").write_text("x\n", encoding="utf-8")
    (output_dir / "logs").mkdir(parents=True)
    (output_dir / "result.txt").write_text("done\n", encoding="utf-8")
    config_path.write_text("answer: 42\n", encoding="utf-8")
    run_logger.set_root(tmp_path)

    meta_path = run_logger.record_run_metadata(
        input_dir=input_dir,
        output_dir=output_dir,
        config_path=config_path,
        config={"answer": 42},
        start_time=datetime(2026, 4, 20, 10, 0, 0),
        end_time=datetime(2026, 4, 20, 10, 0, 2, 340000),
        program_name="Demo",
        version="0.0.1",
    )

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["program"] == {"name": "Demo", "version": "0.0.1"}
    assert metadata["runtime_seconds"] == 2.34
    assert metadata["paths"]["input_dir"] == "input"
    assert metadata["paths"]["output_dir"] == "output"
    assert metadata["configuration"] == {"answer": 42}
    assert str(Path("input") / "raw.csv") in metadata["directory_snapshot"]["input_contents"]["files"]
    assert str(Path("output") / "result.txt") in metadata["directory_snapshot"]["output_contents"]["files"]


def test_terminate_logger_records_metadata_and_removes_file_handlers(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    config_path = tmp_path / "config.yaml"
    input_dir.mkdir()
    output_dir.mkdir()
    config_path.write_text("ok: true\n", encoding="utf-8")
    start = datetime.now() - timedelta(seconds=1)

    run_logger.initialize_logger(start, output_dir, "Demo")
    assert any(isinstance(handler, logging.FileHandler) for handler in run_logger.logger.handlers)

    run_logger.terminate_logger(
        input_dir=input_dir,
        output_dir=output_dir,
        config_path=config_path,
        config={"ok": True},
        start_time=start,
        program_name="Demo",
        version="0.0.1",
    )

    assert (output_dir / "logs" / "run_metadata.json").exists()
    assert not any(isinstance(handler, logging.FileHandler) for handler in run_logger.logger.handlers)


def test_terminate_logger_runs_finalization_hooks(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    config_path = tmp_path / "config.yaml"
    input_dir.mkdir()
    output_dir.mkdir()
    config_path.write_text("ok: true\n", encoding="utf-8")
    start = datetime.now() - timedelta(seconds=1)
    calls = []

    run_logger.initialize_logger(start, output_dir, "Demo")
    run_logger.add_finalization_hook(lambda context: calls.append(context))

    run_logger.terminate_logger(
        input_dir=input_dir,
        output_dir=output_dir,
        config_path=config_path,
        config={"ok": True},
        start_time=start,
        program_name="Demo",
        version="0.0.1",
        status="failed",
    )

    assert len(calls) == 1
    assert calls[0]["status"] == "failed"
    assert calls[0]["output_dir"] == output_dir
