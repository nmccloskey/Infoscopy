from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from collections.abc import Callable

from psair.core.provenance import capture_directory_snapshot, make_jsonable, write_json

# ---------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------
logger = logging.getLogger("RunLogger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Early-log buffer and root directory
_early_logs: list[tuple[str, str]] = []
_root_dir: Path | None = None
_finalization_hooks: list[Callable[[dict], None]] = []


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def set_root(path: Path):
    """Set the global project root directory (usually repo root)."""
    global _root_dir
    _root_dir = path.resolve()


def get_root() -> Path:
    """Return the current project root directory."""
    if _root_dir is None:
        return Path.cwd().resolve()
    return _root_dir


def get_rel_path(path: Path) -> str:
    """Safely return path relative to project root (absolute fallback)."""
    root = get_root()
    try:
        return str(path.resolve().relative_to(root))
    except Exception:
        return str(path.resolve())


def early_log(level: str, message: str):
    """Queue a log message before the file logger is initialized."""
    _early_logs.append((level, message))
    print(f"[{level.upper()}] {message}")  # still visible on console


def flush_early_logs():
    """Replay buffered early logs into the main logger."""
    for level, msg in _early_logs:
        getattr(logger, level.lower(), logger.info)(msg)
    _early_logs.clear()


def add_finalization_hook(hook: Callable[[dict], None]) -> None:
    """Register a callable to run during logger termination."""
    _finalization_hooks.append(hook)


def clear_finalization_hooks() -> None:
    """Clear registered finalization hooks."""
    _finalization_hooks.clear()


def configure_file_handler(
    output_label: str = "",
    log_dir: Path | str | None = None,
) -> Path:
    """
    Attach a basic file handler for legacy callers that do not use initialize_logger.

    OutputManager historically called this during configuration loading, before it
    had a run-specific output directory available. Newer code should prefer
    initialize_logger when it can provide explicit run paths.
    """
    root = get_root()
    target_dir = Path(log_dir).resolve() if log_dir is not None else root / "logs"
    target_dir.mkdir(parents=True, exist_ok=True)

    log_path = (target_dir / "run_log.log").resolve()

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path:
            return log_path

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.info(f"Log file created: {get_rel_path(log_path)}")
    flush_early_logs()
    return log_path


# ---------------------------------------------------------------------
# Initialization and termination
# ---------------------------------------------------------------------
def initialize_logger(
    start_time: datetime,
    out_dir: Path,
    program_name: str,
    version: str | None = None,
) -> Path:
    """
    Initialize file-based logging for a program run.
    """
    global _root_dir
    if _root_dir is None:
        _root_dir = Path.cwd().resolve()

    log_dir = out_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = (log_dir / "run_log.log").resolve()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    version_str = f" (version {version})" if version else ""
    logger.info(
        f"=== {program_name}{version_str} run initialized at {start_time.isoformat()} ==="
    )
    logger.info(
        f"{program_name} root directory set to: {get_root()} "
        "(all paths relative to this root)"
    )
    logger.info(f"Log file created: {get_rel_path(log_path)}")

    flush_early_logs()
    return log_path


def record_run_metadata(
    input_dir: Path,
    output_dir: Path,
    config_path: Path,
    config: dict,
    start_time: datetime,
    end_time: datetime,
    program_name: str,
    version: str | None = None,
) -> Path:
    """Record structured metadata including configuration and directory snapshots."""
    runtime_seconds = round((end_time - start_time).total_seconds(), 2)

    metadata = {
        "program": {
            "name": program_name,
            "version": version,
        },
        "header": f"{program_name} run {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        "timestamp": end_time.isoformat(timespec="seconds"),
        "runtime_seconds": runtime_seconds,
        "root_directory": str(_root_dir),
        "paths": {
            "input_dir": get_rel_path(input_dir),
            "output_dir": get_rel_path(output_dir),
            "config_file": get_rel_path(config_path),
        },
        "configuration": make_jsonable(config),
        "directory_snapshot": {
            "input_contents": capture_directory_snapshot(
                input_dir,
                root=get_root(),
                include_file_stats=False,
            ),
            "output_contents": capture_directory_snapshot(
                output_dir,
                root=get_root(),
                include_file_stats=False,
            ),
        },
    }

    meta_path = (output_dir / "logs" / "run_metadata.json").resolve()
    write_json(meta_path, metadata)

    logger.info(f"Run metadata saved at {get_rel_path(meta_path)}")
    return meta_path


def terminate_logger(
    input_dir: Path,
    output_dir: Path,
    config_path: Path,
    config: dict,
    start_time: datetime,
    program_name: str,
    version: str | None = None,
    status: str = "completed",
):
    """Finalize logging: record metadata and close file handlers."""
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    logger.info(
        f"=== {program_name} run completed at {end_time.isoformat()} ==="
    )
    logger.info(f"Total runtime: {elapsed:.2f} seconds")

    context = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "config_path": config_path,
        "config": config,
        "start_time": start_time,
        "end_time": end_time,
        "program_name": program_name,
        "version": version,
        "status": status,
    }

    try:
        record_run_metadata(
            input_dir=input_dir,
            output_dir=output_dir,
            config_path=config_path,
            config=config,
            start_time=start_time,
            end_time=end_time,
            program_name=program_name,
            version=version,
        )

        for hook in list(_finalization_hooks):
            hook(context)
    finally:
        clear_finalization_hooks()
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.removeHandler(handler)
