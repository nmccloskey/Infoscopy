from __future__ import annotations

from pathlib import Path

import pytest

from psair.examples import ManualSource
from psair.manual.index import ManualFile
from psair.webapp import manual_export as export


def manual_file(rel_path: str, title: str, text: str) -> ManualFile:
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


def command_front_matter(
    *,
    object_id: str = "transcripts.tabularize",
    canonical_command: str = "transcripts tabularize",
    module_id: str = "transcripts",
    title: str = "Transcript Tabularization Example",
) -> str:
    return f"""---
object_type: command
object_types:
  - command
object_id: {object_id}
command_id: {object_id}
canonical_command: {canonical_command}
module_id: {module_id}
title: {title}
view: example_io
view_label: Example I/O
view_order: 50
source_manual: generated_example_io
generated: true
---

"""


def test_detect_manual_export_backends_reports_runtime_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(export.shutil, "which", lambda name: "pandoc" if name == "pandoc" else None)
    monkeypatch.setattr(export, "_weasyprint_pdf_available", lambda: True)
    monkeypatch.setattr(export, "_module_available", lambda name: name == "docx")

    assert export.detect_manual_export_backends() == {
        "pandoc_pdf": True,
        "weasyprint_pdf": True,
        "docx": True,
    }
    assert export.detect_manual_export_backends(check_pdf=False) == {
        "pandoc_pdf": False,
        "weasyprint_pdf": False,
        "docx": True,
    }


def test_get_best_pdf_backend_prefers_pandoc_then_weasyprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        export,
        "detect_manual_export_backends",
        lambda: {"pandoc_pdf": True, "weasyprint_pdf": True, "docx": False},
    )
    assert export.get_best_pdf_backend() == "pandoc"

    monkeypatch.setattr(
        export,
        "detect_manual_export_backends",
        lambda: {"pandoc_pdf": False, "weasyprint_pdf": True, "docx": False},
    )
    assert export.get_best_pdf_backend() == "weasyprint"

    monkeypatch.setattr(
        export,
        "detect_manual_export_backends",
        lambda: {"pandoc_pdf": False, "weasyprint_pdf": False, "docx": False},
    )
    assert export.get_best_pdf_backend() is None


def test_build_manual_markdown_from_index_orders_strips_and_records_metadata() -> None:
    flat = {
        "10_late.md": manual_file("10_late.md", "Late", "# 10 Late\nBeta"),
        "01_intro.md": manual_file("01_intro.md", "Intro", "# 01 Intro\nAlpha"),
        "section/02_topic.md": manual_file(
            "section/02_topic.md",
            "Topic",
            "# 02 Topic\nGamma",
        ),
    }

    markdown_text, metadata = export.build_manual_markdown_from_index(flat)

    assert markdown_text.startswith("# Intro\nAlpha")
    assert "\\newpage" in markdown_text
    assert "# 01 Intro" not in markdown_text
    assert "# Topic" in markdown_text
    assert [item["rel_path"] for item in metadata] == [
        "01_intro.md",
        "10_late.md",
        "section/02_topic.md",
    ]
    assert metadata[0] == {
        "rel_path": "01_intro.md",
        "title": "Intro",
        "filename": "01_intro.md",
    }


def test_build_manual_markdown_from_index_can_leave_headings_and_pagebreaks_off() -> None:
    flat = {
        "01_intro.md": manual_file("01_intro.md", "Intro", "# 01 Intro\nAlpha"),
        "02_topic.md": manual_file("02_topic.md", "Topic", "# 02 Topic\nBeta"),
    }

    markdown_text, _metadata = export.build_manual_markdown_from_index(
        flat,
        strip_heading_numbers=False,
        pagebreaks=False,
    )

    assert markdown_text == "# 01 Intro\nAlpha\n\n# 02 Topic\nBeta\n"


