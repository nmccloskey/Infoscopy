from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from psair.examples.assets import asset_path


def write_rendered_doc(package: str, *parts: str, text: str) -> Path:
    """Write a UTF-8 markdown document into a package resource directory."""
    path = Path(asset_path(package, *parts))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def fenced(text: str, language: str = "") -> str:
    """Return text wrapped in a Markdown fenced code block."""
    return f"```{language}\n{text.rstrip()}\n```"


def preview_json(data: dict[str, Any]) -> str:
    """Return pretty JSON for documentation previews."""
    return json.dumps(data, indent=2)


def preview_yaml(
    data: dict[str, Any],
    keys: Iterable[str] | None = None,
    *,
    allow_unicode: bool = False,
) -> str:
    """Return a YAML preview, optionally limited to selected keys."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to render YAML previews.") from exc

    subset = data if keys is None else {key: data[key] for key in keys if key in data}
    return yaml.safe_dump(
        subset,
        sort_keys=False,
        allow_unicode=allow_unicode,
    ).rstrip()


def markdown_table(table: Any, *, max_rows: int = 8) -> str:
    """Render a small DataFrame-like object as a Markdown table."""
    preview = table.head(max_rows).fillna("")
    headers = [str(col) for col in preview.columns]
    rows = [[str(value) for value in row] for row in preview.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def workbook_sheet_tables(path: str | Path, sheet_names: list[str]) -> str:
    """Render selected workbook sheets as Markdown table sections."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to render workbook previews.") from exc

    workbook_path = Path(path)
    sections = []
    for sheet_name in sheet_names:
        df = pd.read_excel(workbook_path, sheet_name=sheet_name)
        sections.append(f"### Sheet: {sheet_name}\n\n{markdown_table(df)}")
    return "\n\n".join(sections)


def all_workbook_sheet_tables(path: str | Path) -> str:
    """Render all workbook sheets as Markdown table sections."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to render workbook previews.") from exc

    workbook_path = Path(path)
    with pd.ExcelFile(workbook_path, engine="openpyxl") as xls:
        return workbook_sheet_tables(workbook_path, xls.sheet_names)
