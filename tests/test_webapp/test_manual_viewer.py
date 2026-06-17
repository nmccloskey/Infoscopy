from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("streamlit")

from psair.examples import ManualSource
from psair.manual.index import ManualFile
from psair.webapp import manual_viewer as viewer


def manual_file(rel_path: str, title: str, text: str = "# Title\nBody") -> ManualFile:
    return ManualFile(
        rel_path=Path(rel_path),
        abs_path=Path("manual") / rel_path,
        title=title,
        text=text,
    )


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def command_front_matter() -> str:
    return """---
object_type: command
object_types:
  - command
object_id: transcripts.tabularize
command_id: transcripts.tabularize
canonical_command: transcripts tabularize
module_id: transcripts
title: Transcript Tabularization Example
view: example_io
view_label: Example I/O
view_order: 50
source_manual: generated_example_io
generated: true
---

"""


def test_validate_outline_mode_accepts_known_modes_and_rejects_unknown() -> None:
    assert viewer._validate_outline_mode("never") == "never"
    assert viewer._validate_outline_mode("if_missing") == "if_missing"
    assert viewer._validate_outline_mode("always") == "always"

    with pytest.raises(ValueError, match="ensure_outline must be one of"):
        viewer._validate_outline_mode("sometimes")


def test_format_section_label_uses_numeric_prefix_when_present() -> None:
    mf = manual_file("03_nlp_module/03_02_nlp_model.md", "NLP Model")

    assert viewer._format_section_label(mf, "fallback.md") == "3.2: NLP Model"
    assert viewer._format_section_label(None, "readme.md") == "readme.md"
    assert viewer._format_section_label(manual_file("intro.md", "Overview"), "intro.md") == "Overview"


def test_manual_ui_namespace_and_state_keys_are_stable() -> None:
    assert viewer._manual_ui_namespace("docs/PSAIR Manual") == "docs_psair_manual"
    assert viewer._manual_ui_namespace("ignored", ui_key="Main Viewer!") == "main_viewer"
    assert viewer._manual_ui_namespace("///") == "manual"

    assert viewer._manual_state_keys("docs") == {
        "selected": "docs_selected",
        "expand_all": "docs_expand_all",
        "search": "docs_search",
    }


def test_normalize_manual_source_specs_handles_supported_inputs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    generated = tmp_path / "pkg" / "example_io"

    specs = viewer._normalize_manual_source_specs(
        repo_root=repo_root,
        manual_sources=[
            "docs/manual",
            {
                "root": generated,
                "name": "example_io",
                "source_manual": "generated_example_io",
                "role": "generated",
            },
            ManualSource("extra/manual", name="extra"),
        ],
    )

    assert specs == (
        (
            str((repo_root / "docs/manual").resolve()),
            "manual",
            "authored",
            "authored",
        ),
        (
            str(generated.resolve()),
            "example_io",
            "generated_example_io",
            "generated",
        ),
        (
            str((repo_root / "extra/manual").resolve()),
            "extra",
            "authored",
            "authored",
        ),
    )


def test_init_manual_state_preserves_existing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = SimpleNamespace(session_state={"manual_selected": "01_intro.md"})
    monkeypatch.setattr(viewer, "st", fake_st)

    viewer._init_manual_state(
        {
            "selected": "manual_selected",
            "expand_all": "manual_expand_all",
            "search": "manual_search",
        }
    )

    assert fake_st.session_state == {
        "manual_selected": "01_intro.md",
        "manual_expand_all": False,
        "manual_search": "",
    }


def test_prepare_manual_root_warns_for_missing_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(viewer, "st", SimpleNamespace(warning=warnings.append))

    result = viewer._prepare_manual_root(
        repo_root=tmp_path,
        manual_rel_dir="missing",
        ensure_outline="never",
        outline_title="Manual",
        outline_version="1.0",
        outline_max_depth=None,
    )

    assert result is None
    assert warnings == [f"Manual directory not found: {(tmp_path / 'missing').resolve()}"]


