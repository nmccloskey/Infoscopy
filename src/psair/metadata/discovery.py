from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal

from psair.core.logger import logger, get_rel_path


MatchMode = Literal["exact", "contains"]


class FileDiscoveryError(Exception):
    """Base exception for file discovery problems."""


class MultipleFilesFoundError(FileDiscoveryError):
    """Raised when exactly one file is required but multiple matches are found."""


def _coerce_directories(
    directories: Path | str | Iterable[Path | str] | None,
) -> list[Path]:
    """Normalize directory input to a list of Paths."""
    if directories is None:
        return [Path.cwd()]

    if isinstance(directories, (str, Path)):
        return [Path(directories)]

    return [Path(d) for d in directories]


def _normalize_ext(search_ext: str | None) -> str:
    """Normalize an extension string to include a leading dot."""
    if not search_ext:
        return ""

    return search_ext if search_ext.startswith(".") else f".{search_ext}"


def _is_excel_temp_file(path: Path) -> bool:
    """Return True for temporary Excel lock files."""
    return path.name.startswith("~$")


def _deduplicate_by_filename(paths: list[Path]) -> list[Path]:
    """
    Deduplicate matches by filename, preserving the first path encountered.

    This supports workflows that search both input and output directories, where
    the same filename may exist in more than one searched location.
    """
    seen: dict[str, Path] = {}
    duplicates: dict[str, list[Path]] = {}

    for path in paths:
        if path.name in seen:
            duplicates.setdefault(path.name, []).append(path)
        else:
            seen[path.name] = path

    if duplicates:
        logger.warning(
            "Removed duplicate filename(s) found across searched directories."
        )
        for filename, duplicate_paths in duplicates.items():
            logger.warning(f"Duplicate filename '{filename}' found in:")
            for path in [seen[filename], *duplicate_paths]:
                logger.warning(f"  - {get_rel_path(path)}")

    return list(seen.values())


def find_matching_files(
    *,
    directories: Path | str | Iterable[Path | str] | None = None,
    filename: str | Path | None = None,
    search_base: str = "",
    search_ext: str = ".xlsx",
    match_mode: MatchMode = "contains",
    match_metadata_fields: Iterable[str] | None = None,
    deduplicate: bool = True,
    ignore_excel_temp_files: bool = True,
) -> list[Path]:
    """
    Recursively find files matching either an exact filename or a substring pattern.

    Parameters
    ----------
    directories
        One or more directories to search recursively. Defaults to current
        working directory.
    filename
        Exact filename to match when ``match_mode="exact"``.
        May include a path; only the final filename component is used for matching.
    search_base
        Substring to match when ``match_mode="contains"``.
    search_ext
        File extension to match in contains mode. Defaults to ".xlsx".
    match_mode
        "exact" compares against the full filename.
        "contains" searches for files whose names contain ``search_base`` and
        end with ``search_ext``.
    match_metadata_fields
        Optional additional substrings that must appear in the filename.
        Mainly retained for legacy/internal flexible discovery.
    deduplicate
        If True, remove duplicate filenames across searched directories.
    ignore_excel_temp_files
        If True, skip temporary Excel lock files beginning with "~$".

    Returns
    -------
    list[Path]
        Matching file paths. May be empty.

    Raises
    ------
    ValueError
        If required arguments for the selected match mode are missing.
    """
    dirs = _coerce_directories(directories)
    metadata_fields = [str(mt) for mt in (match_metadata_fields or []) if mt]
    all_matches: list[Path] = []

    if match_mode not in {"exact", "contains"}:
        raise ValueError("match_mode must be either 'exact' or 'contains'.")

    if match_mode == "exact":
        if filename is None:
            raise ValueError("filename is required when match_mode='exact'.")

        target_name = Path(filename).name

        for directory in dirs:
            try:
                if not directory.exists():
                    logger.warning(
                        f"Directory not found: {get_rel_path(directory)} (skipping)."
                    )
                    continue

                for path in directory.rglob(target_name):
                    if not path.is_file():
                        continue
                    if ignore_excel_temp_files and _is_excel_temp_file(path):
                        continue
                    if path.name != target_name:
                        continue
                    if all(mt in path.name for mt in metadata_fields):
                        all_matches.append(path)

            except Exception as exc:
                logger.error(f"Error searching in {get_rel_path(directory)}: {exc}")

        search_label = target_name

    else:
        search_ext = _normalize_ext(search_ext)

        if not search_base and not metadata_fields:
            raise ValueError(
                "search_base or match_metadata_fields is required when "
                "match_mode='contains'."
            )

        pattern = f"*{search_base}*{search_ext}"

        for directory in dirs:
            try:
                if not directory.exists():
                    logger.warning(
                        f"Directory not found: {get_rel_path(directory)} (skipping)."
                    )
                    continue

                for path in directory.rglob(pattern):
                    if not path.is_file():
                        continue
                    if ignore_excel_temp_files and _is_excel_temp_file(path):
                        continue
                    if all(mt in path.name for mt in metadata_fields):
                        all_matches.append(path)

            except Exception as exc:
                logger.error(f"Error searching in {get_rel_path(directory)}: {exc}")

        search_label = f"{search_base}*{search_ext}"

    matches = _deduplicate_by_filename(all_matches) if deduplicate else all_matches

    if not matches:
        logger.warning(
            f"No files matched '{search_label}' with metadata labels {metadata_fields}."
        )
        return []

    if len(matches) == 1:
        logger.info(f"Matched file '{search_label}': {get_rel_path(matches[0])}")
    else:
        logger.info(f"Multiple ({len(matches)}) files matched '{search_label}'.")
        for path in matches:
            logger.debug(f"  - {get_rel_path(path)}")

    return matches


def require_one_file(
    matches: list[Path],
    *,
    label: str = "file",
    configured_name: str | Path | None = None,
) -> Path:
    """
    Require exactly one matched file.

    Use this after ``find_matching_files`` in analysis commands where ambiguity
    would make the result unsafe.
    """
    configured_text = (
        f" matching configured name '{Path(configured_name).name}'"
        if configured_name is not None
        else ""
    )

    if not matches:
        raise FileNotFoundError(f"No {label}{configured_text} was found.")

    if len(matches) > 1:
        match_list = "\n".join(f"  - {get_rel_path(path)}" for path in matches)
        raise MultipleFilesFoundError(
            f"Multiple {label} files{configured_text} were found.\n"
            "Please remove duplicates, "
            "rename files, or configure a more specific filename.\n"
            f"Matches:\n{match_list}"
        )

    return matches[0]


def find_one_matching_file(
    *,
    directories: Path | str | Iterable[Path | str] | None = None,
    filename: str | Path | None = None,
    search_base: str = "",
    search_ext: str = ".xlsx",
    match_mode: MatchMode = "exact",
    match_metadata_fields: Iterable[str] | None = None,
    deduplicate: bool = True,
    ignore_excel_temp_files: bool = True,
    label: str = "file",
) -> Path:
    """
    Convenience wrapper for workflows requiring exactly one file.

    Defaults to exact filename matching.
    """
    matches = find_matching_files(
        directories=directories,
        filename=filename,
        search_base=search_base,
        search_ext=search_ext,
        match_mode=match_mode,
        match_metadata_fields=match_metadata_fields,
        deduplicate=deduplicate,
        ignore_excel_temp_files=ignore_excel_temp_files,
    )

    configured_name = filename if match_mode == "exact" else search_base

    return require_one_file(
        matches,
        label=label,
        configured_name=configured_name,
    )
