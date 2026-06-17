from __future__ import annotations

from pathlib import Path

import pytest

from psair.examples import (
    ManualCompositionError,
    ManualSource,
    build_composed_manual,
    build_composed_manual_index,
    split_front_matter,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def command_front_matter(
    *,
    object_id: str = "transcripts.tabularize",
    view: str = "example_io",
    title: str = "Transcript Tabularization Example",
) -> str:
    return f"""---
object_type: command
object_types:
  - command
object_id: {object_id}
command_id: {object_id}
canonical_command: transcripts tabularize
module_id: transcripts
title: {title}
view: {view}
view_label: Example I/O
view_order: 50
slot: examples
source_manual: generated_example_io
generated: true
---

"""


def test_split_front_matter_parses_yaml_and_returns_body_only() -> None:
    metadata, body = split_front_matter(
        command_front_matter() + "# Transcript Tabularization Example\nBody\n"
    )

    assert metadata["object_type"] == "command"
    assert metadata["object_id"] == "transcripts.tabularize"
    assert metadata["view"] == "example_io"
    assert body == "# Transcript Tabularization Example\nBody\n"


def test_composes_generated_example_io_as_virtual_command_sibling(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    quickstart = write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "01_quickstart.md",
        "# `transcripts tabularize` Quickstart\nRun it.\n",
    )
    write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "04_implementation_notes.md",
        "# `transcripts tabularize` Implementation Notes\nInternals.\n",
    )
    generated_doc = write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(
                generated,
                name="example_io",
                source_manual="generated_example_io",
                role="generated",
            ),
        ],
        infer_from_paths=True,
    )

    expected_rel = (
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md"
    )
    assert expected_rel in composed.flat
    assert composed.flat[expected_rel].abs_path == generated_doc.resolve()
    assert composed.flat[expected_rel].title == "Example I/O"
    assert composed.flat[expected_rel].text.startswith(
        "# Transcript Tabularization Example"
    )
    assert not composed.flat[expected_rel].text.startswith("---")
    assert composed.flat[
        "04_modules/01_transcripts/05_commands/01_tabularize/01_quickstart.md"
    ].abs_path == quickstart.resolve()
    assert not any("No authored anchor" in item for item in composed.diagnostics)


def test_build_composed_manual_index_returns_existing_tree_and_flat_shapes(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    write(authored / "01_intro.md", "# Intro\nBody.\n")

    tree, flat = build_composed_manual_index([ManualSource(str(authored))])

    assert "01_intro.md" in tree
    assert flat["01_intro.md"].title == "Intro"
    assert flat["01_intro.md"].text == "# Intro\nBody.\n"


def test_path_inference_is_opt_in(tmp_path: Path) -> None:
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
    write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=False,
    )

    assert (
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md"
        not in composed.flat
    )
    assert "transcripts/tabularize.md" in composed.flat
    assert any("No authored anchor" in item for item in composed.diagnostics)


def test_generated_only_views_can_be_grouped_under_generated_root(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "example_io"
    generated_doc = write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [ManualSource(generated, name="example_io", role="generated")],
        unmatched_policy="generated_root",
    )

    rel = "generated/example_io/transcripts/tabularize.md"
    assert rel in composed.flat
    assert composed.flat[rel].abs_path == generated_doc.resolve()


def test_duplicate_object_view_pairs_raise_deterministic_error(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "example_io"
    write(
        generated / "one.md",
        command_front_matter(object_id="demo.run")
        + "# First Example\nGenerated preview.\n",
    )
    write(
        generated / "nested" / "two.md",
        command_front_matter(object_id="demo.run")
        + "# Second Example\nGenerated preview.\n",
    )

    with pytest.raises(ManualCompositionError, match="Duplicate manual view"):
        build_composed_manual(
            [ManualSource(generated, name="example_io", role="generated")]
        )