def test_prepare_manual_root_can_ensure_outline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manual = tmp_path / "manual"
    manual.mkdir()
    calls: list[dict[str, object]] = []

    def fake_ensure_manual_outline(*args: object, **kwargs: object) -> None:
        calls.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(viewer, "ensure_manual_outline", fake_ensure_manual_outline)

    result = viewer._prepare_manual_root(
        repo_root=tmp_path,
        manual_rel_dir="manual",
        ensure_outline="if_missing",
        outline_title="Manual",
        outline_version="1.0",
        outline_max_depth=2,
    )

    assert result == manual.resolve()
    assert calls == [
        {
            "args": (manual.resolve(),),
            "kwargs": {
                "manual_title": "Manual",
                "manual_version": "1.0",
                "max_depth": 2,
                "if_missing_only": True,
            },
        }
    ]


def test_build_composed_manual_index_from_specs_adds_virtual_example_io(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "01_quickstart.md",
        "# `transcripts tabularize` Quickstart\nRun it.\n",
    )
    generated_doc = write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )
    source_specs = (
        (str(authored.resolve()), "authored", "authored", "authored"),
        (
            str(generated.resolve()),
            "example_io",
            "generated_example_io",
            "generated",
        ),
    )

    tree, flat, diagnostics = viewer._build_composed_manual_index_from_specs(
        source_specs,
        infer_from_paths=True,
        unmatched_policy="source_path",
        on_duplicate="error",
    )

    rel = "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md"
    assert rel in flat
    assert flat[rel].abs_path == generated_doc.resolve()
    assert flat[rel].text.startswith("# Transcript Tabularization Example")
    assert "04_modules" in tree
    assert diagnostics == ()


def test_resolve_pdf_yaml_path_prefers_explicit_repo_then_manual_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    manual_root = repo_root / "docs" / "manual"
    manual_root.mkdir(parents=True)
    repo_yaml = repo_root / "manual_pdf.yaml"
    manual_yaml = manual_root / "manual_pdf.yaml"
    repo_yaml.write_text("title: Repo\n", encoding="utf-8")
    manual_yaml.write_text("title: Manual\n", encoding="utf-8")

    assert viewer._resolve_pdf_yaml_path(repo_root, manual_root, "manual_pdf.yaml") == repo_yaml.resolve()
    assert viewer._resolve_pdf_yaml_path(repo_root, manual_root, None) == manual_yaml.resolve()
    assert viewer._resolve_pdf_yaml_path(repo_root, manual_root, "missing.yaml") is None


def test_manual_export_title_uses_yaml_then_fallback_then_directory(
    tmp_path: Path,
) -> None:
    manual_root = tmp_path / "psair_manual"
    manual_root.mkdir()
    yaml_path = manual_root / "manual_pdf.yaml"
    yaml_path.write_text('title: "YAML Title"\n', encoding="utf-8")

    assert viewer._manual_export_title(manual_root, yaml_path, "Fallback") == "YAML Title"
    assert viewer._manual_export_title(manual_root, None, "Fallback") == "Fallback"
    assert viewer._manual_export_title(manual_root, None, "Instruction Manual") == "Psair Manual"


def test_manual_export_filename_and_backend_cache_key() -> None:
    assert viewer._manual_export_filename(Path("PSAIR Manual!"), ".docx") == "PSAIR_Manual.docx"
    assert viewer._manual_export_filename(Path("!!!"), ".pdf") == "manual.pdf"
    assert viewer._backend_cache_key({"docx": True, "pandoc_pdf": False}) == "docx=1,pandoc_pdf=0"


def test_render_manual_content_handles_empty_missing_and_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []
    fake_st = SimpleNamespace(
        session_state={"selected": None},
        info=lambda msg: calls.append(("info", msg)),
        warning=lambda msg: calls.append(("warning", msg)),
        caption=lambda msg: calls.append(("caption", msg)),
        markdown=lambda msg: calls.append(("markdown", msg)),
    )
    monkeypatch.setattr(viewer, "st", fake_st)

    viewer._render_manual_content(flat={}, state_keys={"selected": "selected"})
    fake_st.session_state["selected"] = "missing.md"
    viewer._render_manual_content(flat={}, state_keys={"selected": "selected"})
    fake_st.session_state["selected"] = "01_intro.md"
    viewer._render_manual_content(
        flat={"01_intro.md": manual_file("01_intro.md", "Intro", "# Intro\nBody")},
        state_keys={"selected": "selected"},
        header_label="Docs",
    )

    assert calls == [
        ("info", "Select from the above menu to view instructions."),
        ("warning", "Selected file not found: missing.md"),
        ("caption", "Docs / 01_intro.md"),
        ("markdown", "# Intro\nBody"),
    ]