def test_build_composed_manual_markdown_exports_virtual_example_order(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    command_dir = (
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
    )
    write(command_dir / "01_quickstart.md", "# Quickstart\nRun it.\n")
    write(command_dir / "02_usage_guide.md", "# Usage Guide\nUse it.\n")
    write(command_dir / "04_implementation_notes.md", "# Implementation Notes\nInternals.\n")
    write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    markdown_text, metadata = export.build_composed_manual_markdown(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=True,
        pagebreaks=False,
    )

    assert "---" not in markdown_text
    assert markdown_text.index("# Quickstart") < markdown_text.index("# Usage Guide")
    assert markdown_text.index("# Usage Guide") < markdown_text.index("# Implementation Notes")
    assert markdown_text.index("# Implementation Notes") < markdown_text.index(
        "# Transcript Tabularization Example"
    )
    assert [item["rel_path"] for item in metadata] == [
        "04_modules/01_transcripts/05_commands/01_tabularize/01_quickstart.md",
        "04_modules/01_transcripts/05_commands/01_tabularize/02_usage_guide.md",
        "04_modules/01_transcripts/05_commands/01_tabularize/04_implementation_notes.md",
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md",
    ]
    assert metadata[-1]["title"] == "Example I/O"


def test_build_composed_manual_markdown_applies_path_aliases(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    write(
        authored
        / "04_modules"
        / "03_complete_utterances"
        / "05_commands"
        / "01_files"
        / "01_quickstart.md",
        "# Quickstart\nRun it.\n",
    )
    write(
        generated / "cus" / "files.md",
        command_front_matter(
            object_id="cus.files",
            canonical_command="cus files",
            module_id="cus",
            title="CU Files Example",
        )
        + "# CU Files Example\nGenerated preview.\n",
    )

    markdown_text, metadata = export.build_composed_manual_markdown(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=True,
        path_module_aliases={"complete_utterances": "cus"},
        unmatched_policy="generated_root",
        pagebreaks=False,
    )

    assert "# CU Files Example" in markdown_text
    assert [item["rel_path"] for item in metadata] == [
        "04_modules/03_complete_utterances/05_commands/01_files/01_quickstart.md",
        "04_modules/03_complete_utterances/05_commands/01_files/05_example_io.md",
    ]


def test_pandoc_export_args_include_title_only_when_present() -> None:
    assert export._pandoc_export_args(title="Manual", margin="1in", toc=True, toc_depth=2) == [
        "--toc",
        "--toc-depth",
        "2",
        "-V",
        "geometry:margin=1in",
        "--metadata",
        "title=Manual",
    ]
    assert export._pandoc_export_args(title="", margin=None, toc=False, toc_depth=None) == []


def test_export_manual_pdf_pandoc_requires_pandoc(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(export.shutil, "which", lambda name: None)

    with pytest.raises(export.ManualExportError, match="Pandoc is not available"):
        export.export_manual_pdf_pandoc("# Manual", title="Manual")


def test_export_manual_pdf_falls_back_to_weasyprint_after_pandoc_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(export.shutil, "which", lambda name: "pandoc")
    monkeypatch.setattr(export, "_module_available", lambda name: name in {"markdown", "weasyprint"})

    def fail_pandoc(*args: object, **kwargs: object) -> bytes:
        raise export.ManualExportError("pandoc broke")

    monkeypatch.setattr(export, "export_manual_pdf_pandoc", fail_pandoc)
    monkeypatch.setattr(export, "export_manual_pdf_weasyprint", lambda *args, **kwargs: b"%PDF")

    assert export.export_manual_pdf("# Manual", title="Manual") == (b"%PDF", "weasyprint")


def test_export_manual_pdf_reports_when_no_backend_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(export.shutil, "which", lambda name: None)
    monkeypatch.setattr(export, "_module_available", lambda name: False)

    with pytest.raises(export.ManualExportError, match="No PDF backend is available"):
        export.export_manual_pdf("# Manual", title="Manual")


def test_markdown_html_helpers_escape_title_and_convert_pagebreaks() -> None:
    html_ready = export._markdown_for_html("A\n\n\\newpage\n\nB")
    wrapped = export._wrap_printable_html("<h1>Body</h1>", title="A < B")

    assert '<div class="page-break"></div>' in html_ready
    assert "<title>A &lt; B</title>" in wrapped
    assert "<h1>Body</h1>" in wrapped


def test_clean_inline_markdown_removes_common_markup() -> None:
    cleaned = export._clean_inline_markdown(
        "**Bold** `code` [link](https://example.test) ![Alt](img.png)"
    )

    assert cleaned == "Bold code link (https://example.test) Alt"
