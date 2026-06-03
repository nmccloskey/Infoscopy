from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
import yaml

from psair.examples import (
    ExampleAssets,
    all_workbook_sheet_tables,
    copy_tree_contents,
    fenced,
    iter_rendered_markdown_files,
    long_path,
    markdown_table,
    preview_json,
    preview_yaml,
    read_yaml_asset,
    read_yaml_specs,
    replace_tree,
    scratch_dir,
    write_json,
    write_rendered_doc,
    write_text,
    write_yaml,
    workbook_sheet_tables,
)


def _make_resource_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_name = "example_resource_pkg"
    package_dir = tmp_path / package_name
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")

    spec_dir = package_dir / "assets" / "spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "dataset.yaml").write_text(
        "name: Synthetic Example\nrows: 3\n",
        encoding="utf-8",
        newline="\n",
    )
    (spec_dir / "nested.yaml").write_text(
        "enabled: true\n",
        encoding="utf-8",
        newline="\n",
    )
    (spec_dir / "not_mapping.yaml").write_text(
        "- not\n- a\n- mapping\n",
        encoding="utf-8",
        newline="\n",
    )

    docs_dir = package_dir / "assets" / "rendered_docs" / "example_io"
    docs_dir.mkdir(parents=True)
    (docs_dir / "02_second.md").write_text("# Second\n", encoding="utf-8")
    (docs_dir / "01_first.md").write_text("# First\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    importlib.import_module(package_name)
    return package_name


def test_yaml_asset_helpers_read_mappings_and_reject_other_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _make_resource_package(tmp_path, monkeypatch)

    assert read_yaml_asset(package, "assets", "spec", "dataset.yaml") == {
        "name": "Synthetic Example",
        "rows": 3,
    }
    assert read_yaml_specs(
        package,
        {
            "dataset": "dataset.yaml",
            "nested": ("nested.yaml",),
        },
        root=("assets", "spec"),
    ) == {
        "dataset": {"name": "Synthetic Example", "rows": 3},
        "nested": {"enabled": True},
    }

    with pytest.raises(TypeError, match="must contain a mapping"):
        read_yaml_asset(package, "assets", "spec", "not_mapping.yaml")


def test_example_assets_wraps_specs_docs_and_rendered_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _make_resource_package(tmp_path, monkeypatch)
    assets = ExampleAssets(package)

    assert assets.read_yaml_mapping("assets", "spec", "nested.yaml") == {
        "enabled": True
    }
    assert assets.read_specs({"dataset": "dataset.yaml"})["dataset"]["rows"] == 3
    assert assets.rendered_docs_path().name == "example_io"
    assert [path.name for path in assets.iter_rendered_markdown_files()] == [
        "01_first.md",
        "02_second.md",
    ]

    written = assets.write_rendered_doc("03_third.md", text="# Third\n")

    assert written.name == "03_third.md"
    assert written.read_text(encoding="utf-8") == "# Third\n"
    assert [path.name for path in iter_rendered_markdown_files(
        package,
        "assets",
        "rendered_docs",
        "example_io",
    )] == [
        "01_first.md",
        "02_second.md",
        "03_third.md",
    ]


def test_safe_file_writes_refuse_overwrites_until_forced(tmp_path: Path) -> None:
    text_path = tmp_path / "out" / "note.txt"
    write_text(text_path, "first", force=False)

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        write_text(text_path, "second", force=False)

    write_text(text_path, "second", force=True)
    assert text_path.read_text(encoding="utf-8") == "second"

    yaml_path = tmp_path / "config.yaml"
    json_path = tmp_path / "data.json"
    write_yaml(yaml_path, {"name": "Example", "count": 2}, force=False)
    write_json(json_path, {"ok": True}, force=False)

    assert yaml.safe_load(yaml_path.read_text(encoding="utf-8")) == {
        "name": "Example",
        "count": 2,
    }
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"ok": True}


def test_scratch_dir_and_tree_copy_helpers(tmp_path: Path) -> None:
    with scratch_dir(tmp_path, prefix="scratch_") as scratch:
        assert scratch.exists()
        assert scratch.name.startswith("scratch_")
        scratch.joinpath("created.txt").write_text("inside", encoding="utf-8")
    assert not scratch.exists()

    source = tmp_path / "source"
    source.joinpath("nested").mkdir(parents=True)
    source.joinpath("nested", "file.txt").write_text("copied", encoding="utf-8")

    target = tmp_path / "target"
    copy_tree_contents(source, target)
    assert target.joinpath("nested", "file.txt").read_text(encoding="utf-8") == "copied"

    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        replace_tree(source, existing, force=False)

    replace_tree(source, existing, force=True)
    assert existing.joinpath("nested", "file.txt").read_text(encoding="utf-8") == "copied"


def test_long_path_resolves_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    resolved = long_path("relative.txt")

    assert resolved.is_absolute()
    if resolved.drive:
        assert str(resolved).startswith("\\\\?\\") or resolved == tmp_path / "relative.txt"


def test_markdown_preview_helpers() -> None:
    assert fenced("hello\n", "text") == "```text\nhello\n```"
    assert preview_json({"a": 1}) == '{\n  "a": 1\n}'
    assert preview_yaml({"a": 1, "b": 2}, ["b"]) == "b: 2"


def test_markdown_table_and_workbook_previews(tmp_path: Path) -> None:
    pd = pytest.importorskip("pandas")

    df = pd.DataFrame(
        [
            {"sample_id": "S001", "score": 1},
            {"sample_id": "S002", "score": None},
        ]
    )

    assert markdown_table(df) == (
        "| sample_id | score |\n"
        "| --- | --- |\n"
        "| S001 | 1.0 |\n"
        "| S002 |  |"
    )

    workbook = tmp_path / "preview.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="scores", index=False)
        pd.DataFrame([{"note": "ok"}]).to_excel(writer, sheet_name="notes", index=False)

    selected = workbook_sheet_tables(workbook, ["scores"])
    all_tables = all_workbook_sheet_tables(workbook)

    assert "### Sheet: scores" in selected
    assert "| sample_id | score |" in selected
    assert "### Sheet: notes" in all_tables
    assert "| note |" in all_tables


def test_write_rendered_doc_uses_package_resource_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _make_resource_package(tmp_path, monkeypatch)

    path = write_rendered_doc(
        package,
        "assets",
        "rendered_docs",
        "example_io",
        "nested",
        "doc.md",
        text="# Nested\n",
    )

    assert path.read_text(encoding="utf-8") == "# Nested\n"
